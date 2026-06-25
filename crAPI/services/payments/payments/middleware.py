import os
import re
import json
import hashlib
import time
from datetime import datetime, timezone, timedelta

from django.conf import settings as django_settings
from django.core.cache import cache
from django.http import JsonResponse


def _allowed_merchants():
    """Read merchant allowlist from Django settings at request time so override_settings works."""
    raw = getattr(django_settings, 'PAYMENTS_ALLOWED_MERCHANT_IDS', '')
    return frozenset(m.strip() for m in raw.split(',') if m.strip())

REQUIRED_HEADERS = [
    ('HTTP_X_REQUESTID',              'X-RequestID'),
    ('HTTP_X_LEVO_MERCHANT_ID',       'x-levo-merchant-id'),
    ('HTTP_X_LEVO_TERMINAL_ID',       'x-levo-terminal-id'),
    ('HTTP_X_LEVO_REQUEST_TIMESTAMP', 'x-levo-request-timestamp'),
    ('HTTP_X_LEVO_IDEMPOTENCY_KEY',   'x-levo-idempotency-key'),
]

_TS_RE         = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$')
_REPLAY_WINDOW = timedelta(minutes=5)
_RID_TTL       = 600   # 10 min — X-RequestID uniqueness window
_IDEM_TTL      = 300   # 5 min  — idempotency key TTL
_PAYMENTS_PATH = '/payments/api/payments/'

# Health endpoint bypasses all middleware checks
_HEALTH_PATH = '/payments/api/payments/health'

_REQUIRE_JWT = os.environ.get('PAYMENTS_REQUIRE_JWT', 'false').lower() == 'true'
if _REQUIRE_JWT:
    import jwt as _jwt
    _JWT_SECRET    = os.environ.get('JWT_SECRET', 'crapi')
    _JWT_ALGORITHM = 'HS256'


class PaymentsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(_PAYMENTS_PATH):
            return self.get_response(request)

        if request.path == _HEALTH_PATH:
            return self.get_response(request)

        request._pay_start = time.monotonic()

        # 0. Optional JWT guard (disabled by default — see ADR-003)
        if _REQUIRE_JWT:
            auth = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth.startswith('Bearer '):
                return JsonResponse({'error': 'unauthorized'}, status=401)
            try:
                _jwt.decode(auth[7:], _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
            except _jwt.PyJWTError:
                return JsonResponse({'error': 'unauthorized'}, status=401)

        # 1. Required header presence
        for meta_key, display in REQUIRED_HEADERS:
            if not request.META.get(meta_key):
                return JsonResponse(
                    {'error': 'missing_header', 'header': display}, status=400)

        # 2. Merchant allowlist
        merchant_id = request.META['HTTP_X_LEVO_MERCHANT_ID']
        if merchant_id not in _allowed_merchants():
            return JsonResponse(
                {'error': 'merchant_not_allowed', 'merchant_id': merchant_id},
                status=403)

        # 3. Timestamp: ISO 8601 UTC format + 5-min replay window
        ts_str = request.META['HTTP_X_LEVO_REQUEST_TIMESTAMP']
        if not _TS_RE.match(ts_str):
            return JsonResponse(
                {'error': 'invalid_timestamp',
                 'detail': 'must match ISO 8601 UTC, e.g. 2026-06-24T10:30:00.000Z'},
                status=400)
        try:
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            if abs(datetime.now(tz=timezone.utc) - ts) > _REPLAY_WINDOW:
                return JsonResponse(
                    {'error': 'timestamp_out_of_window',
                     'detail': 'timestamp must be within 5 minutes of server time'},
                    status=400)
        except ValueError:
            return JsonResponse({'error': 'invalid_timestamp'}, status=400)

        # 4. X-RequestID uniqueness — 10-min dedup window
        request_id = request.META['HTTP_X_REQUESTID']
        rid_key = f'pay:rid:{request_id}'
        if cache.get(rid_key):
            return JsonResponse({'error': 'duplicate_request_id'}, status=409)
        cache.set(rid_key, 1, _RID_TTL)

        # 5. Idempotency key — 5-min TTL; same key+body → cached response, different body → 409
        idem_key = request.META['HTTP_X_LEVO_IDEMPOTENCY_KEY']
        _ = request.body   # force Django to read and buffer the body
        body_hash = hashlib.sha256(request.body).hexdigest()
        idem_cache_key = f'pay:idem:{idem_key}'
        cached = cache.get(idem_cache_key)
        if cached:
            if cached['hash'] == body_hash:
                r = JsonResponse(cached['response'], status=cached['status'])
                r['X-Idempotency-Hit'] = 'true'
                return r
            return JsonResponse(
                {'error': 'idempotency_conflict',
                 'detail': 'same idempotency key submitted with a different request body'},
                status=409)

        request._idem_cache_key = idem_cache_key
        request._body_hash = body_hash

        response = self.get_response(request)

        # Cache the response for future idempotent replays
        if response.status_code == 200 and hasattr(request, '_idem_cache_key'):
            try:
                cache.set(request._idem_cache_key, {
                    'hash': request._body_hash,
                    'response': json.loads(response.content),
                    'status': response.status_code,
                }, _IDEM_TTL)
            except (json.JSONDecodeError, Exception):
                pass

        return response
