# Generated by Django 3.1.4 on 2021-02-10 18:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contract",
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
                ("created", models.DateTimeField()),
                (
                    "status",
                    models.TextField(
                        choices=[
                            ("pending", "pending"),
                            ("rejected", "rejected"),
                            ("accepted", "accepted"),
                            ("cancelled", "cancelled"),
                        ]
                    ),
                ),
                ("log", models.JSONField(blank=True, null=True)),
                (
                    "from_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="my_contracts",
                        to="users.gooseuser",
                    ),
                ),
                (
                    "system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.system"
                    ),
                ),
                (
                    "to_char",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.character",
                    ),
                ),
            ],
        ),
    ]
