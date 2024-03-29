# Generated by Django 3.1.4 on 2021-02-10 18:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contracts", "__first__"),
        ("users", "__first__"),
        ("ownership", "__first__"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CharacterLocation",
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
                    "character",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.character",
                    ),
                ),
                (
                    "system",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.system",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CorpHanger",
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
                    "hanger",
                    models.CharField(
                        choices=[
                            ("1", "Hanger 1"),
                            ("2", "Hanger 2"),
                            ("3", "Hanger 3"),
                            ("4", "Hanger 4"),
                        ],
                        max_length=1,
                    ),
                ),
                (
                    "corp",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="users.corp"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InventoryItem",
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
                ("created_at", models.DateTimeField()),
                (
                    "contract",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contracts.contract",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ItemType",
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
            ],
        ),
        migrations.CreateModel(
            name="StackedInventoryItem",
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
                ("created_at", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="Station",
            fields=[
                ("name", models.TextField(primary_key=True, serialize=False)),
                (
                    "system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.system"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="JunkedItem",
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
                ("reason", models.TextField()),
                (
                    "item",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.inventoryitem",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ItemSubType",
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
                    "item_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="items.itemtype"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ItemSubSubType",
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
                    "item_sub_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.itemsubtype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ItemLocation",
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
                    "character_location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.characterlocation",
                    ),
                ),
                (
                    "corp_hanger",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.corphanger",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                ("name", models.TextField(primary_key=True, serialize=False)),
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
        migrations.AddField(
            model_name="inventoryitem",
            name="item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="items.item"
            ),
        ),
        migrations.AddField(
            model_name="inventoryitem",
            name="location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="items.itemlocation"
            ),
        ),
        migrations.AddField(
            model_name="inventoryitem",
            name="loot_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="ownership.lootgroup",
            ),
        ),
        migrations.AddField(
            model_name="inventoryitem",
            name="stack",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="items.stackedinventoryitem",
            ),
        ),
        migrations.AddField(
            model_name="corphanger",
            name="station",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="items.station"
            ),
        ),
        migrations.AddIndex(
            model_name="item",
            index=models.Index(
                fields=["-cached_lowest_sell"], name="items_item_cached__72dc0a_idx"
            ),
        ),
    ]
