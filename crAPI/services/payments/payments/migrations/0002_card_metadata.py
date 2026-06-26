from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('payments', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='paymenttransaction',
            name='card_metadata',
            field=models.CharField(blank=True, default='', max_length=512),
        ),
    ]
