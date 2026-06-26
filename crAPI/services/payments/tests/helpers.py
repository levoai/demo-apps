"""Shared test helpers for crapi-payments test suite."""
import uuid
from datetime import datetime, timezone


def now_iso():
    """Current UTC timestamp in the format the middleware accepts."""
    return datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')


def unique_request_id():
    return f'RID{uuid.uuid4().hex[:20].upper()}'


def unique_idem_key():
    return f'IDEM-{uuid.uuid4().hex}'


def valid_headers(merchant_id='test_merch_001', terminal_id='TERM-001',
                  request_id=None, idem_key=None):
    """Returns a dict of all required payment headers."""
    return {
        'HTTP_X_REQUESTID':              request_id or unique_request_id(),
        'HTTP_X_LEVO_MERCHANT_ID':       merchant_id,
        'HTTP_X_LEVO_TERMINAL_ID':       terminal_id,
        'HTTP_X_LEVO_REQUEST_TIMESTAMP': now_iso(),
        'HTTP_X_LEVO_IDEMPOTENCY_KEY':   idem_key or unique_idem_key(),
        'CONTENT_TYPE':                  'application/json',
    }


def auth_body(amount=10000, currency='USD'):
    return {
        'card': {
            'pan': '4111111111111111',
            'expiry': {'month': 12, 'year': 2027},
            'holder_name': 'Test User',
        },
        'transaction': {
            'amount': {'value': amount, 'currency': currency},
            'order': {
                'order_id': f'ORD-{uuid.uuid4().hex[:8]}',
                'line_items': [
                    {'sku': 'SKU-001', 'description': 'Widget',
                     'quantity': 1, 'unit_price': amount,
                     'merchant_category_code': '5999'},
                ],
            },
        },
    }
