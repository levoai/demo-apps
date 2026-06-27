import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('transaction_id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True)),
                ('auth_id',    models.CharField(blank=True, default='', max_length=32)),
                ('operation',  models.CharField(max_length=16, choices=[
                    ('auth', 'Authorize'),
                    ('sale', 'Sale'),
                    ('reversal', 'Reversal'),
                    ('capture', 'Capture'),
                    ('void-capture', 'Void Capture'),
                    ('refund', 'Refund'),
                    ('void-refund', 'Void Refund'),
                    ('credit', 'Credit'),
                ])),
                ('status',     models.CharField(max_length=32, choices=[
                    ('authorized', 'Authorized'),
                    ('settled', 'Settled'),
                    ('reversed', 'Reversed'),
                    ('captured', 'Captured'),
                    ('void_capture_complete', 'Void Capture Complete'),
                    ('refunded', 'Refunded'),
                    ('void_refund_complete', 'Void Refund Complete'),
                    ('credited', 'Credited'),
                ])),
                ('amount_value', models.BigIntegerField(default=0)),
                ('currency',    models.CharField(default='USD', max_length=3)),
                ('merchant_id', models.CharField(max_length=64)),
                ('request_id',  models.CharField(db_index=True, max_length=64)),
                ('original_transaction', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='derived', to='payments.paymenttransaction')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'payment_transaction', 'app_label': 'payments'},
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['auth_id'], name='pay_auth_id_idx')),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['merchant_id', 'created_at'], name='pay_merch_date_idx')),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(
                fields=['original_transaction', 'operation'], name='pay_orig_op_idx')),
    ]
