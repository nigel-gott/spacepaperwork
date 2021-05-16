# Generated by Django 3.1.4 on 2021-02-10 18:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnomType",
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
                ("level", models.PositiveIntegerField()),
                (
                    "type",
                    models.TextField(
                        choices=[
                            ("PvP Roam", "PvP Roam"),
                            ("PvP Gatecamp", "PvP Gatecamp"),
                            ("Deadspace", "Deadspace"),
                            ("Scout", "Scout"),
                            ("Inquisitor", "Inquisitor"),
                            ("Condensed Belt", "Condensed Belt"),
                            ("Condensed Cluster", "Condensed Cluster"),
                        ]
                    ),
                ),
                (
                    "faction",
                    models.TextField(
                        choices=[
                            ("Guristas", "Guritas"),
                            ("Angel", "Angel"),
                            ("Blood", "Blood"),
                            ("Sansha", "Sansha"),
                            ("Serpentis", "Serpentis"),
                            ("Asteroids", "Asteroids"),
                            ("PvP", "PvP"),
                        ]
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Fleet",
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
                    "loot_type",
                    models.TextField(
                        choices=[
                            ("Master Looter", "Master Looter"),
                            ("Free For All", "Free For All"),
                        ],
                        default="Master Looter",
                    ),
                ),
                ("gives_shares_to_alts", models.BooleanField(default=False)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField(blank=True, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("location", models.TextField(blank=True, null=True)),
                ("expected_duration", models.TextField(blank=True, null=True)),
                (
                    "fc",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.gooseuser",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="KillMail",
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
                ("killed_ship", models.TextField()),
                ("description", models.TextField()),
                (
                    "fleet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="fleets.fleet"
                    ),
                ),
                (
                    "looter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.character",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FleetAnom",
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
                (
                    "anom_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="fleets.anomtype",
                    ),
                ),
                (
                    "fleet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="fleets.fleet"
                    ),
                ),
                (
                    "system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.system"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FleetMember",
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
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("left_at", models.DateTimeField(blank=True, null=True)),
                ("admin_permissions", models.BooleanField(default=False)),
                (
                    "character",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.character",
                    ),
                ),
                (
                    "fleet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="fleets.fleet"
                    ),
                ),
            ],
            options={
                "unique_together": {("character", "fleet")},
            },
        ),
    ]
