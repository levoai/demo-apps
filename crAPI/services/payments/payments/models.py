import uuid
from django.db import models


class TransactionOperation(models.TextChoices):
    AUTH         = 'auth',         'Authorize'
    SALE         = 'sale',         'Sale'
    REVERSAL     = 'reversal',     'Reversal'
    CAPTURE      = 'capture',      'Capture'
    VOID_CAPTURE = 'void-capture', 'Void Capture'
    REFUND       = 'refund',       'Refund'
    VOID_REFUND  = 'void-refund',  'Void Refund'
    CREDIT       = 'credit',       'Credit'


class TransactionStatus(models.TextChoices):
    AUTHORIZED        = 'authorized',            'Authorized'
    SETTLED           = 'settled',               'Settled'
    REVERSED          = 'reversed',              'Reversed'
    CAPTURED          = 'captured',              'Captured'
    VOID_CAPTURE_DONE = 'void_capture_complete', 'Void Capture Complete'
    REFUNDED          = 'refunded',              'Refunded'
    VOID_REFUND_DONE  = 'void_refund_complete',  'Void Refund Complete'
    CREDITED          = 'credited',              'Credited'


class PlanInterval(models.TextChoices):
    DAY   = 'day',   'Day'
    WEEK  = 'week',  'Week'
    MONTH = 'month', 'Month'
    YEAR  = 'year',  'Year'


class SubscriptionStatus(models.TextChoices):
    TRIALING   = 'trialing',   'Trialing'
    ACTIVE     = 'active',     'Active'
    PAST_DUE   = 'past_due',   'Past Due'
    PAUSED     = 'paused',     'Paused'
    CANCELED   = 'canceled',   'Canceled'
    INCOMPLETE = 'incomplete', 'Incomplete'


class PaymentTransaction(models.Model):
    transaction_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    auth_id        = models.CharField(max_length=32, blank=True, default='')
    operation      = models.CharField(
        max_length=16, choices=TransactionOperation.choices)
    status         = models.CharField(
        max_length=32, choices=TransactionStatus.choices)
    # Amount in minor units (cents) to avoid float precision issues
    amount_value   = models.BigIntegerField(default=0)
    currency       = models.CharField(max_length=3, default='USD')
    merchant_id    = models.CharField(max_length=64)
    request_id     = models.CharField(max_length=64, db_index=True)
    original_transaction = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='derived')
    created_at     = models.DateTimeField(auto_now_add=True)
    # VULNERABILITY [Sensitive Data Exposure]: card details stored in plaintext
    card_metadata  = models.CharField(max_length=512, blank=True, default='')

    class Meta:
        app_label = 'payments'
        db_table  = 'payment_transaction'
        indexes   = [
            models.Index(fields=['auth_id'],                           name='pay_auth_id_idx'),
            models.Index(fields=['merchant_id', 'created_at'],         name='pay_merch_date_idx'),
            models.Index(fields=['original_transaction', 'operation'], name='pay_orig_op_idx'),
        ]

    def __str__(self):
        return f'{self.operation}:{self.transaction_id} [{self.status}]'


class Plan(models.Model):
    """Recurring price point a Subscription is created against."""
    plan_id        = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    code           = models.CharField(max_length=64)
    name           = models.CharField(max_length=128)
    # Minor units (cents), as on PaymentTransaction
    amount_value   = models.BigIntegerField(default=0)
    currency       = models.CharField(max_length=3, default='USD')
    interval       = models.CharField(
        max_length=8, choices=PlanInterval.choices, default=PlanInterval.MONTH)
    interval_count = models.IntegerField(default=1)
    trial_days     = models.IntegerField(default=0)
    merchant_id    = models.CharField(max_length=64)
    active         = models.BooleanField(default=True)
    metadata       = models.CharField(max_length=512, blank=True, default='')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'payments'
        db_table  = 'payment_plan'
        indexes   = [
            models.Index(fields=['merchant_id', 'active'], name='pay_plan_merch_idx'),
            models.Index(fields=['code'],                  name='pay_plan_code_idx'),
        ]

    def __str__(self):
        return f'plan:{self.plan_id} [{self.code}]'


class Subscription(models.Model):
    """A customer's recurring commitment to a Plan."""
    subscription_id      = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    # SET_NULL: deleting a plan orphans its subscriptions rather than cascading
    plan                 = models.ForeignKey(
        Plan, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='subscriptions')
    merchant_id          = models.CharField(max_length=64)
    customer_email       = models.CharField(max_length=128, blank=True, default='')
    customer_name        = models.CharField(max_length=128, blank=True, default='')
    customer_ref         = models.CharField(max_length=64, blank=True, default='')
    status               = models.CharField(
        max_length=16, choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end   = models.DateTimeField(null=True, blank=True)
    price_override       = models.BigIntegerField(null=True, blank=True)
    quantity             = models.IntegerField(default=1)
    discount_code        = models.CharField(max_length=64, blank=True, default='')
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at          = models.DateTimeField(null=True, blank=True)
    # $0 auth holding the card this subscription bills against
    payment_method_txn   = models.ForeignKey(
        PaymentTransaction, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='subscriptions')
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'payments'
        db_table  = 'payment_subscription'
        indexes   = [
            models.Index(fields=['merchant_id', 'status'], name='pay_sub_merch_idx'),
            models.Index(fields=['customer_email'],        name='pay_sub_email_idx'),
            models.Index(fields=['plan', 'status'],        name='pay_sub_plan_idx'),
        ]

    def __str__(self):
        return f'subscription:{self.subscription_id} [{self.status}]'
