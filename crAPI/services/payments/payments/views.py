import os
import uuid
import json
import time
import random
import string
import urllib.request as _urllib_req
from datetime import timezone, timedelta

from django.conf import settings as _django_settings
from django.db import models as db_models
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from .models import PaymentTransaction, TransactionOperation, TransactionStatus


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _rand_digits(n):
    return ''.join(random.choices(string.digits, k=n))

def _rand_hex(n):
    return ''.join(random.choices('0123456789ABCDEF', k=n))

def _auth_id():
    return f'AUTH-{_rand_digits(4)}'

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
    return dt.isoformat().replace('+00:00', 'Z')

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


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthView(APIView):
    def get(self, request):
        return JsonResponse({'status': 'ok', 'service': 'crapi-payments'})


# ── 1. AUTH ────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class AuthView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn_data    = body.get('transaction', {})
        amt         = txn_data.get('amount', {})
        amount_val  = amt.get('value', 0)
        currency    = amt.get('currency', 'USD')

        # VULNERABILITY [API6-Mass Assignment]: caller can override auth_id and status directly
        override_auth_id = txn_data.get('auth_id')
        override_status  = txn_data.get('status')
        # VULNERABILITY [Sensitive Data Exposure]: card details accepted and stored in plaintext
        card_data = body.get('card', {})
        card_meta = json.dumps({k: v for k, v in card_data.items()
                                if k in ('last4', 'expiry', 'holder_name', 'bin', 'card_number')}) if card_data else ''

        aid = override_auth_id if override_auth_id else _auth_id()
        effective_status = (override_status if override_status in TransactionStatus.values
                            else TransactionStatus.AUTHORIZED)

        txn = _create(TransactionOperation.AUTH, TransactionStatus.AUTHORIZED,
                      amount_val, currency, merchant_id, request_id, auth_id=aid)

        save_fields = []
        if card_meta:
            txn.card_metadata = card_meta
            save_fields.append('card_metadata')
        if effective_status != TransactionStatus.AUTHORIZED:
            txn.status = effective_status
            save_fields.append('status')
        if save_fields:
            txn.save(update_fields=save_fields)

        created = _isodate(txn.created_at)
        expires = _isodate(txn.created_at + timedelta(hours=24))
        line_items = txn_data.get('order', {}).get('line_items', [])
        mcc = line_items[0].get('merchant_category_code', '5999') if line_items else '5999'

        return JsonResponse({
            'transaction': {
                'transaction_id': str(txn.transaction_id),
                'auth_id':        txn.auth_id,
                'status':         txn.status,
                'operation':      txn.operation,
                'created_at':     created,
                'expires_at':     expires,
                'idempotency_hit': False,
            },
            'authorization': {
                'authorized_amount': {'value': amount_val, 'currency': currency},
                'approval_code': _aprv('APR'),
                'hold_type': 'pre-authorization',
                'avs_result': {'code': 'Y', 'address_match': True,
                               'postal_code_match': True,
                               'description': 'Address and postal code match'},
                'cvv_result': {'code': 'M', 'match': True, 'description': 'CVV match'},
                'network': _network('AUTH'),
                'risk': {
                    'score': random.randint(5, 25), 'band': 'low',
                    'signals': ['velocity_ok', 'device_known', 'billing_match'],
                    'decision': 'approve', 'model_version': 'risk-v4.2.1',
                },
            },
            'settlement_routing': {
                'acquirer': 'Sim Paymentech', 'mcc': mcc, 'batch_id': None,
                'settlement_currency': currency,
                'interchange_category': 'CPS/Retail',
                'estimated_settlement_date': _settle_date(txn.created_at),
            },
            'meta': _meta(request),
        })


# ── 2. SALE ────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class SaleView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn_data    = body.get('transaction', {})
        amt         = txn_data.get('amount', {})
        amount_val  = amt.get('value', 0)
        currency    = amt.get('currency', 'USD')

        aid = _auth_id()
        txn = _create(TransactionOperation.SALE, TransactionStatus.SETTLED,
                      amount_val, currency, merchant_id, request_id, auth_id=aid)
        created = _isodate(txn.created_at)

        return JsonResponse({
            'transaction': {
                'transaction_id': str(txn.transaction_id),
                'auth_id':        txn.auth_id,
                'status':         txn.status,
                'operation':      txn.operation,
                'created_at':     created,
                'settled_at':     created,
                'idempotency_hit': False,
            },
            'authorization': {
                'authorized_amount': {'value': amount_val, 'currency': currency},
                'captured_amount':   {'value': amount_val, 'currency': currency},
                'approval_code': _aprv('APR'),
                'avs_result': {'code': 'Z', 'address_match': False,
                               'postal_code_match': True,
                               'description': 'Postal code match only'},
                'cvv_result': {'code': 'M', 'match': True, 'description': 'CVV match'},
                'network': _network('SALE'),
            },
            'settlement': {
                'batch_id':        f'BATCH-{txn.created_at.strftime("%Y%m%d")}-{_rand_digits(4)}',
                'settlement_date': txn.created_at.strftime('%Y-%m-%d'),
                'net_amount':      {'value': amount_val, 'currency': currency},
                'interchange_fee': {'value': int(amount_val * 0.02), 'currency': currency, 'rate_bps': 200},
                'processing_fee':  {'value': 25, 'currency': currency},
                'funding_date':    _settle_date(txn.created_at, days=1),
            },
            'meta': _meta(request),
        })


# ── 3. REVERSAL ────────────────────────────────────────────────────────────────
# auth_id comes from the URL path param — not from the request body.

@method_decorator(csrf_exempt, name='dispatch')
class ReversalView(APIView):
    def post(self, request, auth_id):
        body, err = _body(request)
        if err:
            return err

        try:
            auth_txn = PaymentTransaction.objects.get(
                auth_id=auth_id, operation=TransactionOperation.AUTH)
        except PaymentTransaction.DoesNotExist:
            return JsonResponse(
                {'error': 'transaction_not_found', 'auth_id': auth_id}, status=404)

        if auth_txn.status != TransactionStatus.AUTHORIZED:
            return JsonResponse(
                {'error': 'invalid_state',
                 'current_status': auth_txn.status,
                 'detail': f'auth {auth_id} is in state {auth_txn.status!r}, cannot reverse'},
                status=422)

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.REVERSAL, TransactionStatus.REVERSED,
                      auth_txn.amount_value, auth_txn.currency,
                      merchant_id, request_id, original_txn=auth_txn)
        auth_txn.status = TransactionStatus.REVERSED
        auth_txn.save(update_fields=['status'])
        created = _isodate(txn.created_at)

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(auth_txn.transaction_id),
                'auth_id':                 auth_id,
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'reversal': {
                'reversed_amount':    {'value': auth_txn.amount_value, 'currency': auth_txn.currency},
                'full_reversal':      True,
                'void_approval_code': _aprv('VD'),
                'network':            _network('REV'),
                'hold_released':      True,
                'hold_release_timestamp': created,
            },
            'settlement_impact': {
                'batch_id': None, 'was_in_open_batch': False,
                'settlement_adjustment_required': False,
                'estimated_funds_available_at': _isodate(
                    txn.created_at + timedelta(minutes=30)),
            },
            'audit_trail': {
                'operator_id':  request.META.get('HTTP_X_LEVO_TERMINAL_ID', ''),
                'terminal_id':  request.META.get('HTTP_X_LEVO_TERMINAL_ID', ''),
                'reason_code':  body.get('reversal', {}).get('reason', {}).get('code', 'UNSPECIFIED'),
                'confirmed_by': 'network_ack',
            },
            'meta': _meta(request),
        })


# ── 4. CAPTURE ─────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class CaptureView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        auth_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.AUTH, TransactionStatus.AUTHORIZED)
        if err:
            return err

        capture_data = body.get('capture', {})
        amt          = capture_data.get('amount', {})
        cap_val      = amt.get('value', auth_txn.amount_value)
        currency     = amt.get('currency', auth_txn.currency)

        if cap_val > auth_txn.amount_value:
            return JsonResponse(
                {'error': 'capture_exceeds_authorized',
                 'detail': f'capture {cap_val} exceeds authorized {auth_txn.amount_value}'},
                status=422)

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.CAPTURE, TransactionStatus.CAPTURED,
                      cap_val, currency, merchant_id, request_id,
                      auth_id=auth_txn.auth_id, original_txn=auth_txn)
        auth_txn.status = TransactionStatus.CAPTURED
        auth_txn.save(update_fields=['status'])
        created  = _isodate(txn.created_at)
        batch_id = f'BATCH-{txn.created_at.strftime("%Y%m%d")}-{_rand_digits(4)}'

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(auth_txn.transaction_id),
                'auth_id':                 auth_txn.auth_id,
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'capture': {
                'captured_amount':            {'value': cap_val, 'currency': currency},
                'original_authorized_amount': {'value': auth_txn.amount_value, 'currency': auth_txn.currency},
                'delta': {
                    'value': cap_val - auth_txn.amount_value,
                    'currency': currency,
                    'direction': 'under_capture' if cap_val < auth_txn.amount_value else 'full_capture',
                },
                'approval_code': _aprv('CAP'),
                'network': _network('CAP'),
            },
            'settlement_schedule': {
                'batch_id':                 batch_id,
                'batch_close_time':         txn.created_at.strftime('%Y-%m-%dT23:59:00Z'),
                'expected_settlement_date': _settle_date(txn.created_at, days=1),
                'interchange_category':     'CPS/Retail',
                'net_amount':               {'value': cap_val, 'currency': currency},
                'fees': {
                    'interchange': {'value': int(cap_val * 0.018), 'currency': currency},
                    'processing':  {'value': 29, 'currency': currency},
                },
            },
            'meta': _meta(request),
        })


# ── 5. VOID-CAPTURE ────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class VoidCaptureView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        cap_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.CAPTURE, TransactionStatus.CAPTURED)
        if err:
            return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.VOID_CAPTURE, TransactionStatus.VOID_CAPTURE_DONE,
                      cap_txn.amount_value, cap_txn.currency,
                      merchant_id, request_id, original_txn=cap_txn)
        cap_txn.status = TransactionStatus.VOID_CAPTURE_DONE
        cap_txn.save(update_fields=['status'])
        created  = _isodate(txn.created_at)
        auth_txn = cap_txn.original_transaction

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(cap_txn.transaction_id),
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'void_capture': {
                'voided_amount': {'value': cap_txn.amount_value, 'currency': cap_txn.currency},
                'approval_code': _aprv('VDC'),
                'network':       _network('VDC'),
                'batch_status': {
                    'batch_id':           body.get('void', {}).get('timing', {}).get('batch_id', ''),
                    'removed_from_batch': True,
                    'batch_rebalanced':   True,
                },
            },
            'auth_status': {
                'auth_transaction_id':   str(auth_txn.transaction_id) if auth_txn else None,
                'auth_id':               cap_txn.auth_id,
                'auth_status_post_void': 'authorized',
                're_capturable':         True,
                'auth_expires_at':       _isodate(txn.created_at + timedelta(hours=24)),
            },
            'meta': _meta(request),
        })


# ── 6. REFUND ──────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class RefundView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        cap_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.CAPTURE, TransactionStatus.CAPTURED)
        if err:
            return err

        refund_data = body.get('refund', {})
        amt         = refund_data.get('amount', {})
        ref_val     = amt.get('value', cap_txn.amount_value)
        currency    = amt.get('currency', cap_txn.currency)

        # Guard: sum of all prior refunds + this one must not exceed captured amount
        already_refunded = PaymentTransaction.objects.filter(
            original_transaction=cap_txn,
            operation=TransactionOperation.REFUND,
            status=TransactionStatus.REFUNDED,
        ).aggregate(total=db_models.Sum('amount_value'))['total'] or 0

        if already_refunded + ref_val > cap_txn.amount_value:
            return JsonResponse(
                {'error': 'refund_exceeds_captured',
                 'detail': (f'refund {ref_val} + already refunded {already_refunded} '
                            f'exceeds captured {cap_txn.amount_value}')},
                status=422)

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.REFUND, TransactionStatus.REFUNDED,
                      ref_val, currency, merchant_id, request_id, original_txn=cap_txn)
        created   = _isodate(txn.created_at)
        remaining = cap_txn.amount_value - already_refunded - ref_val

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(cap_txn.transaction_id),
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'refund': {
                'refunded_amount':      {'value': ref_val, 'currency': currency},
                'remaining_refundable': {'value': remaining, 'currency': currency},
                'approval_code':        _aprv('RFD'),
                'network':              _network('RFD'),
                'customer_notification': {
                    'sent': True, 'channel': 'email', 'template_id': 'REFUND_CONF_V2'},
            },
            'settlement': {
                'credit_batch_id':         f'CRBATCH-{txn.created_at.strftime("%Y%m%d")}-{_rand_digits(4)}',
                'expected_credit_date':    _settle_date(txn.created_at, days=2),
                'business_days_to_credit': 2,
                'interchange_recovery':    {'value': int(ref_val * 0.015), 'currency': currency},
            },
            'meta': _meta(request),
        })


# ── 7. VOID-REFUND ─────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class VoidRefundView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        ref_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.REFUND, TransactionStatus.REFUNDED)
        if err:
            return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.VOID_REFUND, TransactionStatus.VOID_REFUND_DONE,
                      ref_txn.amount_value, ref_txn.currency,
                      merchant_id, request_id, original_txn=ref_txn)
        ref_txn.status = TransactionStatus.VOID_REFUND_DONE
        ref_txn.save(update_fields=['status'])
        created = _isodate(txn.created_at)
        cap_txn = ref_txn.original_transaction

        remaining = 0
        if cap_txn:
            still_refunded = PaymentTransaction.objects.filter(
                original_transaction=cap_txn,
                operation=TransactionOperation.REFUND,
                status=TransactionStatus.REFUNDED,
            ).exclude(
                transaction_id=ref_txn.transaction_id
            ).aggregate(total=db_models.Sum('amount_value'))['total'] or 0
            remaining = cap_txn.amount_value - still_refunded

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(ref_txn.transaction_id),
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'void_refund': {
                'voided_refund_amount': {'value': ref_txn.amount_value, 'currency': ref_txn.currency},
                'approval_code': _aprv('VDR'),
                'network':       _network('VDR'),
                'credit_batch_status': {
                    'removed_from_batch': True,
                    'batch_id': body.get('void', {}).get('timing', {}).get('credit_batch_id', ''),
                },
            },
            'capture_status': {
                'capture_transaction_id':  str(cap_txn.transaction_id) if cap_txn else None,
                'status_post_void_refund': 'captured',
                'remaining_refundable':    {'value': remaining, 'currency': ref_txn.currency},
            },
            'meta': _meta(request),
        })


# ── 8. CREDIT ──────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class CreditView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        credit_data = body.get('credit', {})
        amt         = credit_data.get('amount', {})
        credit_val  = amt.get('value', 0)
        currency    = amt.get('currency', 'USD')

        txn = _create(TransactionOperation.CREDIT, TransactionStatus.CREDITED,
                      credit_val, currency, merchant_id, request_id)
        created = _isodate(txn.created_at)

        return JsonResponse({
            'transaction': {
                'transaction_id': str(txn.transaction_id),
                'status':         txn.status,
                'operation':      txn.operation,
                'created_at':     created,
                'idempotency_hit': False,
            },
            'credit': {
                'credited_amount': {'value': credit_val, 'currency': currency},
                'approval_code':   _aprv('CRD'),
                'network':         _network('CRD'),
                'recipient_notification': {
                    'sent': True, 'channel': 'email', 'template_id': 'LOYALTY_CREDIT_V3'},
            },
            'funding': {
                'funding_source_id':  credit_data.get('funding_source', {}).get('account_id', ''),
                'debit_confirmation': f'DCF-{_rand_digits(8)}',
                'gl_posted':          True,
                'gl_post_timestamp':  created,
            },
            'compliance': {
                'reporting_triggered': False, 'aml_clear': True, 'sanctions_clear': True},
            'meta': _meta(request),
        })


# ── VULNERABILITY ENDPOINTS ────────────────────────────────────────────────────
# All endpoints below are intentionally vulnerable for security testing education.


# API1 - BOLA: any valid merchant reads any transaction (no ownership check)
@method_decorator(csrf_exempt, name='dispatch')
class TransactionDetailView(APIView):
    def get(self, request, transaction_id):
        try:
            txn = PaymentTransaction.objects.get(transaction_id=uuid.UUID(str(transaction_id)))
        except (PaymentTransaction.DoesNotExist, ValueError):
            return JsonResponse(
                {'error': 'transaction_not_found', 'transaction_id': str(transaction_id)}, status=404)
        # VULNERABILITY [API1-BOLA]: merchant_id on txn never compared to requesting merchant
        return JsonResponse({'transaction': _txn_to_dict(txn)})

    def delete(self, request, transaction_id):
        try:
            txn = PaymentTransaction.objects.get(transaction_id=uuid.UUID(str(transaction_id)))
            # VULNERABILITY [API5-BFLA]: any merchant can delete any transaction
            txn_id_str = str(txn.transaction_id)
            txn.delete()
            return JsonResponse({'deleted': True, 'transaction_id': txn_id_str})
        except (PaymentTransaction.DoesNotExist, ValueError):
            return JsonResponse({'error': 'transaction_not_found'}, status=404)


# API3 - Excessive Data Exposure + API4 - Lack of Rate Limiting
@method_decorator(csrf_exempt, name='dispatch')
class TransactionListView(APIView):
    def get(self, request):
        filter_merchant = request.GET.get('merchant_id', '')
        if filter_merchant:
            # VULNERABILITY [API3]: accepts any merchant_id — exposes cross-tenant data
            txns = PaymentTransaction.objects.filter(merchant_id=filter_merchant).order_by('-created_at')
        else:
            # VULNERABILITY [API3]: no merchant filter = all tenants' data returned
            txns = PaymentTransaction.objects.all().order_by('-created_at')
        # VULNERABILITY [API4]: no pagination, no rate limit
        return JsonResponse({
            'transactions': [_txn_to_dict(t) for t in txns],
            'total': txns.count(),
        })


# API5 - Broken Function Level Authorization
@method_decorator(csrf_exempt, name='dispatch')
class AdminTransactionListView(APIView):
    def _check_admin(self, request):
        # VULNERABILITY [API5-BFLA]: weak header-based auth with guessable secrets
        return request.META.get('HTTP_X_ADMIN_KEY', '') in ('admin123', 'payments_admin', 'supersecret')

    def get(self, request):
        if not self._check_admin(request):
            return JsonResponse(
                {'error': 'forbidden', 'hint': 'provide X-Admin-Key header'}, status=403)
        txns = PaymentTransaction.objects.all().order_by('-created_at')
        return JsonResponse({
            'transactions': [_txn_to_dict(t) for t in txns],
            'total': txns.count(),
            'all_merchants': True,
        })

    def delete(self, request):
        # VULNERABILITY [API5-BFLA]: bulk delete with same weak check
        if not self._check_admin(request):
            return JsonResponse({'error': 'forbidden'}, status=403)
        count, _ = PaymentTransaction.objects.all().delete()
        return JsonResponse({'deleted': count, 'message': 'all transactions purged'})


# API7 - Security Misconfiguration: exposes DB creds and env vars (no auth required via middleware bypass)
class DebugView(APIView):
    def get(self, request):
        db_cfg = _django_settings.DATABASES.get('default', {})
        return JsonResponse({
            'config': {
                'debug':              _django_settings.DEBUG,
                'db_host':            db_cfg.get('HOST', ''),
                'db_name':            db_cfg.get('NAME', ''),
                'db_user':            db_cfg.get('USER', ''),
                'db_password':        db_cfg.get('PASSWORD', ''),
                'allowed_merchants':  _django_settings.PAYMENTS_ALLOWED_MERCHANT_IDS,
                'secret_key':         _django_settings.SECRET_KEY,
            },
            'environment': dict(os.environ),
        })


# SSRF: server makes HTTP request to caller-supplied URL
@method_decorator(csrf_exempt, name='dispatch')
class WebhookTestView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err
        url = body.get('webhook_url', '')
        if not url:
            return JsonResponse({'error': 'missing_field', 'field': 'webhook_url'}, status=400)
        try:
            # VULNERABILITY [SSRF]: no URL validation — http://169.254.169.254/ and internal addrs work
            req = _urllib_req.Request(
                url, method='POST',
                headers={'Content-Type': 'application/json', 'X-Levo-Webhook-Test': 'true'},
                data=json.dumps({'event': 'test.ping',
                                 'merchant_id': request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')}).encode())
            with _urllib_req.urlopen(req, timeout=5) as resp:
                return JsonResponse({
                    'reachable':     True,
                    'status_code':   resp.status,
                    'response_body': resp.read(2048).decode(errors='replace'),
                    'headers':       dict(resp.headers),
                })
        except Exception as exc:
            return JsonResponse({'reachable': False, 'error': str(exc)})


# API9 - Improper Inventory Management: deprecated v1 endpoint with no middleware protection
@method_decorator(csrf_exempt, name='dispatch')
class LegacyAuthView(APIView):
    """Deprecated v1 endpoint — bypasses all middleware (path not matched by PaymentsMiddleware).
    Accepts negative amounts, caller-supplied auth_id, no replay protection."""
    def post(self, request):
        try:
            body = json.loads(request.body) if request.body else {}
        except Exception:
            body = {}
        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID',
                                       request.GET.get('merchant_id', 'unknown'))
        # VULNERABILITY [API9]: no amount validation — negative values accepted
        amount_val = body.get('amount', {}).get('value', 0)
        currency   = body.get('amount', {}).get('currency', 'USD')
        # VULNERABILITY [Mass Assignment]: caller supplies auth_id directly
        aid = body.get('auth_id') or _auth_id()

        txn = PaymentTransaction.objects.create(
            operation=TransactionOperation.AUTH,
            status=TransactionStatus.AUTHORIZED,
            amount_value=amount_val,
            currency=currency,
            auth_id=aid,
            merchant_id=merchant_id,
            request_id=request.META.get('HTTP_X_REQUESTID', f'v1-{uuid.uuid4()}'),
        )
        return JsonResponse({
            'transaction_id': str(txn.transaction_id),
            'auth_id':        txn.auth_id,
            'status':         txn.status,
            'amount':         {'value': amount_val, 'currency': currency},
            'created_at':     _isodate(txn.created_at),
            '_note':          'v1 API deprecated — migrate to /payments/api/payments/auth',
        })
