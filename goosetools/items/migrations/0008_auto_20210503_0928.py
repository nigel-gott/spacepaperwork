# Generated by Django 3.1.4 on 2021-05-03 09:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("items", "0007_auto_20210503_0901"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="item",
            name="volume",
        ),
        migrations.CreateModel(
            name="ItemChangeProposal",
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
                    "change",
                    models.TextField(
                        choices=[
                            ("update", "update"),
                            ("delete", "delete"),
                            ("new", "new"),
                        ]
                    ),
                ),
                ("name", models.TextField(blank=True, null=True)),
                ("eve_echoes_market_id", models.TextField(blank=True, null=True)),
                (
                    "volume",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=20, null=True
                    ),
                ),
                (
                    "existing_item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="items.item",
                    ),
                ),
            ],
        ),
    ]
