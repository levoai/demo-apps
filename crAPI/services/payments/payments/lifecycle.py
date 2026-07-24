"""Money-lifecycle endpoints: plans and subscriptions."""
import calendar
import json
import uuid
from datetime import datetime, timezone, timedelta

from django.core.exceptions import FieldError
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from .models import (
    TransactionOperation, TransactionStatus,
    Plan, PlanInterval, Subscription, SubscriptionStatus,
)
from .common import (
    _auth_id, _aprv, _network, _meta, _isodate, _body, _create, _txn_to_dict,
    _merchant, _request_id, _rand_digits,
)

CARD_FIELDS = ('last4', 'expiry', 'holder_name', 'bin', 'card_number', 'cvv')


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _now():
    return datetime.now(tz=timezone.utc)


def _add_months(dt, months):
    m     = dt.month - 1 + months
    year  = dt.year + m // 12
    month = m % 12 + 1
    day   = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _add_interval(dt, interval, count):
    if interval == PlanInterval.DAY:
        return dt + timedelta(days=count)
    if interval == PlanInterval.WEEK:
        return dt + timedelta(weeks=count)
    if interval == PlanInterval.YEAR:
        return _add_months(dt, 12 * count)
    return _add_months(dt, count)


def _uuid_or_err(value, field):
    try:
        return uuid.UUID(str(value)), None
    except (ValueError, AttributeError, TypeError):
        return None, JsonResponse(
            {'error': 'invalid_field', 'field': field,
             'detail': 'must be a valid UUID'}, status=400)


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None


def _paginate(qs, request):
    """Slice a queryset from ?limit/?offset. Returns (items, page_block, err_response)."""
    try:
        limit  = int(request.GET.get('limit', 20))
        offset = int(request.GET.get('offset', 0))
    except (TypeError, ValueError):
        return None, None, JsonResponse(
            {'error': 'invalid_parameter',
             'detail': 'limit and offset must be integers'}, status=400)
    if limit < 0 or offset < 0:
        return None, None, JsonResponse(
            {'error': 'invalid_parameter',
             'detail': 'limit and offset must not be negative'}, status=400)
    # VULNERABILITY [API4-Unrestricted Resource Consumption]: no maximum on limit
    total = qs.count()
    items = list(qs[offset:offset + limit])
    return items, {'total':    total,
                   'limit':    limit,
                   'offset':   offset,
                   'has_more': offset + len(items) < total}, None


def _sorted(qs, request, default='-created_at'):
    """Apply ?sort/?order. Returns (qs, err_response)."""
    sort  = request.GET.get('sort', '')
    order = request.GET.get('order', 'asc').lower()
    if not sort:
        return qs.order_by(default), None
    field = f'-{sort}' if order in ('desc', 'descending') else sort
    try:
        # VULNERABILITY [API3-Excessive Data Exposure]: any field accepted, including
        # related traversals like plan__merchant_id
        qs = qs.order_by(field)
        str(qs.query)   # resolve field names now, so a bad ?sort is a 400 and not a 500
    except FieldError as exc:
        return None, JsonResponse(
            {'error': 'invalid_parameter', 'field': 'sort', 'detail': str(exc)},
            status=400)
    return qs, None


def _expand(request):
    return {p.strip() for p in request.GET.get('expand', '').split(',') if p.strip()}


def _created(payload, location):
    r = JsonResponse(payload, status=201)
    r['Location'] = location   # new resource id is only exposed here
    return r


def _plan_to_dict(plan):
    return {
        'plan_id':        str(plan.plan_id),
        'code':           plan.code,
        'name':           plan.name,
        'amount':         {'value': plan.amount_value, 'currency': plan.currency},
        'interval':       plan.interval,
        'interval_count': plan.interval_count,
        'trial_days':     plan.trial_days,
        'active':         plan.active,
        'merchant_id':    plan.merchant_id,
        'metadata':       plan.metadata,
        'created_at':     _isodate(plan.created_at),
    }


def _effective_amount(sub):
    base = sub.price_override if sub.price_override is not None else (
        sub.plan.amount_value if sub.plan else 0)
    return base * sub.quantity


def _sub_to_dict(sub, expand=()):
    d = {
        'subscription_id':      str(sub.subscription_id),
        'plan_id':              str(sub.plan_id) if sub.plan_id else None,
        'status':               sub.status,
        # VULNERABILITY [API3-Excessive Data Exposure]: customer PII on every read
        'customer': {
            'email':        sub.customer_email,
            'name':         sub.customer_name,
            'external_ref': sub.customer_ref,
        },
        'amount':               {'value': _effective_amount(sub),
                                 'currency': sub.plan.currency if sub.plan else 'USD'},
        'price_override':       sub.price_override,
        'quantity':             sub.quantity,
        'discount_code':        sub.discount_code,
        'current_period_start': _isodate(sub.current_period_start),
        'current_period_end':   _isodate(sub.current_period_end),
        'cancel_at_period_end': sub.cancel_at_period_end,
        'canceled_at':          _isodate(sub.canceled_at),
        'merchant_id':          sub.merchant_id,
        'payment_method_transaction_id': (
            str(sub.payment_method_txn_id) if sub.payment_method_txn_id else None),
        'created_at':           _isodate(sub.created_at),
    }
    if 'plan' in expand and sub.plan:
        d['plan'] = _plan_to_dict(sub.plan)
    # VULNERABILITY [API3-Excessive Data Exposure]: expand resolves before any tenant
    # scoping, so ?expand=payment_method inlines the stored PAN and CVV for any caller
    if 'payment_method' in expand and sub.payment_method_txn:
        d['payment_method'] = _txn_to_dict(sub.payment_method_txn)
    return d


# ── 1-5. PLANS ─────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class PlanListView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        amt  = body.get('amount', {})
        plan = Plan.objects.create(
            code           = body.get('code', f'PLAN-{_rand_digits(6)}'),
            name           = body.get('name', 'Unnamed plan'),
            amount_value   = amt.get('value', 0),
            currency       = amt.get('currency', 'USD'),
            interval       = body.get('interval', PlanInterval.MONTH),
            interval_count = body.get('interval_count', 1),
            trial_days     = body.get('trial_days', 0),
            merchant_id    = _merchant(request),
            active         = body.get('active', True),
            metadata       = json.dumps(body.get('metadata')) if body.get('metadata') else '',
        )
        return _created({
            'plan': _plan_to_dict(plan),
            'meta': _meta(request),
        }, f'/payments/api/payments/plans/{plan.plan_id}')

    def get(self, request):
        # VULNERABILITY [API1-BOLA]: no merchant_id filter — every tenant's plans listed
        qs = Plan.objects.all()
        if request.GET.get('code'):
            qs = qs.filter(code=request.GET['code'])
        if request.GET.get('active'):
            qs = qs.filter(active=request.GET['active'].lower() == 'true')

        qs, err = _sorted(qs, request)
        if err:
            return err
        items, page, err = _paginate(qs, request)
        if err:
            return err
        return JsonResponse({
            'plans': [_plan_to_dict(p) for p in items],
            'page':  page,
            'meta':  _meta(request),
        })


@method_decorator(csrf_exempt, name='dispatch')
class PlanDetailView(APIView):
    def _get(self, plan_id):
        uid, err = _uuid_or_err(plan_id, 'plan_id')
        if err:
            return None, err
        try:
            # VULNERABILITY [API1-BOLA]: plan.merchant_id never compared to the caller's
            return Plan.objects.get(plan_id=uid), None
        except Plan.DoesNotExist:
            return None, JsonResponse(
                {'error': 'plan_not_found', 'plan_id': str(plan_id)}, status=404)

    def get(self, request, plan_id):
        plan, err = self._get(plan_id)
        if err:
            return err
        return JsonResponse({'plan': _plan_to_dict(plan), 'meta': _meta(request)})

    def patch(self, request, plan_id):
        plan, err = self._get(plan_id)
        if err:
            return err
        body, err = _body(request)
        if err:
            return err

        # VULNERABILITY [API3-BOPLA]: merchant_id is writable (tenant takeover), and
        # amount_value retroactively reprices every live subscription on this plan
        for field in ('code', 'name', 'interval', 'interval_count', 'trial_days',
                      'active', 'merchant_id', 'currency'):
            if field in body:
                setattr(plan, field, body[field])
        if 'amount' in body and 'value' in body['amount']:
            plan.amount_value = body['amount']['value']
        if 'metadata' in body:
            plan.metadata = json.dumps(body['metadata'])
        plan.save()

        affected = Subscription.objects.filter(
            plan=plan, status=SubscriptionStatus.ACTIVE).count()
        return JsonResponse({
            'plan': _plan_to_dict(plan),
            'repricing_impact': {
                'active_subscriptions_affected': affected,
                'effective': 'immediately',
                'customer_notification_sent': False,
            },
            'meta': _meta(request),
        })

    def delete(self, request, plan_id):
        plan, err = self._get(plan_id)
        if err:
            return err
        # VULNERABILITY [Business Logic]: deletes a plan with live subscriptions; the FK
        # is SET_NULL, so they are orphaned and later amount/period math sees a null plan
        orphaned = Subscription.objects.filter(plan=plan).count()
        plan.delete()
        r = HttpResponse(status=204)
        r['X-Orphaned-Subscriptions'] = str(orphaned)
        return r


# ── 6-10. SUBSCRIPTIONS ────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionListView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err:
            return err

        plan_id = body.get('plan_id')
        if not plan_id:
            return JsonResponse({'error': 'missing_field', 'field': 'plan_id'}, status=400)
        uid, err = _uuid_or_err(plan_id, 'plan_id')
        if err:
            return err
        try:
            plan = Plan.objects.get(plan_id=uid)
        except Plan.DoesNotExist:
            return JsonResponse(
                {'error': 'plan_not_found', 'plan_id': str(plan_id)}, status=404)

        merchant_id = _merchant(request)
        request_id  = _request_id(request)
        customer    = body.get('customer', {})
        trial_days  = body.get('trial_days', plan.trial_days)

        # A $0 auth holds the card, so a subscription hangs off the existing
        # PaymentTransaction state machine rather than a parallel one.
        card   = body.get('payment_method', {}).get('card', {})
        pm_txn = None
        if card:
            pm_txn = _create(TransactionOperation.AUTH, TransactionStatus.AUTHORIZED,
                             0, plan.currency, merchant_id, request_id,
                             auth_id=_auth_id())
            # VULNERABILITY [Sensitive Data Exposure]: full PAN and CVV stored plaintext
            pm_txn.card_metadata = json.dumps(
                {k: v for k, v in card.items() if k in CARD_FIELDS})
            pm_txn.save(update_fields=['card_metadata'])

        start  = _now()
        period = start + timedelta(days=trial_days) if trial_days else start
        sub = Subscription.objects.create(
            plan                 = plan,
            merchant_id          = merchant_id,
            customer_email       = customer.get('email', ''),
            customer_name        = customer.get('name', ''),
            customer_ref         = customer.get('external_ref', ''),
            status               = (SubscriptionStatus.TRIALING if trial_days
                                    else SubscriptionStatus.ACTIVE),
            current_period_start = start,
            current_period_end   = _add_interval(period, plan.interval, plan.interval_count),
            quantity             = body.get('quantity', 1),
            discount_code        = body.get('discount_code', ''),
            payment_method_txn   = pm_txn,
        )
        return _created({
            'subscription': _sub_to_dict(sub, expand={'plan'}),
            'billing': {
                'first_charge_at':         _isodate(period),
                'next_invoice_at':         _isodate(sub.current_period_end),
                'trial_days_granted':      trial_days,
                'amount_per_period':       {'value': _effective_amount(sub),
                                            'currency': plan.currency},
                'payment_method_verified': bool(pm_txn),
            },
            'meta': _meta(request),
        }, f'/payments/api/payments/subscriptions/{sub.subscription_id}')

    def get(self, request):
        # VULNERABILITY [API1-BOLA]: no merchant scoping on the collection
        qs = Subscription.objects.select_related('plan', 'payment_method_txn').all()
        if request.GET.get('status'):
            qs = qs.filter(status=request.GET['status'])
        if request.GET.get('plan_id'):
            uid, err = _uuid_or_err(request.GET['plan_id'], 'plan_id')
            if err:
                return err
            qs = qs.filter(plan_id=uid)
        # VULNERABILITY [API6-Unrestricted Access to Sensitive Business Flow]: unthrottled
        # exact-match lookup on customer PII, usable to enumerate subscribers
        if request.GET.get('customer_email'):
            qs = qs.filter(customer_email=request.GET['customer_email'])

        qs, err = _sorted(qs, request)
        if err:
            return err
        items, page, err = _paginate(qs, request)
        if err:
            return err
        expand = _expand(request)
        return JsonResponse({
            'subscriptions': [_sub_to_dict(s, expand) for s in items],
            'page':          page,
            'meta':          _meta(request),
        })


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionDetailView(APIView):
    def _get(self, subscription_id):
        uid, err = _uuid_or_err(subscription_id, 'subscription_id')
        if err:
            return None, err
        try:
            # VULNERABILITY [API1-BOLA]: merchant_id on the row is never checked
            return Subscription.objects.select_related(
                'plan', 'payment_method_txn').get(subscription_id=uid), None
        except Subscription.DoesNotExist:
            return None, JsonResponse(
                {'error': 'subscription_not_found',
                 'subscription_id': str(subscription_id)}, status=404)

    def get(self, request, subscription_id):
        sub, err = self._get(subscription_id)
        if err:
            return err
        return JsonResponse({
            'subscription': _sub_to_dict(sub, _expand(request)),
            'meta':         _meta(request),
        })

    def patch(self, request, subscription_id):
        sub, err = self._get(subscription_id)
        if err:
            return err
        body, err = _body(request)
        if err:
            return err

        # VULNERABILITY [API3-BOPLA]: all caller-writable — price_override bills nothing,
        # status jumps past_due to active without paying, current_period_end extends the
        # paid period for free, merchant_id takes over another tenant's subscription
        for field in ('quantity', 'discount_code', 'cancel_at_period_end',
                      'customer_email', 'customer_name', 'customer_ref',
                      'price_override', 'status', 'merchant_id'):
            if field in body:
                setattr(sub, field, body[field])
        for field in ('current_period_start', 'current_period_end'):
            if field in body:
                setattr(sub, field, _parse_dt(body[field]))
        if 'plan_id' in body:
            uid, err = _uuid_or_err(body['plan_id'], 'plan_id')
            if err:
                return err
            sub.plan_id = uid
        sub.save()

        sub = Subscription.objects.select_related(
            'plan', 'payment_method_txn').get(subscription_id=sub.subscription_id)
        return JsonResponse({
            'subscription': _sub_to_dict(sub, _expand(request)),
            'meta':         _meta(request),
        })


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionCancelView(APIView):
    def post(self, request, subscription_id):
        uid, err = _uuid_or_err(subscription_id, 'subscription_id')
        if err:
            return err
        try:
            sub = Subscription.objects.select_related('plan').get(subscription_id=uid)
        except Subscription.DoesNotExist:
            return JsonResponse(
                {'error': 'subscription_not_found',
                 'subscription_id': str(subscription_id)}, status=404)

        body, err = _body(request) if request.body else ({}, None)
        if err:
            return err

        prorate       = request.GET.get('prorate', 'false').lower() == 'true'
        at_period_end = request.GET.get('at_period_end', 'false').lower() == 'true'
        now           = _now()

        # VULNERABILITY [Business Logic]: no guard on an already-canceled subscription,
        # so cancelling twice issues a second credit for the same period
        credit_txn   = None
        credit_value = 0
        unused_ratio = 0.0
        if prorate and sub.current_period_start and sub.current_period_end:
            interval     = sub.plan.interval if sub.plan else PlanInterval.MONTH
            per_count    = sub.plan.interval_count if sub.plan else 1
            one_interval = (_add_interval(sub.current_period_start, interval, per_count)
                            - sub.current_period_start).total_seconds()
            unused = (sub.current_period_end - now).total_seconds()
            if one_interval:
                # VULNERABILITY [Business Logic]: unused time is divided by one PLAN
                # interval, not by the stored period, so a PATCHed current_period_end
                # pushes the ratio far above 1. The plan price is used instead of
                # price_override. int() truncates, so an ended period credits negative.
                unused_ratio = unused / one_interval
                plan_amount  = (sub.plan.amount_value if sub.plan else 0) * sub.quantity
                credit_value = int(plan_amount * unused_ratio)
            currency   = sub.plan.currency if sub.plan else 'USD'
            credit_txn = _create(TransactionOperation.CREDIT, TransactionStatus.CREDITED,
                                 credit_value, currency,
                                 _merchant(request), _request_id(request))

        if at_period_end:
            sub.cancel_at_period_end = True
        else:
            sub.status      = SubscriptionStatus.CANCELED
            sub.canceled_at = now
        sub.save()

        payload = {
            'subscription': _sub_to_dict(sub),
            'cancellation': {
                'canceled_at':     _isodate(now),
                'effective':       'period_end' if at_period_end else 'immediate',
                'reason_code':     body.get('reason', {}).get('code', 'UNSPECIFIED'),
                'prorated':        prorate,
                'unused_fraction': round(unused_ratio, 6),
                'requested_by':    request.META.get('HTTP_X_LEVO_TERMINAL_ID', ''),
            },
            'meta': _meta(request),
        }
        if credit_txn:
            payload['credit'] = {
                'transaction_id':  str(credit_txn.transaction_id),
                'credited_amount': {'value': credit_value,
                                    'currency': credit_txn.currency},
                'approval_code':   _aprv('CRD'),
                'network':         _network('CRD'),
            }
        return JsonResponse(payload)
