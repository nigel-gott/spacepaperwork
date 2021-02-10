# Generated by Django 3.1.4 on 2021-02-10 18:10

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import djmoney.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        ("fleets", "0001_initial"),
    ]

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
                (
                    "fleet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="fleets.fleet"
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
                ("closed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "bucket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ownership.lootbucket",
                    ),
                ),
                (
                    "fleet_anom",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="fleets.fleetanom",
                    ),
                ),
                (
                    "killmail",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="fleets.killmail",
                    ),
                ),
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
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.gooseuser",
                    ),
                ),
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
                (
                    "character",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.character",
                    ),
                ),
                (
                    "loot_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ownership.lootgroup",
                    ),
                ),
            ],
            options={
                "unique_together": {("character", "loot_group")},
            },
        ),
    ]
