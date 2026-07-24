"""Seed plans and subscriptions across every allowlisted merchant, so cross-tenant
reads are observable on a fresh boot. Idempotent on (merchant_id, code)."""
import json
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from payments.models import (
    PaymentTransaction, TransactionOperation, TransactionStatus,
    Plan, PlanInterval, Subscription, SubscriptionStatus,
)

PLAN_TEMPLATES = [
    ('STARTER-MONTHLY',  'Starter Monthly',  999,   PlanInterval.MONTH, 1, 14),
    ('PRO-MONTHLY',      'Pro Monthly',      4999,  PlanInterval.MONTH, 1, 0),
    ('PRO-ANNUAL',       'Pro Annual',       49900, PlanInterval.YEAR,  1, 30),
    ('ENTERPRISE-QTR',   'Enterprise Quarterly', 249900, PlanInterval.MONTH, 3, 0),
]

CUSTOMERS = [
    ('ada.lovelace@example.com',   'Ada Lovelace'),
    ('grace.hopper@example.com',   'Grace Hopper'),
    ('alan.turing@example.com',    'Alan Turing'),
    ('katherine.j@example.com',    'Katherine Johnson'),
    ('margaret.h@example.com',     'Margaret Hamilton'),
]

CARDS = [
    ('4111111111111111', '411111', '1111', '12/27', '737'),
    ('5555555555554444', '555555', '4444', '04/28', '112'),
    ('378282246310005',  '378282', '0005', '09/29', '9997'),
]

STATUSES = [SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING, SubscriptionStatus.PAST_DUE]


class Command(BaseCommand):
    help = 'Seed lifecycle plans and subscriptions for every allowlisted merchant'

    def add_arguments(self, parser):
        parser.add_argument('--subs-per-plan', type=int, default=2,
                            help='subscriptions to create per plan (default 2)')
        parser.add_argument('--seed', type=int, default=20260724,
                            help='RNG seed, so runs are reproducible')

    def handle(self, *args, **opts):
        random.seed(opts['seed'])
        merchants = [m.strip() for m in
                     getattr(settings, 'PAYMENTS_ALLOWED_MERCHANT_IDS', '').split(',')
                     if m.strip()]
        if not merchants:
            self.stderr.write('PAYMENTS_ALLOWED_MERCHANT_IDS is empty — nothing to seed')
            return

        plans_made = subs_made = 0
        for merchant in merchants:
            for code, name, amount, interval, count, trial in PLAN_TEMPLATES:
                plan, created = Plan.objects.get_or_create(
                    merchant_id=merchant, code=code,
                    defaults={
                        'name':           name,
                        'amount_value':   amount,
                        'currency':       'USD',
                        'interval':       interval,
                        'interval_count': count,
                        'trial_days':     trial,
                        'active':         True,
                        'metadata':       json.dumps({'seeded': True, 'tier': code}),
                    })
                if created:
                    plans_made += 1
                subs_made += self._seed_subs(plan, merchant, opts['subs_per_plan'])

        self.stdout.write(
            f'[payments] seeded {plans_made} plan(s) and {subs_made} subscription(s) '
            f'across {len(merchants)} merchant(s)')

    def _seed_subs(self, plan, merchant, count):
        existing = Subscription.objects.filter(plan=plan).count()
        made = 0
        for i in range(max(0, count - existing)):
            email, cname = random.choice(CUSTOMERS)
            pan, bin_, last4, expiry, cvv = random.choice(CARDS)
            now = timezone.now()

            # $0 auth holds the card, matching POST /subscriptions
            pm = PaymentTransaction.objects.create(
                operation=TransactionOperation.AUTH,
                status=TransactionStatus.AUTHORIZED,
                amount_value=0, currency=plan.currency,
                auth_id=f'AUTH-{random.randint(0, 10**12 - 1):012d}',
                merchant_id=merchant,
                request_id=f'seed-{plan.code}-{i}',
                card_metadata=json.dumps({
                    'card_number': pan, 'bin': bin_, 'last4': last4,
                    'expiry': expiry, 'cvv': cvv, 'holder_name': cname,
                }),
            )
            start = now - timedelta(days=random.randint(1, 25))
            Subscription.objects.create(
                plan=plan, merchant_id=merchant,
                customer_email=email, customer_name=cname,
                customer_ref=f'CUST-{random.randint(10000, 99999)}',
                status=random.choice(STATUSES),
                current_period_start=start,
                current_period_end=start + timedelta(days=30),
                quantity=random.choice([1, 1, 2, 5]),
                payment_method_txn=pm,
            )
            made += 1
        return made
