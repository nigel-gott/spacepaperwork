# Generated by Django 3.1.4 on 2021-01-18 13:38

from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("ownership", "__first__"),
        ("items", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SoldItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                (
                    "sold_via",
                    models.TextField(
                        choices=[
                            ("internal", "Internal Market"),
                            ("external", "External Market"),
                            ("contract", "Contract"),
                        ]
                    ),
                ),
                ("transfered", models.BooleanField(default=False)),
                ("transfered_quantity", models.PositiveIntegerField(default=0)),
                (
                    "item",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.inventoryitem",
                    ),
                ),
                (
                    "transfer_log",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="ownership.transferlog",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MarketOrder",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "internal_or_external",
                    models.TextField(
                        choices=[("internal", "Internal"), ("external", "External")]
                    ),
                ),
                (
                    "buy_or_sell",
                    models.TextField(choices=[("buy", "Buy"), ("sell", "Sell")]),
                ),
                ("quantity", models.PositiveIntegerField()),
                (
                    "listed_at_price_currency",
                    djmoney.models.fields.CurrencyField(
                        choices=[("EEI", "Eve Echoes ISK")],
                        default="EEI",
                        editable=False,
                        max_length=3,
                    ),
                ),
                (
                    "listed_at_price",
                    djmoney.models.fields.MoneyField(
                        decimal_places=2, default_currency="EEI", max_digits=20
                    ),
                ),
                (
                    "transaction_tax",
                    models.DecimalField(decimal_places=2, max_digits=5),
                ),
                ("broker_fee", models.DecimalField(decimal_places=2, max_digits=5)),
                (
                    "item",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.inventoryitem",
                    ),
                ),
            ],
        ),
    ]
