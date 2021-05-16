# Generated by Django 3.1.4 on 2021-02-12 16:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0009_discordguild_has_manage_roles"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
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
                ("type", models.TextField()),
                ("data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateField(auto_now_add=True)),
                ("priority", models.IntegerField(default=0)),
                (
                    "permission",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.goosepermission",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.gooseuser",
                    ),
                ),
            ],
        ),
    ]
