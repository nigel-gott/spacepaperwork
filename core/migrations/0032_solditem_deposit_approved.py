# Generated by Django 3.1.2 on 2020-10-22 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_eggdeposit'),
    ]

    operations = [
        migrations.AddField(
            model_name='solditem',
            name='deposit_approved',
            field=models.BooleanField(default=False),
        ),
    ]
