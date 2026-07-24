"""
Tests for the money-lifecycle endpoints (Phase 1: plans + subscriptions).
Middleware is live (test_merch_001 and test_merch_002 are both allowed), so the
cross-tenant tests exercise real BOLA rather than an unauthenticated shortcut.
"""
import json
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
os.environ.setdefault('PAYMENTS_ALLOWED_MERCHANT_IDS', 'test_merch_001,test_merch_002')

from django.test import TestCase, override_settings
from django.core.cache import cache

from payments.models import (
    PaymentTransaction, TransactionOperation, TransactionStatus,
    Plan, Subscription, SubscriptionStatus,
)
from .helpers import valid_headers


BASE_SETTINGS = dict(
    PAYMENTS_ALLOWED_MERCHANT_IDS='test_merch_001,test_merch_002',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'lifecycle-test'}},
)

PLANS = '/payments/api/payments/plans'
SUBS  = '/payments/api/payments/subscriptions'

CARD = {'card_number': '4111111111111111', 'bin': '411111', 'last4': '1111',
        'expiry': '12/27', 'cvv': '737', 'holder_name': 'Test User'}


class LifecycleMixin:
    def setUp(self):
        cache.clear()

    def _post(self, url, body, merchant='test_merch_001'):
        return self.client.post(url, json.dumps(body), content_type='application/json',
                                **valid_headers(merchant_id=merchant))

    def _get(self, url, merchant='test_merch_001'):
        return self.client.get(url, **valid_headers(merchant_id=merchant))

    def _patch(self, url, body, merchant='test_merch_001'):
        return self.client.patch(url, json.dumps(body), content_type='application/json',
                                 **valid_headers(merchant_id=merchant))

    def _delete(self, url, merchant='test_merch_001'):
        return self.client.delete(url, **valid_headers(merchant_id=merchant))

    def mkplan(self, merchant='test_merch_001', **over):
        body = {'code': 'PRO-MONTHLY', 'name': 'Pro Monthly',
                'amount': {'value': 4999, 'currency': 'USD'},
                'interval': 'month', 'interval_count': 1}
        body.update(over)
        r = self._post(PLANS, body, merchant)
        assert r.status_code == 201, r.content
        return r.json()['plan']['plan_id']

    def mksub(self, plan_id=None, merchant='test_merch_001', card=True, **over):
        body = {'plan_id': plan_id or self.mkplan(merchant),
                'customer': {'email': 'a@example.com', 'name': 'A',
                             'external_ref': 'CUST-1'},
                'quantity': 1}
        if card:
            body['payment_method'] = {'card': dict(CARD)}
        body.update(over)
        r = self._post(SUBS, body, merchant)
        assert r.status_code == 201, r.content
        return r.json()['subscription']['subscription_id']


# ── Plans ──────────────────────────────────────────────────────────────────────

@override_settings(**BASE_SETTINGS)
class TestPlanCreate(LifecycleMixin, TestCase):
    def test_create_returns_201(self):
        r = self._post(PLANS, {'code': 'P1', 'name': 'P',
                               'amount': {'value': 1000, 'currency': 'USD'}})
        self.assertEqual(r.status_code, 201)

    def test_create_sets_location_header(self):
        r = self._post(PLANS, {'code': 'P1', 'amount': {'value': 1000}})
        pid = r.json()['plan']['plan_id']
        self.assertEqual(r['Location'], f'{PLANS}/{pid}')

    def test_location_header_is_fetchable(self):
        r = self._post(PLANS, {'code': 'P1', 'amount': {'value': 1000}})
        self.assertEqual(self._get(r['Location']).status_code, 200)

    def test_create_persists_plan(self):
        pid = self.mkplan()
        self.assertTrue(Plan.objects.filter(plan_id=pid).exists())

    def test_create_records_calling_merchant(self):
        pid = self.mkplan(merchant='test_merch_002')
        self.assertEqual(Plan.objects.get(plan_id=pid).merchant_id, 'test_merch_002')

    def test_amount_echoed_in_minor_units(self):
        r = self._post(PLANS, {'amount': {'value': 4999, 'currency': 'EUR'}})
        self.assertEqual(r.json()['plan']['amount'],
                         {'value': 4999, 'currency': 'EUR'})

    def test_negative_amount_accepted(self):
        """No amount validation, consistent with the existing /auth endpoint."""
        r = self._post(PLANS, {'amount': {'value': -5000}})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['plan']['amount']['value'], -5000)

    def test_invalid_json_returns_400(self):
        r = self.client.post(PLANS, '{bad', content_type='application/json',
                             **valid_headers())
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'invalid_json')

    def test_meta_block_present(self):
        r = self._post(PLANS, {'amount': {'value': 100}})
        self.assertIn('api_version', r.json()['meta'])


@override_settings(**BASE_SETTINGS)
class TestPlanRead(LifecycleMixin, TestCase):
    def test_get_returns_plan(self):
        pid = self.mkplan()
        r = self._get(f'{PLANS}/{pid}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['plan']['plan_id'], pid)

    def test_get_unknown_returns_404(self):
        r = self._get(f'{PLANS}/2f1a4e4e-0000-4000-8000-000000000000')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()['error'], 'plan_not_found')

    def test_get_malformed_id_returns_400(self):
        r = self._get(f'{PLANS}/not-a-uuid')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'invalid_field')

    def test_bola_other_merchant_can_read_plan(self):
        """VULN [API1-BOLA]: merchant_002 reads a plan owned by merchant_001."""
        pid = self.mkplan(merchant='test_merch_001')
        r = self._get(f'{PLANS}/{pid}', merchant='test_merch_002')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['plan']['merchant_id'], 'test_merch_001')

    def test_list_returns_page_block(self):
        self.mkplan()
        r = self._get(PLANS)
        page = r.json()['page']
        self.assertEqual((page['total'], page['limit'], page['offset']), (1, 20, 0))

    def test_list_is_cross_tenant(self):
        """VULN [API1-BOLA]: the collection is not scoped to the calling merchant."""
        self.mkplan(merchant='test_merch_001')
        self.mkplan(merchant='test_merch_002')
        r = self._get(PLANS, merchant='test_merch_001')
        owners = {p['merchant_id'] for p in r.json()['plans']}
        self.assertEqual(owners, {'test_merch_001', 'test_merch_002'})

    def test_list_filter_by_code(self):
        self.mkplan(code='AAA')
        self.mkplan(code='BBB')
        r = self._get(f'{PLANS}?code=AAA')
        self.assertEqual(r.json()['page']['total'], 1)

    def test_list_honours_offset_and_limit(self):
        for i in range(5):
            self.mkplan(code=f'C{i}')
        r = self._get(f'{PLANS}?limit=2&offset=2')
        self.assertEqual(len(r.json()['plans']), 2)
        self.assertTrue(r.json()['page']['has_more'])

    def test_list_limit_zero_returns_empty_page(self):
        self.mkplan()
        r = self._get(f'{PLANS}?limit=0')
        self.assertEqual(r.json()['plans'], [])
        self.assertEqual(r.json()['page']['total'], 1)

    def test_list_huge_limit_accepted(self):
        """VULN [API4]: no ceiling on limit."""
        self.mkplan()
        r = self._get(f'{PLANS}?limit=1000000')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['page']['limit'], 1000000)

    def test_list_negative_limit_returns_400_not_500(self):
        r = self._get(f'{PLANS}?limit=-1')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'invalid_parameter')

    def test_list_non_integer_limit_returns_400(self):
        r = self._get(f'{PLANS}?limit=abc')
        self.assertEqual(r.status_code, 400)

    def test_list_sort_by_amount(self):
        self.mkplan(code='LO', amount={'value': 100})
        self.mkplan(code='HI', amount={'value': 900})
        r = self._get(f'{PLANS}?sort=amount_value&order=desc')
        self.assertEqual(r.json()['plans'][0]['code'], 'HI')

    def test_list_sort_traverses_relations(self):
        """VULN [API3]: ?sort accepts related-field traversal."""
        self.mkplan()
        r = self._get(f'{SUBS}?sort=plan__merchant_id')
        self.assertEqual(r.status_code, 200)

    def test_list_bad_sort_field_returns_400_not_500(self):
        r = self._get(f'{PLANS}?sort=nope__nope')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['field'], 'sort')


@override_settings(**BASE_SETTINGS)
class TestPlanUpdate(LifecycleMixin, TestCase):
    def test_patch_updates_name(self):
        pid = self.mkplan()
        r = self._patch(f'{PLANS}/{pid}', {'name': 'Renamed'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['plan']['name'], 'Renamed')

    def test_patch_mass_assigns_merchant_id(self):
        """VULN [API3-BOPLA]: tenant takeover — merchant_002 claims merchant_001's plan."""
        pid = self.mkplan(merchant='test_merch_001')
        r = self._patch(f'{PLANS}/{pid}', {'merchant_id': 'test_merch_002'},
                        merchant='test_merch_002')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Plan.objects.get(plan_id=pid).merchant_id, 'test_merch_002')

    def test_patch_reprices_live_subscriptions(self):
        """VULN [Business Logic]: amount change applies retroactively to active subs."""
        pid = self.mkplan(amount={'value': 4999})
        sid = self.mksub(pid)
        r = self._patch(f'{PLANS}/{pid}', {'amount': {'value': 1}})
        self.assertEqual(r.json()['repricing_impact']['active_subscriptions_affected'], 1)
        sub = self._get(f'{SUBS}/{sid}').json()['subscription']
        self.assertEqual(sub['amount']['value'], 1)

    def test_patch_unknown_plan_returns_404(self):
        r = self._patch(f'{PLANS}/2f1a4e4e-0000-4000-8000-000000000000', {'name': 'x'})
        self.assertEqual(r.status_code, 404)


@override_settings(**BASE_SETTINGS)
class TestPlanDelete(LifecycleMixin, TestCase):
    def test_delete_returns_204_with_no_body(self):
        pid = self.mkplan()
        r = self._delete(f'{PLANS}/{pid}')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.content, b'')

    def test_delete_removes_plan(self):
        pid = self.mkplan()
        self._delete(f'{PLANS}/{pid}')
        self.assertFalse(Plan.objects.filter(plan_id=pid).exists())

    def test_delete_orphans_active_subscriptions(self):
        """VULN [Business Logic]: plan deleted out from under a live subscription."""
        pid = self.mkplan()
        sid = self.mksub(pid)
        r = self._delete(f'{PLANS}/{pid}')
        self.assertEqual(r['X-Orphaned-Subscriptions'], '1')
        sub = Subscription.objects.get(subscription_id=sid)
        self.assertIsNone(sub.plan_id)
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)

    def test_orphaned_subscription_is_still_readable(self):
        pid = self.mkplan()
        sid = self.mksub(pid)
        self._delete(f'{PLANS}/{pid}')
        r = self._get(f'{SUBS}/{sid}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['subscription']['amount']['value'], 0)

    def test_delete_unknown_returns_404(self):
        r = self._delete(f'{PLANS}/2f1a4e4e-0000-4000-8000-000000000000')
        self.assertEqual(r.status_code, 404)


# ── Subscriptions ──────────────────────────────────────────────────────────────

@override_settings(**BASE_SETTINGS)
class TestSubscriptionCreate(LifecycleMixin, TestCase):
    def test_create_returns_201_and_location(self):
        pid = self.mkplan()
        r = self._post(SUBS, {'plan_id': pid, 'customer': {'email': 'a@b.c'}})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r['Location'],
                         f"{SUBS}/{r.json()['subscription']['subscription_id']}")

    def test_create_requires_plan_id(self):
        r = self._post(SUBS, {'customer': {'email': 'a@b.c'}})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['field'], 'plan_id')

    def test_create_unknown_plan_returns_404(self):
        r = self._post(SUBS, {'plan_id': '2f1a4e4e-0000-4000-8000-000000000000'})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()['error'], 'plan_not_found')

    def test_create_malformed_plan_id_returns_400(self):
        r = self._post(SUBS, {'plan_id': 'nope'})
        self.assertEqual(r.status_code, 400)

    def test_create_holds_card_as_zero_dollar_auth(self):
        """The subscription hangs off the existing PaymentTransaction state machine."""
        sid = self.mksub()
        sub = Subscription.objects.get(subscription_id=sid)
        txn = sub.payment_method_txn
        self.assertIsNotNone(txn)
        self.assertEqual(txn.operation, TransactionOperation.AUTH)
        self.assertEqual(txn.status, TransactionStatus.AUTHORIZED)
        self.assertEqual(txn.amount_value, 0)
        self.assertTrue(txn.auth_id.startswith('AUTH-'))

    def test_created_auth_is_reversible_via_existing_endpoint(self):
        """Chain: new endpoint produces an id the pre-existing /reversal consumes."""
        sid = self.mksub()
        aid = Subscription.objects.get(subscription_id=sid).payment_method_txn.auth_id
        r = self.client.post(f'/payments/api/payments/reversal/{aid}',
                             json.dumps({'reversal': {'reason': {'code': 'CANCEL'}}}),
                             content_type='application/json', **valid_headers())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['transaction']['status'], 'reversed')

    def test_create_without_card_has_no_holding_txn(self):
        sid = self.mksub(card=False)
        self.assertIsNone(
            Subscription.objects.get(subscription_id=sid).payment_method_txn)

    def test_trial_days_sets_trialing_status(self):
        pid = self.mkplan(trial_days=14)
        r = self._post(SUBS, {'plan_id': pid})
        self.assertEqual(r.json()['subscription']['status'], 'trialing')
        self.assertEqual(r.json()['billing']['trial_days_granted'], 14)

    def test_no_trial_sets_active_status(self):
        r = self._post(SUBS, {'plan_id': self.mkplan()})
        self.assertEqual(r.json()['subscription']['status'], 'active')

    def test_period_end_advances_by_plan_interval(self):
        pid = self.mkplan(interval='month', interval_count=1)
        s = self._post(SUBS, {'plan_id': pid}).json()['subscription']
        self.assertNotEqual(s['current_period_start'], s['current_period_end'])

    def test_interval_count_zero_yields_empty_period(self):
        """Edge: interval_count=0 makes period_end equal period_start."""
        pid = self.mkplan(interval='month', interval_count=0)
        s = self._post(SUBS, {'plan_id': pid}).json()['subscription']
        self.assertEqual(s['current_period_start'], s['current_period_end'])

    def test_negative_trial_days_ends_period_in_the_past(self):
        """Edge: a negative trial longer than the interval ends the period before it began."""
        pid = self.mkplan(trial_days=-90, interval='month', interval_count=1)
        s = self._post(SUBS, {'plan_id': pid}).json()['subscription']
        self.assertLess(s['current_period_end'], s['current_period_start'])

    def test_quantity_multiplies_amount(self):
        pid = self.mkplan(amount={'value': 1000})
        r = self._post(SUBS, {'plan_id': pid, 'quantity': 3})
        self.assertEqual(r.json()['subscription']['amount']['value'], 3000)

    def test_quantity_zero_yields_zero_amount(self):
        pid = self.mkplan(amount={'value': 1000})
        r = self._post(SUBS, {'plan_id': pid, 'quantity': 0})
        self.assertEqual(r.json()['subscription']['amount']['value'], 0)


@override_settings(**BASE_SETTINGS)
class TestSubscriptionRead(LifecycleMixin, TestCase):
    def test_get_returns_subscription(self):
        sid = self.mksub()
        r = self._get(f'{SUBS}/{sid}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['subscription']['subscription_id'], sid)

    def test_get_unknown_returns_404(self):
        r = self._get(f'{SUBS}/2f1a4e4e-0000-4000-8000-000000000000')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()['error'], 'subscription_not_found')

    def test_customer_pii_returned_unconditionally(self):
        """VULN [API3]: customer email/name on every read."""
        sid = self.mksub()
        cust = self._get(f'{SUBS}/{sid}').json()['subscription']['customer']
        self.assertEqual(cust['email'], 'a@example.com')

    def test_card_not_inlined_without_expand(self):
        sid = self.mksub()
        self.assertNotIn('payment_method', self._get(f'{SUBS}/{sid}').json()['subscription'])

    def test_expand_payment_method_leaks_pan_and_cvv(self):
        """VULN [API3]: ?expand=payment_method returns the stored PAN and CVV."""
        sid = self.mksub()
        r = self._get(f'{SUBS}/{sid}?expand=payment_method')
        card = r.json()['subscription']['payment_method']['card']
        self.assertEqual(card['card_number'], '4111111111111111')
        self.assertEqual(card['cvv'], '737')

    def test_expand_bypasses_tenant_scoping(self):
        """VULN [API1+API3]: another merchant expands the card on a foreign subscription."""
        sid = self.mksub(merchant='test_merch_001')
        r = self._get(f'{SUBS}/{sid}?expand=payment_method', merchant='test_merch_002')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json()['subscription']['payment_method']['card']['card_number'],
            '4111111111111111')

    def test_expand_plan_inlines_plan(self):
        sid = self.mksub()
        r = self._get(f'{SUBS}/{sid}?expand=plan')
        self.assertIn('plan', r.json()['subscription'])

    def test_list_is_cross_tenant(self):
        self.mksub(merchant='test_merch_001')
        self.mksub(merchant='test_merch_002')
        r = self._get(SUBS, merchant='test_merch_001')
        self.assertEqual(r.json()['page']['total'], 2)

    def test_list_filter_by_status(self):
        self.mksub()
        r = self._get(f'{SUBS}?status=canceled')
        self.assertEqual(r.json()['page']['total'], 0)

    def test_customer_email_lookup_is_unthrottled(self):
        """VULN [API6]: exact-match PII lookup with no rate limit."""
        self.mksub(merchant='test_merch_001')
        r = self._get(f'{SUBS}?customer_email=a@example.com', merchant='test_merch_002')
        self.assertEqual(r.json()['page']['total'], 1)

    def test_list_bad_plan_id_filter_returns_400(self):
        r = self._get(f'{SUBS}?plan_id=nope')
        self.assertEqual(r.status_code, 400)


@override_settings(**BASE_SETTINGS)
class TestSubscriptionUpdate(LifecycleMixin, TestCase):
    def test_patch_updates_quantity(self):
        sid = self.mksub()
        r = self._patch(f'{SUBS}/{sid}', {'quantity': 4})
        self.assertEqual(r.json()['subscription']['quantity'], 4)

    def test_patch_price_override_to_zero(self):
        """VULN [API3-BOPLA]: bill nothing while staying active."""
        pid = self.mkplan(amount={'value': 9999})
        sid = self.mksub(pid)
        r = self._patch(f'{SUBS}/{sid}', {'price_override': 0})
        self.assertEqual(r.json()['subscription']['amount']['value'], 0)

    def test_patch_price_override_negative(self):
        sid = self.mksub()
        r = self._patch(f'{SUBS}/{sid}', {'price_override': -10000})
        self.assertEqual(r.json()['subscription']['amount']['value'], -10000)

    def test_patch_status_past_due_to_active(self):
        """VULN [API3-BOPLA]: skip dunning by flipping status directly."""
        sid = self.mksub()
        self._patch(f'{SUBS}/{sid}', {'status': 'past_due'})
        r = self._patch(f'{SUBS}/{sid}', {'status': 'active'})
        self.assertEqual(r.json()['subscription']['status'], 'active')

    def test_patch_extends_period_end(self):
        """VULN [API3-BOPLA]: free extension of the paid period."""
        sid = self.mksub()
        r = self._patch(f'{SUBS}/{sid}',
                        {'current_period_end': '2099-01-01T00:00:00Z'})
        self.assertTrue(r.json()['subscription']['current_period_end'].startswith('2099'))

    def test_patch_mass_assigns_merchant_id(self):
        """VULN [API3-BOPLA]: tenant takeover of a subscription."""
        sid = self.mksub(merchant='test_merch_001')
        self._patch(f'{SUBS}/{sid}', {'merchant_id': 'test_merch_002'},
                    merchant='test_merch_002')
        self.assertEqual(
            Subscription.objects.get(subscription_id=sid).merchant_id, 'test_merch_002')

    def test_patch_repoints_to_another_merchants_plan(self):
        sid   = self.mksub(merchant='test_merch_001')
        other = self.mkplan(merchant='test_merch_002', amount={'value': 1})
        r = self._patch(f'{SUBS}/{sid}', {'plan_id': other})
        self.assertEqual(r.json()['subscription']['plan_id'], other)

    def test_patch_unknown_returns_404(self):
        r = self._patch(f'{SUBS}/2f1a4e4e-0000-4000-8000-000000000000', {'quantity': 1})
        self.assertEqual(r.status_code, 404)


@override_settings(**BASE_SETTINGS)
class TestSubscriptionCancel(LifecycleMixin, TestCase):
    def _cancel(self, sid, query='', merchant='test_merch_001'):
        return self.client.post(f'{SUBS}/{sid}/cancel{query}',
                                json.dumps({'reason': {'code': 'CUSTOMER_REQUEST'}}),
                                content_type='application/json',
                                **valid_headers(merchant_id=merchant))

    def test_cancel_returns_200_and_sets_canceled(self):
        sid = self.mksub()
        r = self._cancel(sid)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['subscription']['status'], 'canceled')

    def test_cancel_unknown_returns_404(self):
        r = self._cancel('2f1a4e4e-0000-4000-8000-000000000000')
        self.assertEqual(r.status_code, 404)

    def test_cancel_without_prorate_issues_no_credit(self):
        sid = self.mksub()
        self.assertNotIn('credit', self._cancel(sid).json())

    def test_cancel_at_period_end_keeps_subscription_active(self):
        sid = self.mksub()
        r = self._cancel(sid, '?at_period_end=true')
        self.assertEqual(r.json()['subscription']['status'], 'active')
        self.assertTrue(r.json()['subscription']['cancel_at_period_end'])

    def test_prorated_cancel_issues_credit_transaction(self):
        sid = self.mksub()
        r = self._cancel(sid, '?prorate=true')
        credit = r.json()['credit']
        txn = PaymentTransaction.objects.get(transaction_id=credit['transaction_id'])
        self.assertEqual(txn.operation, TransactionOperation.CREDIT)
        self.assertEqual(txn.status, TransactionStatus.CREDITED)

    def test_prorated_credit_ignores_price_override(self):
        """VULN [Business Logic]: proration uses the plan price, not what was billed."""
        pid = self.mkplan(amount={'value': 100000})
        sid = self.mksub(pid)
        self._patch(f'{SUBS}/{sid}', {'price_override': 1})
        credit = self._cancel(sid, '?prorate=true').json()['credit']
        self.assertGreater(credit['credited_amount']['value'], 1)

    def test_extended_period_inflates_prorated_credit(self):
        """VULN chain: PATCH current_period_end, then cancel with proration."""
        pid = self.mkplan(amount={'value': 10000})
        sid = self.mksub(pid)
        baseline = self._cancel(sid, '?prorate=true').json()['credit']['credited_amount']['value']

        sid2 = self.mksub(pid)
        self._patch(f'{SUBS}/{sid2}', {'current_period_end': '2099-01-01T00:00:00Z'})
        inflated = self._cancel(sid2, '?prorate=true').json()['credit']['credited_amount']['value']
        self.assertGreater(inflated, baseline * 100)

    def test_cancel_twice_issues_two_credits(self):
        """VULN [Business Logic]: no guard on an already-canceled subscription."""
        sid = self.mksub()
        first  = self._cancel(sid, '?prorate=true').json()['credit']['transaction_id']
        second = self._cancel(sid, '?prorate=true').json()['credit']['transaction_id']
        self.assertNotEqual(first, second)
        self.assertEqual(PaymentTransaction.objects.filter(
            operation=TransactionOperation.CREDIT).count(), 2)

    def test_cancel_of_ended_period_yields_negative_credit(self):
        """Edge: a period that already ended prorates to a negative credit."""
        pid = self.mkplan(amount={'value': 10000})
        sid = self.mksub(pid)
        self._patch(f'{SUBS}/{sid}', {'current_period_end': '2020-01-01T00:00:00Z'})
        credit = self._cancel(sid, '?prorate=true').json()['credit']
        self.assertLess(credit['credited_amount']['value'], 0)

    def test_cancel_by_other_merchant(self):
        """VULN [API5-BFLA]: any allowlisted merchant cancels a foreign subscription."""
        sid = self.mksub(merchant='test_merch_001')
        r = self._cancel(sid, merchant='test_merch_002')
        self.assertEqual(r.status_code, 200)

    def test_orphaned_subscription_cancel_does_not_500(self):
        """Edge: cancelling after its plan was deleted."""
        pid = self.mkplan()
        sid = self.mksub(pid)
        self._delete(f'{PLANS}/{pid}')
        r = self._cancel(sid, '?prorate=true')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['credit']['credited_amount']['value'], 0)


# ── Middleware coverage on the new routes ──────────────────────────────────────

@override_settings(**BASE_SETTINGS)
class TestLifecycleMiddlewareApplies(LifecycleMixin, TestCase):
    def test_missing_header_returns_400(self):
        h = valid_headers()
        del h['HTTP_X_REQUESTID']
        r = self.client.get(PLANS, **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'missing_header')

    def test_unlisted_merchant_returns_403(self):
        r = self._get(PLANS, merchant='not_allowed')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['error'], 'merchant_not_allowed')

    def test_duplicate_request_id_returns_409(self):
        h = valid_headers()
        self.client.get(PLANS, **h)
        r = self.client.get(PLANS, **h)
        self.assertEqual(r.status_code, 409)

    def test_legacy_api_key_bypasses_guards_on_new_routes(self):
        """VULN [API2]: the ?api_key bypass reaches the lifecycle endpoints too."""
        r = self.client.get(f'{PLANS}?api_key=legacy_pay_key_2019')
        self.assertEqual(r.status_code, 200)
