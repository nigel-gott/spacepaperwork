# Generated by Django 3.1.2 on 2020-10-22 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_auto_20201022_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gooseuser',
            name='broker_fee',
            field=models.DecimalField(decimal_places=2, default=8.0, max_digits=5, verbose_name='Your Broker Fee in %'),
        ),
        migrations.AlterField(
            model_name='gooseuser',
            name='transaction_tax',
            field=models.DecimalField(decimal_places=2, default=15.0, max_digits=5, verbose_name='Your Transaction Tax in %'),
        ),
    ]
