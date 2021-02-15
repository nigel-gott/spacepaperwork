# Generated by Django 3.1.4 on 2021-02-15 12:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ownership", "0002_auto_20210213_1704"),
        ("contracts", "0003_contract_logged_quantity"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="transfer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="ownership.transferlog",
            ),
        ),
    ]
