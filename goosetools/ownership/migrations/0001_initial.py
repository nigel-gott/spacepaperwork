# Generated by Django 3.1.2 on 2020-11-24 16:47

from django.db import migrations, models
import djmoney.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LootBucket",
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
            ],
        ),
        migrations.CreateModel(
            name="LootGroup",
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
                ("name", models.TextField(blank=True, null=True)),
                ("manual", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="LootShare",
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
                ("share_quantity", models.PositiveIntegerField(default=0)),
                ("flat_percent_cut", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="TransferLog",
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
                ("time", models.DateTimeField()),
                ("explaination", models.JSONField()),
                ("count", models.PositiveIntegerField()),
                (
                    "total_currency",
                    djmoney.models.fields.CurrencyField(
                        choices=[("EEI", "Eve Echoes ISK")],
                        default="EEI",
                        editable=False,
                        max_length=3,
                    ),
                ),
                (
                    "total",
                    djmoney.models.fields.MoneyField(
                        decimal_places=2, default_currency="EEI", max_digits=20
                    ),
                ),
                (
                    "own_share_currency",
                    djmoney.models.fields.CurrencyField(
                        choices=[("EEI", "Eve Echoes ISK")],
                        default="EEI",
                        editable=False,
                        max_length=3,
                    ),
                ),
                (
                    "own_share",
                    djmoney.models.fields.MoneyField(
                        blank=True,
                        decimal_places=2,
                        default_currency="EEI",
                        max_digits=20,
                        null=True,
                    ),
                ),
                ("deposit_command", models.TextField(default="")),
                ("transfer_command", models.TextField(default="")),
                ("own_share_in_eggs", models.BooleanField(default=True)),
                ("all_done", models.BooleanField(default=True)),
                ("legacy_transfer", models.BooleanField(default=True)),
            ],
        ),
    ]