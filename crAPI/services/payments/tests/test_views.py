"""
View-level tests for all 8 payment operations.
Middleware is live (uses test settings: test_merch_001 is allowed).
Tests cover: happy path, state machine violations, amount guards.
"""
import json
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
os.environ.setdefault('PAYMENTS_ALLOWED_MERCHANT_IDS', 'test_merch_001,test_merch_002')

from django.test import TestCase, override_settings
from django.core.cache import cache

from payments.models import PaymentTransaction, TransactionOperation, TransactionStatus
from .helpers import valid_headers, unique_request_id, unique_idem_key, auth_body


BASE_SETTINGS = dict(
    PAYMENTS_ALLOWED_MERCHANT_IDS='test_merch_001,test_merch_002',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'view-test'}},
)


@override_settings(**BASE_SETTINGS)
class TestAuthView(TestCase):
    def setUp(self):
        cache.clear()

    def _post(self, body=None, **hkwargs):
        h = valid_headers(**hkwargs)
        b = json.dumps(body or auth_body())
        return self.client.post('/payments/api/payments/auth', b,
                                content_type='application/json', **h)

    def test_auth_returns_200(self):
        r = self._post()
        self.assertEqual(r.status_code, 200)

    def test_auth_response_has_transaction_id(self):
        r = self._post()
        data = r.json()
        self.assertIn('transaction_id', data['transaction'])
        self.assertTrue(data['transaction']['transaction_id'])

    def test_auth_response_has_auth_id(self):
        r = self._post()
        auth_id = r.json()['transaction']['auth_id']
        self.assertTrue(auth_id.startswith('AUTH-'))

    def test_auth_status_is_authorized(self):
        r = self._post()
        self.assertEqual(r.json()['transaction']['status'], 'authorized')

    def test_auth_operation_is_auth(self):
        r = self._post()
        self.assertEqual(r.json()['transaction']['operation'], 'auth')

    def test_auth_response_has_avs_result(self):
        r = self._post()
        self.assertIn('avs_result', r.json()['authorization'])

    def test_auth_response_has_risk_score(self):
        r = self._post()
        self.assertIn('risk', r.json()['authorization'])
        self.assertIn('score', r.json()['authorization']['risk'])

    def test_auth_response_has_network_block(self):
        r = self._post()
        self.assertIn('network', r.json()['authorization'])
        self.assertEqual(r.json()['authorization']['network']['response_code'], '00')

    def test_auth_stores_transaction_in_db(self):
        r = self._post()
        tid = r.json()['transaction']['transaction_id']
        txn = PaymentTransaction.objects.get(transaction_id=tid)
        self.assertEqual(txn.operation, TransactionOperation.AUTH)
        self.assertEqual(txn.status, TransactionStatus.AUTHORIZED)

    def test_auth_amount_reflected_in_response(self):
        r = self._post(body=auth_body(amount=55000))
        self.assertEqual(r.json()['authorization']['authorized_amount']['value'], 55000)

    def test_invalid_json_returns_400(self):
        h = valid_headers()
        r = self.client.post('/payments/api/payments/auth', 'not-json',
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'invalid_json')


@override_settings(**BASE_SETTINGS)
class TestSaleView(TestCase):
    def setUp(self):
        cache.clear()

    def _post(self, body=None):
        h = valid_headers()
        b = json.dumps(body or auth_body(amount=25000))
        return self.client.post('/payments/api/payments/sale', b,
                                content_type='application/json', **h)

    def test_sale_returns_200(self):
        r = self._post()
        self.assertEqual(r.status_code, 200)

    def test_sale_status_is_settled(self):
        r = self._post()
        self.assertEqual(r.json()['transaction']['status'], 'settled')

    def test_sale_has_settlement_block(self):
        r = self._post()
        self.assertIn('settlement', r.json())
        self.assertIn('batch_id', r.json()['settlement'])

    def test_sale_has_interchange_fee(self):
        r = self._post()
        self.assertIn('interchange_fee', r.json()['settlement'])


@override_settings(**BASE_SETTINGS)
class TestReversalView(TestCase):
    def setUp(self):
        cache.clear()

    def _auth(self, amount=10000):
        h = valid_headers()
        b = json.dumps(auth_body(amount=amount))
        r = self.client.post('/payments/api/payments/auth', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)
        return r.json()['transaction']['auth_id'], r.json()['transaction']['transaction_id']

    def _reversal(self, auth_id):
        h = valid_headers()
        b = json.dumps({'reversal': {'reason': {'code': 'CUSTOMER_REQUEST'}}})
        return self.client.post(f'/payments/api/payments/reversal/{auth_id}', b,
                                content_type='application/json', **h)

    def test_reversal_returns_200(self):
        aid, _ = self._auth()
        r = self._reversal(aid)
        self.assertEqual(r.status_code, 200)

    def test_reversal_status_is_reversed(self):
        aid, _ = self._auth()
        r = self._reversal(aid)
        self.assertEqual(r.json()['transaction']['status'], 'reversed')

    def test_reversal_links_original_transaction(self):
        aid, orig_id = self._auth()
        r = self._reversal(aid)
        self.assertEqual(r.json()['transaction']['original_transaction_id'], orig_id)

    def test_reversal_on_nonexistent_auth_returns_404(self):
        r = self._reversal('AUTH-9999')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()['error'], 'transaction_not_found')

    def test_reversal_hold_released(self):
        aid, _ = self._auth()
        r = self._reversal(aid)
        self.assertTrue(r.json()['reversal']['hold_released'])


@override_settings(**BASE_SETTINGS)
class TestCaptureView(TestCase):
    def setUp(self):
        cache.clear()

    def _auth(self, amount=20000):
        h = valid_headers()
        b = json.dumps(auth_body(amount=amount))
        r = self.client.post('/payments/api/payments/auth', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)
        return r.json()['transaction']['transaction_id']

    def _capture(self, txn_id, capture_amount=None):
        h = valid_headers()
        body = {'original_transaction_id': txn_id}
        if capture_amount is not None:
            body['capture'] = {'amount': {'value': capture_amount, 'currency': 'USD'}}
        r = self.client.post('/payments/api/payments/capture', json.dumps(body),
                             content_type='application/json', **h)
        return r

    def test_capture_full_amount_returns_200(self):
        tid = self._auth(amount=20000)
        r = self._capture(tid)
        self.assertEqual(r.status_code, 200)

    def test_capture_status_is_captured(self):
        tid = self._auth()
        r = self._capture(tid)
        self.assertEqual(r.json()['transaction']['status'], 'captured')

    def test_partial_capture_succeeds(self):
        tid = self._auth(amount=20000)
        r = self._capture(tid, capture_amount=10000)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['capture']['captured_amount']['value'], 10000)
        self.assertEqual(r.json()['capture']['delta']['direction'], 'under_capture')

    def test_capture_exceeds_auth_returns_422(self):
        tid = self._auth(amount=10000)
        r = self._capture(tid, capture_amount=15000)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()['error'], 'capture_exceeds_authorized')

    def test_capture_with_invalid_uuid_returns_400(self):
        h = valid_headers()
        b = json.dumps({'original_transaction_id': 'not-a-uuid'})
        r = self.client.post('/payments/api/payments/capture', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)

    def test_capture_nonexistent_txn_returns_404(self):
        import uuid
        h = valid_headers()
        b = json.dumps({'original_transaction_id': str(uuid.uuid4())})
        r = self.client.post('/payments/api/payments/capture', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 404)

    def test_capture_has_settlement_schedule(self):
        tid = self._auth()
        r = self._capture(tid)
        self.assertIn('settlement_schedule', r.json())
        self.assertIn('batch_id', r.json()['settlement_schedule'])


@override_settings(**BASE_SETTINGS)
class TestVoidCaptureView(TestCase):
    def setUp(self):
        cache.clear()

    def _auth_then_capture(self, amount=15000):
        h = valid_headers()
        b = json.dumps(auth_body(amount=amount))
        auth_r = self.client.post('/payments/api/payments/auth', b,
                                  content_type='application/json', **h)
        auth_tid = auth_r.json()['transaction']['transaction_id']

        h2 = valid_headers()
        cap_b = json.dumps({'original_transaction_id': auth_tid})
        cap_r = self.client.post('/payments/api/payments/capture', cap_b,
                                 content_type='application/json', **h2)
        self.assertEqual(cap_r.status_code, 200)
        return cap_r.json()['transaction']['transaction_id']

    def test_void_capture_returns_200(self):
        cap_tid = self._auth_then_capture()
        h = valid_headers()
        b = json.dumps({'original_transaction_id': cap_tid})
        r = self.client.post('/payments/api/payments/void-capture', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)

    def test_void_capture_status(self):
        cap_tid = self._auth_then_capture()
        h = valid_headers()
        b = json.dumps({'original_transaction_id': cap_tid})
        r = self.client.post('/payments/api/payments/void-capture', b,
                             content_type='application/json', **h)
        self.assertEqual(r.json()['transaction']['status'], 'void_capture_complete')

    def test_void_capture_on_non_capture_returns_422(self):
        # Attempt to void-capture an auth transaction (wrong operation)
        h = valid_headers()
        b = json.dumps(auth_body())
        auth_r = self.client.post('/payments/api/payments/auth', b,
                                  content_type='application/json', **h)
        auth_tid = auth_r.json()['transaction']['transaction_id']

        h2 = valid_headers()
        b2 = json.dumps({'original_transaction_id': auth_tid})
        r = self.client.post('/payments/api/payments/void-capture', b2,
                             content_type='application/json', **h2)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()['error'], 'invalid_state')

    def test_void_capture_re_capturable_flag(self):
        cap_tid = self._auth_then_capture()
        h = valid_headers()
        b = json.dumps({'original_transaction_id': cap_tid})
        r = self.client.post('/payments/api/payments/void-capture', b,
                             content_type='application/json', **h)
        self.assertTrue(r.json()['auth_status']['re_capturable'])


@override_settings(**BASE_SETTINGS)
class TestRefundView(TestCase):
    def setUp(self):
        cache.clear()

    def _auth_then_capture(self, amount=50000):
        h = valid_headers()
        b = json.dumps(auth_body(amount=amount))
        auth_r = self.client.post('/payments/api/payments/auth', b,
                                  content_type='application/json', **h)
        auth_tid = auth_r.json()['transaction']['transaction_id']

        h2 = valid_headers()
        cap_r = self.client.post('/payments/api/payments/capture',
                                 json.dumps({'original_transaction_id': auth_tid}),
                                 content_type='application/json', **h2)
        self.assertEqual(cap_r.status_code, 200)
        return cap_r.json()['transaction']['transaction_id']

    def test_full_refund_returns_200(self):
        cap_tid = self._auth_then_capture(50000)
        h = valid_headers()
        b = json.dumps({
            'original_transaction_id': cap_tid,
            'refund': {'amount': {'value': 50000, 'currency': 'USD'}},
        })
        r = self.client.post('/payments/api/payments/refund', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['transaction']['status'], 'refunded')

    def test_partial_refund_remaining_refundable(self):
        cap_tid = self._auth_then_capture(50000)
        h = valid_headers()
        b = json.dumps({
            'original_transaction_id': cap_tid,
            'refund': {'amount': {'value': 20000, 'currency': 'USD'}},
        })
        r = self.client.post('/payments/api/payments/refund', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['refund']['remaining_refundable']['value'], 30000)

    def test_two_partial_refunds_within_limit(self):
        cap_tid = self._auth_then_capture(50000)

        h1 = valid_headers()
        r1 = self.client.post('/payments/api/payments/refund',
                              json.dumps({'original_transaction_id': cap_tid,
                                          'refund': {'amount': {'value': 20000, 'currency': 'USD'}}}),
                              content_type='application/json', **h1)
        self.assertEqual(r1.status_code, 200)

        h2 = valid_headers()
        r2 = self.client.post('/payments/api/payments/refund',
                              json.dumps({'original_transaction_id': cap_tid,
                                          'refund': {'amount': {'value': 20000, 'currency': 'USD'}}}),
                              content_type='application/json', **h2)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()['refund']['remaining_refundable']['value'], 10000)

    def test_refund_exceeds_captured_returns_422(self):
        cap_tid = self._auth_then_capture(10000)
        h = valid_headers()
        b = json.dumps({
            'original_transaction_id': cap_tid,
            'refund': {'amount': {'value': 20000, 'currency': 'USD'}},
        })
        r = self.client.post('/payments/api/payments/refund', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()['error'], 'refund_exceeds_captured')

    def test_cumulative_refund_exceeds_cap_returns_422(self):
        cap_tid = self._auth_then_capture(10000)

        h1 = valid_headers()
        r1 = self.client.post('/payments/api/payments/refund',
                              json.dumps({'original_transaction_id': cap_tid,
                                          'refund': {'amount': {'value': 8000, 'currency': 'USD'}}}),
                              content_type='application/json', **h1)
        self.assertEqual(r1.status_code, 200)

        # Second refund would bring total to 11000 > 10000
        h2 = valid_headers()
        r2 = self.client.post('/payments/api/payments/refund',
                              json.dumps({'original_transaction_id': cap_tid,
                                          'refund': {'amount': {'value': 3000, 'currency': 'USD'}}}),
                              content_type='application/json', **h2)
        self.assertEqual(r2.status_code, 422)
        self.assertEqual(r2.json()['error'], 'refund_exceeds_captured')


@override_settings(**BASE_SETTINGS)
class TestVoidRefundView(TestCase):
    def setUp(self):
        cache.clear()

    def _setup_to_refund(self, amount=30000):
        """Auth → Capture → Refund; return refund txn_id and capture txn_id."""
        h = valid_headers()
        auth_r = self.client.post('/payments/api/payments/auth',
                                  json.dumps(auth_body(amount=amount)),
                                  content_type='application/json', **h)
        auth_tid = auth_r.json()['transaction']['transaction_id']

        h2 = valid_headers()
        cap_r = self.client.post('/payments/api/payments/capture',
                                 json.dumps({'original_transaction_id': auth_tid}),
                                 content_type='application/json', **h2)
        cap_tid = cap_r.json()['transaction']['transaction_id']

        h3 = valid_headers()
        ref_r = self.client.post('/payments/api/payments/refund',
                                 json.dumps({'original_transaction_id': cap_tid,
                                             'refund': {'amount': {'value': amount, 'currency': 'USD'}}}),
                                 content_type='application/json', **h3)
        self.assertEqual(ref_r.status_code, 200)
        return ref_r.json()['transaction']['transaction_id'], cap_tid

    def test_void_refund_returns_200(self):
        ref_tid, _ = self._setup_to_refund()
        h = valid_headers()
        r = self.client.post('/payments/api/payments/void-refund',
                             json.dumps({'original_transaction_id': ref_tid}),
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)

    def test_void_refund_status(self):
        ref_tid, _ = self._setup_to_refund()
        h = valid_headers()
        r = self.client.post('/payments/api/payments/void-refund',
                             json.dumps({'original_transaction_id': ref_tid}),
                             content_type='application/json', **h)
        self.assertEqual(r.json()['transaction']['status'], 'void_refund_complete')

    def test_void_refund_restores_remaining_refundable(self):
        ref_tid, cap_tid = self._setup_to_refund(amount=30000)
        h = valid_headers()
        r = self.client.post('/payments/api/payments/void-refund',
                             json.dumps({'original_transaction_id': ref_tid}),
                             content_type='application/json', **h)
        # After voiding the only refund, full amount should be refundable again
        self.assertEqual(r.json()['capture_status']['remaining_refundable']['value'], 30000)


@override_settings(**BASE_SETTINGS)
class TestCreditView(TestCase):
    def setUp(self):
        cache.clear()

    def test_credit_returns_200(self):
        h = valid_headers()
        b = json.dumps({
            'credit': {
                'amount': {'value': 5000, 'currency': 'USD'},
                'type': 'loyalty',
                'funding_source': {'account_id': 'ACCT-001'},
            }
        })
        r = self.client.post('/payments/api/payments/credit', b,
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)

    def test_credit_status_is_credited(self):
        h = valid_headers()
        b = json.dumps({'credit': {'amount': {'value': 1000, 'currency': 'USD'}}})
        r = self.client.post('/payments/api/payments/credit', b,
                             content_type='application/json', **h)
        self.assertEqual(r.json()['transaction']['status'], 'credited')

    def test_credit_has_compliance_block(self):
        h = valid_headers()
        b = json.dumps({'credit': {'amount': {'value': 1000, 'currency': 'USD'}}})
        r = self.client.post('/payments/api/payments/credit', b,
                             content_type='application/json', **h)
        self.assertIn('compliance', r.json())
        self.assertTrue(r.json()['compliance']['aml_clear'])


@override_settings(**BASE_SETTINGS)
class TestStateMachineChain(TestCase):
    """End-to-end chain tests: auth → capture → refund → void-refund."""

    def setUp(self):
        cache.clear()

    def test_full_chain_auth_capture_refund_void_refund(self):
        amount = 40000

        # Auth
        h = valid_headers()
        auth_r = self.client.post('/payments/api/payments/auth',
                                  json.dumps(auth_body(amount=amount)),
                                  content_type='application/json', **h)
        self.assertEqual(auth_r.status_code, 200)
        auth_tid = auth_r.json()['transaction']['transaction_id']

        # Capture
        h = valid_headers()
        cap_r = self.client.post('/payments/api/payments/capture',
                                 json.dumps({'original_transaction_id': auth_tid}),
                                 content_type='application/json', **h)
        self.assertEqual(cap_r.status_code, 200)
        cap_tid = cap_r.json()['transaction']['transaction_id']

        # Refund
        h = valid_headers()
        ref_r = self.client.post('/payments/api/payments/refund',
                                 json.dumps({'original_transaction_id': cap_tid,
                                             'refund': {'amount': {'value': amount, 'currency': 'USD'}}}),
                                 content_type='application/json', **h)
        self.assertEqual(ref_r.status_code, 200)
        ref_tid = ref_r.json()['transaction']['transaction_id']

        # Void-refund
        h = valid_headers()
        vr_r = self.client.post('/payments/api/payments/void-refund',
                                json.dumps({'original_transaction_id': ref_tid}),
                                content_type='application/json', **h)
        self.assertEqual(vr_r.status_code, 200)
        self.assertEqual(vr_r.json()['capture_status']['remaining_refundable']['value'], amount)

    def test_auth_then_reversal_then_capture_fails(self):
        """After reversal, capturing the auth must fail with invalid_state."""
        h = valid_headers()
        auth_r = self.client.post('/payments/api/payments/auth',
                                  json.dumps(auth_body(amount=10000)),
                                  content_type='application/json', **h)
        auth_tid = auth_r.json()['transaction']['transaction_id']
        auth_id  = auth_r.json()['transaction']['auth_id']

        # Reverse
        h2 = valid_headers()
        rev_r = self.client.post(f'/payments/api/payments/reversal/{auth_id}',
                                 json.dumps({}), content_type='application/json', **h2)
        self.assertEqual(rev_r.status_code, 200)

        # Now update the auth transaction status to reversed in DB so the next capture fails
        from payments.models import PaymentTransaction, TransactionStatus
        PaymentTransaction.objects.filter(transaction_id=auth_tid).update(
            status=TransactionStatus.REVERSED)

        # Attempt capture on now-reversed auth
        h3 = valid_headers()
        cap_r = self.client.post('/payments/api/payments/capture',
                                 json.dumps({'original_transaction_id': auth_tid}),
                                 content_type='application/json', **h3)
        self.assertEqual(cap_r.status_code, 422)
        self.assertEqual(cap_r.json()['error'], 'invalid_state')
