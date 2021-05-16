# Generated by Django 3.1.4 on 2021-05-03 08:02

import django.db.models.deletion
from django.db import migrations, models


# noinspection PyPep8Naming
# pylint: disable=unused-argument
def populate_new_items_table(apps, schema_editor):
    EchoesItem = apps.get_model("items", "EchoesItem")
    Item = apps.get_model("items", "Item")
    for i in Item.objects.all():
        ei = EchoesItem(
            item_type=i.item_type,
            name=i.name,
            eve_echoes_market_id=i.eve_echoes_market_id,
            cached_lowest_sell=i.cached_lowest_sell,
        )
        ei.full_clean()
        ei.save()


class Migration(migrations.Migration):
    dependencies = [
        ("items", "0002_auto_20210301_1844"),
    ]

    operations = [
        migrations.CreateModel(
            name="EchoesItem",
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
                ("name", models.TextField()),
                (
                    "eve_echoes_market_id",
                    models.TextField(blank=True, null=True, unique=True),
                ),
                (
                    "cached_lowest_sell",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=20, null=True
                    ),
                ),
                (
                    "item_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.itemsubsubtype",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="echoesitem",
            index=models.Index(
                fields=["-cached_lowest_sell"], name="items_echoe_cached__932ffa_idx"
            ),
        ),
        migrations.RunPython(populate_new_items_table),
    ]