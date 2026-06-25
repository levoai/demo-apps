"""
Middleware unit tests — covers all guard layers in PaymentsMiddleware:
  1. Required header presence
  2. Merchant allowlist
  3. Timestamp format + replay window
  4. X-RequestID uniqueness (10-min dedup)
  5. Idempotency: cache hit, conflict
"""
import json
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
os.environ.setdefault('PAYMENTS_ALLOWED_MERCHANT_IDS', 'test_merch_001,test_merch_002')

from django.test import TestCase, override_settings
from django.core.cache import cache

from .helpers import valid_headers, unique_request_id, unique_idem_key, now_iso, auth_body


AUTH_URL = '/payments/api/payments/auth'
BODY     = json.dumps(auth_body())


@override_settings(
    PAYMENTS_ALLOWED_MERCHANT_IDS='test_merch_001,test_merch_002',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'mw-test'}},
)
class TestRequiredHeaders(TestCase):
    """Each required header, when absent, must return 400 missing_header."""

    REQUIRED = [
        'HTTP_X_REQUESTID',
        'HTTP_X_LEVO_MERCHANT_ID',
        'HTTP_X_LEVO_TERMINAL_ID',
        'HTTP_X_LEVO_REQUEST_TIMESTAMP',
        'HTTP_X_LEVO_IDEMPOTENCY_KEY',
    ]

    def test_missing_request_id(self):
        h = valid_headers()
        h.pop('HTTP_X_REQUESTID')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'missing_header')
        self.assertIn('X-RequestID', r.json()['header'])

    def test_missing_merchant_id(self):
        h = valid_headers()
        h.pop('HTTP_X_LEVO_MERCHANT_ID')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'missing_header')

    def test_missing_terminal_id(self):
        h = valid_headers()
        h.pop('HTTP_X_LEVO_TERMINAL_ID')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'missing_header')

    def test_missing_timestamp(self):
        h = valid_headers()
        h.pop('HTTP_X_LEVO_REQUEST_TIMESTAMP')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'missing_header')

    def test_missing_idempotency_key(self):
        h = valid_headers()
        h.pop('HTTP_X_LEVO_IDEMPOTENCY_KEY')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'missing_header')


@override_settings(
    PAYMENTS_ALLOWED_MERCHANT_IDS='test_merch_001,test_merch_002',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'mw-test-merch'}},
)
class TestMerchantAllowlist(TestCase):
    def test_unknown_merchant_returns_403(self):
        h = valid_headers(merchant_id='unknown_merchant_xyz')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['error'], 'merchant_not_allowed')
        self.assertEqual(r.json()['merchant_id'], 'unknown_merchant_xyz')

    def test_known_merchant_passes_allowlist(self):
        h = valid_headers(merchant_id='test_merch_001')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        # Should pass merchant check and reach the view (200)
        self.assertEqual(r.status_code, 200)

    def test_second_known_merchant_passes(self):
        h = valid_headers(merchant_id='test_merch_002')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)


@override_settings(
    PAYMENTS_ALLOWED_MERCHANT_IDS='test_merch_001',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'mw-test-ts'}},
)
class TestTimestampValidation(TestCase):
    def test_malformed_timestamp_returns_400(self):
        h = valid_headers()
        h['HTTP_X_LEVO_REQUEST_TIMESTAMP'] = '2026-06-24 10:30:00'  # wrong format
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'invalid_timestamp')

    def test_timestamp_without_z_returns_400(self):
        h = valid_headers()
        h['HTTP_X_LEVO_REQUEST_TIMESTAMP'] = '2026-06-24T10:30:00'  # missing Z
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)

    def test_old_timestamp_returns_400(self):
        h = valid_headers()
        h['HTTP_X_LEVO_REQUEST_TIMESTAMP'] = '2020-01-01T00:00:00.000Z'  # ancient
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'timestamp_out_of_window')

    def test_future_timestamp_over_5min_returns_400(self):
        from datetime import datetime, timezone, timedelta
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
        h = valid_headers()
        h['HTTP_X_LEVO_REQUEST_TIMESTAMP'] = future.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'timestamp_out_of_window')

    def test_valid_current_timestamp_passes(self):
        h = valid_headers()
        r = self.client.post(AUTH_URL, BODY, content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)


@override_settings(
    PAYMENTS_ALLOWED_MERCHANT_IDS='test_merch_001',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'mw-test-rid'}},
)
class TestRequestIDUniqueness(TestCase):
    def setUp(self):
        cache.clear()

    def test_duplicate_request_id_returns_409(self):
        rid = unique_request_id()
        h1 = valid_headers(request_id=rid)
        h2 = valid_headers(request_id=rid, idem_key=unique_idem_key())

        r1 = self.client.post(AUTH_URL, BODY, content_type='application/json', **h1)
        self.assertEqual(r1.status_code, 200)

        r2 = self.client.post(AUTH_URL, BODY, content_type='application/json', **h2)
        self.assertEqual(r2.status_code, 409)
        self.assertEqual(r2.json()['error'], 'duplicate_request_id')

    def test_unique_request_ids_succeed(self):
        h1 = valid_headers(request_id=unique_request_id())
        h2 = valid_headers(request_id=unique_request_id())

        r1 = self.client.post(AUTH_URL, BODY, content_type='application/json', **h1)
        r2 = self.client.post(AUTH_URL, BODY, content_type='application/json', **h2)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)


@override_settings(
    PAYMENTS_ALLOWED_MERCHANT_IDS='test_merch_001',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'mw-test-idem'}},
)
class TestIdempotency(TestCase):
    def setUp(self):
        cache.clear()

    def test_same_key_same_body_returns_cached_response(self):
        idem = unique_idem_key()
        h1 = valid_headers(idem_key=idem)
        h2 = valid_headers(request_id=unique_request_id(), idem_key=idem)

        r1 = self.client.post(AUTH_URL, BODY, content_type='application/json', **h1)
        r2 = self.client.post(AUTH_URL, BODY, content_type='application/json', **h2)

        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2['X-Idempotency-Hit'], 'true')
        # Response bodies should be identical (same transaction_id)
        self.assertEqual(r1.json()['transaction']['transaction_id'],
                         r2.json()['transaction']['transaction_id'])

    def test_same_key_different_body_returns_409(self):
        idem = unique_idem_key()
        body1 = json.dumps(auth_body(amount=10000))
        body2 = json.dumps(auth_body(amount=20000))

        h1 = valid_headers(idem_key=idem)
        h2 = valid_headers(request_id=unique_request_id(), idem_key=idem)

        r1 = self.client.post(AUTH_URL, body1, content_type='application/json', **h1)
        r2 = self.client.post(AUTH_URL, body2, content_type='application/json', **h2)

        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 409)
        self.assertEqual(r2.json()['error'], 'idempotency_conflict')

    def test_health_endpoint_bypasses_middleware(self):
        r = self.client.get('/payments/api/payments/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ok')
