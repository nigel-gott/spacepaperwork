# Generated by Django 3.1.2 on 2020-11-15 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_transferlog_legacy_transfer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='isktransaction',
            name='transaction_type',
            field=models.TextField(choices=[('price_change_broker_fee', 'Price Change Broker Fee'), ('broker_fee', 'Broker Fee'), ('transaction_tax', 'Transaction Tax'), ('contract_broker_fee', 'Contract Broker Fee'), ('contract_transaction_tax', 'Contract Transaction Tax'), ('contract_gross_profit', 'Contract Gross Profit'), ('external_market_price_adjustment_fee', 'InGame Market Price Adjustment Fee'), ('external_market_gross_profit', 'InGame Market Gross Profit'), ('egg_deposit', 'Egg Deposit'), ('fractional_remains', 'Fractional Remains'), ('buyback', 'Buy Back')]),
        ),
    ]
