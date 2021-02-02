# Generated by Django 3.1.4 on 2021-02-02 13:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_auto_20210201_1358"),
    ]

    operations = [
        migrations.CreateModel(
            name="GooseGroup",
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
                ("name", models.TextField(unique=True)),
                (
                    "linked_discord_role",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.discordrole",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GoosePermission",
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
                    "name",
                    models.TextField(
                        choices=[
                            (
                                "basic_access",
                                "Able to Apply to join and view the home page and other basic registered user pages",
                            ),
                            ("loot_tracker", "Able to use the loot tracker"),
                            (
                                "loot_tracker_admin",
                                "Automatically an admin in every fleet and able to do loot buyback",
                            ),
                            (
                                "user_admin",
                                "Able to approve user applications and manage users",
                            ),
                            (
                                "single_corp_admin",
                                "Able to approve corp applications for a specific corp",
                            ),
                            (
                                "all_corp_admin",
                                "Able to approve corp applications for all corps and manage characters in that corp",
                            ),
                            ("ship_orderer", "Able to place ship orders"),
                            ("free_ship_orderer", "Able to place free ship orders"),
                            (
                                "ship_order_admin",
                                "Able to claim and work on ship orders",
                            ),
                            (
                                "ship_order_price_admin",
                                "Able to add/remove ship types and set if they are free or not",
                            ),
                        ],
                        unique=True,
                    ),
                ),
                (
                    "corp",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.corp",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GroupMember",
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
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.goosegroup",
                    ),
                ),
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
            name="GroupPermission",
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
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.goosegroup",
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.goosepermission",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="userpermission",
            name="corp",
        ),
        migrations.RemoveField(
            model_name="userpermissiongroup",
            name="linked_discord_role",
        ),
        migrations.RemoveField(
            model_name="userpermissiongroupmapping",
            name="group",
        ),
        migrations.RemoveField(
            model_name="userpermissiongroupmapping",
            name="permission",
        ),
        migrations.DeleteModel(
            name="UserGroup",
        ),
        migrations.DeleteModel(
            name="UserPermission",
        ),
        migrations.DeleteModel(
            name="UserPermissionGroup",
        ),
        migrations.DeleteModel(
            name="UserPermissionGroupMapping",
        ),
    ]
