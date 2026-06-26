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
