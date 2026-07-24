"""Shared helpers for the payments views, reused by views.py and lifecycle.py."""
import json
import random
import string
import time
import uuid
from datetime import timedelta

from django.http import JsonResponse

from .models import PaymentTransaction


def _rand_digits(n):
    return ''.join(random.choices(string.digits, k=n))

def _rand_hex(n):
    return ''.join(random.choices('0123456789ABCDEF', k=n))

def _auth_id():
    # 12 digits: auth_id is the /reversal/{auth_id} lookup key and has no unique
    # constraint, so a narrow space collides and reversals hit the wrong transaction.
    return f'AUTH-{_rand_digits(12)}'

def _aprv(pfx):
    return f'{pfx}-{_rand_digits(4)}'

def _network(op_code):
    return {
        'acquirer_id':            'ACQ-SIM-001',
        'network_transaction_id': f'NTX-SIM-{op_code}-{_rand_hex(12)}',
        'response_code':          '00',
        'response_message':       'Approved',
        'processing_host':        'PAY-SIM-GW-1',
        'round_trip_ms':          random.randint(120, 380),
    }

def _meta(request):
    elapsed = int((time.monotonic() - getattr(request, '_pay_start', time.monotonic())) * 1000)
    return {
        'request_id':         request.META.get('HTTP_X_REQUESTID', ''),
        'processing_time_ms': elapsed,
        'api_version':        '2026-06',
        'scenario':           request.META.get('HTTP_X_LEVO_TEST_SCENARIO', ''),
        'gateway_node':       'pay-sim-node-1',
        'correlation_id':     request.META.get('HTTP_X_LEVO_CORRELATION_ID'),
    }

def _isodate(dt):
    return dt.isoformat().replace('+00:00', 'Z') if dt else None

def _settle_date(dt, days=2):
    return (dt + timedelta(days=days)).strftime('%Y-%m-%d')

def _body(request):
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, ValueError) as e:
        return None, JsonResponse({'error': 'invalid_json', 'detail': str(e)}, status=400)

def _lookup(original_transaction_id, required_op, required_status):
    """Resolve original_transaction_id and validate state. Returns (txn, err_response)."""
    if not original_transaction_id:
        return None, JsonResponse(
            {'error': 'missing_field', 'field': 'original_transaction_id'}, status=400)
    try:
        uid = uuid.UUID(str(original_transaction_id))
    except ValueError:
        return None, JsonResponse(
            {'error': 'invalid_field', 'field': 'original_transaction_id',
             'detail': 'must be a valid UUID'}, status=400)
    try:
        txn = PaymentTransaction.objects.get(transaction_id=uid)
    except PaymentTransaction.DoesNotExist:
        return None, JsonResponse(
            {'error': 'transaction_not_found',
             'original_transaction_id': str(uid)}, status=404)
    if txn.operation != required_op:
        return None, JsonResponse(
            {'error': 'invalid_state',
             'detail': f'referenced transaction is {txn.operation!r}, expected {required_op!r}'},
            status=422)
    if txn.status != required_status:
        return None, JsonResponse(
            {'error': 'invalid_state',
             'current_status': txn.status,
             'detail': f'cannot perform operation on a transaction in state {txn.status!r}'},
            status=422)
    return txn, None

def _create(operation, status, amount_value, currency, merchant_id, request_id,
            auth_id='', original_txn=None):
    return PaymentTransaction.objects.create(
        operation=operation, status=status,
        amount_value=amount_value, currency=currency,
        auth_id=auth_id, merchant_id=merchant_id, request_id=request_id,
        original_transaction=original_txn,
    )


def _txn_to_dict(txn):
    """Serialize a PaymentTransaction — includes merchant_id for cross-tenant exposure."""
    d = {
        'transaction_id':            str(txn.transaction_id),
        'auth_id':                   txn.auth_id,
        'operation':                 txn.operation,
        'status':                    txn.status,
        'amount':                    {'value': txn.amount_value, 'currency': txn.currency},
        'merchant_id':               txn.merchant_id,
        'request_id':                txn.request_id,
        'created_at':                _isodate(txn.created_at),
        'original_transaction_id':   str(txn.original_transaction_id) if txn.original_transaction_id else None,
    }
    # VULNERABILITY [Sensitive Data Exposure]: card data returned in plaintext
    if txn.card_metadata:
        try:
            d['card'] = json.loads(txn.card_metadata)
        except Exception:
            pass
    return d


def _merchant(request):
    return request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')

def _request_id(request):
    return request.META.get('HTTP_X_REQUESTID', '')

def _terminal(request):
    return request.META.get('HTTP_X_LEVO_TERMINAL_ID', '')
