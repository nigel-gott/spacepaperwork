# Generated by Django 3.1.2 on 2020-10-30 07:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0059_item_eve_echoes_market_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="ItemMarketDataEvent",
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
                ("sell", models.DecimalField(decimal_places=2, max_digits=14)),
                ("buy", models.DecimalField(decimal_places=2, max_digits=14)),
                ("highest_sell", models.DecimalField(decimal_places=2, max_digits=14)),
                ("lowest_buy", models.DecimalField(decimal_places=2, max_digits=14)),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.item"
                    ),
                ),
            ],
        ),
    ]
