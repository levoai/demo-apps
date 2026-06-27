"""Model-level tests for PaymentTransaction."""
import os
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
os.environ.setdefault('PAYMENTS_ALLOWED_MERCHANT_IDS', 'test_merch_001')

from django.test import TestCase
from payments.models import PaymentTransaction, TransactionOperation, TransactionStatus


class TestPaymentTransactionModel(TestCase):

    def _make(self, operation=TransactionOperation.AUTH,
              status=TransactionStatus.AUTHORIZED,
              amount=10000, currency='USD',
              merchant_id='test_merch_001',
              request_id=None, auth_id='AUTH-0001'):
        return PaymentTransaction.objects.create(
            operation=operation, status=status,
            amount_value=amount, currency=currency,
            merchant_id=merchant_id,
            request_id=request_id or f'RID-{uuid.uuid4().hex[:16]}',
            auth_id=auth_id,
        )

    def test_uuid_primary_key_generated(self):
        txn = self._make()
        self.assertIsNotNone(txn.transaction_id)
        self.assertIsInstance(txn.transaction_id, uuid.UUID)

    def test_default_currency_is_usd(self):
        txn = PaymentTransaction.objects.create(
            operation=TransactionOperation.CREDIT,
            status=TransactionStatus.CREDITED,
            amount_value=500,
            merchant_id='test_merch_001',
            request_id='RID-001',
        )
        self.assertEqual(txn.currency, 'USD')

    def test_str_representation(self):
        txn = self._make()
        s = str(txn)
        self.assertIn('auth', s)
        self.assertIn('authorized', s)

    def test_foreign_key_self_reference(self):
        auth_txn = self._make()
        cap_txn = PaymentTransaction.objects.create(
            operation=TransactionOperation.CAPTURE,
            status=TransactionStatus.CAPTURED,
            amount_value=10000, currency='USD',
            merchant_id='test_merch_001',
            request_id=f'RID-{uuid.uuid4().hex[:16]}',
            auth_id=auth_txn.auth_id,
            original_transaction=auth_txn,
        )
        self.assertEqual(cap_txn.original_transaction_id, auth_txn.transaction_id)

    def test_derived_reverse_relation(self):
        auth_txn = self._make()
        cap_txn = PaymentTransaction.objects.create(
            operation=TransactionOperation.CAPTURE,
            status=TransactionStatus.CAPTURED,
            amount_value=10000, currency='USD',
            merchant_id='test_merch_001',
            request_id=f'RID-{uuid.uuid4().hex[:16]}',
            original_transaction=auth_txn,
        )
        self.assertEqual(auth_txn.derived.count(), 1)
        self.assertEqual(auth_txn.derived.first().transaction_id, cap_txn.transaction_id)

    def test_all_operations_valid(self):
        for op, status in [
            (TransactionOperation.AUTH,         TransactionStatus.AUTHORIZED),
            (TransactionOperation.SALE,         TransactionStatus.SETTLED),
            (TransactionOperation.REVERSAL,     TransactionStatus.REVERSED),
            (TransactionOperation.CAPTURE,      TransactionStatus.CAPTURED),
            (TransactionOperation.VOID_CAPTURE, TransactionStatus.VOID_CAPTURE_DONE),
            (TransactionOperation.REFUND,       TransactionStatus.REFUNDED),
            (TransactionOperation.VOID_REFUND,  TransactionStatus.VOID_REFUND_DONE),
            (TransactionOperation.CREDIT,       TransactionStatus.CREDITED),
        ]:
            txn = PaymentTransaction.objects.create(
                operation=op, status=status,
                amount_value=1000, currency='USD',
                merchant_id='test_merch_001',
                request_id=f'RID-{uuid.uuid4().hex[:16]}',
            )
            txn.refresh_from_db()
            self.assertEqual(txn.operation, op)
            self.assertEqual(txn.status, status)

    def test_amount_stored_in_minor_units(self):
        txn = self._make(amount=9999)
        txn.refresh_from_db()
        self.assertEqual(txn.amount_value, 9999)

    def test_auth_id_index_lookup(self):
        txn = self._make(auth_id='AUTH-7777')
        found = PaymentTransaction.objects.get(auth_id='AUTH-7777')
        self.assertEqual(found.transaction_id, txn.transaction_id)
