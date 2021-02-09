# Generated by Django 3.1.4 on 2021-02-08 11:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0018_auto_20210208_0910"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiscordRole",
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
                ("role_id", models.TextField(unique=True)),
            ],
        ),
        migrations.AddField(
            model_name="corp",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="corp",
            name="public_corp",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="corp",
            name="discord_role_given_on_approval",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="corps_giving_on_approval",
                to="users.discordrole",
            ),
        ),
        migrations.AddField(
            model_name="corp",
            name="discord_roles_allowing_application",
            field=models.ManyToManyField(
                related_name="corps_allowing_application", to="users.DiscordRole"
            ),
        ),
        migrations.AddField(
            model_name="goosegroup",
            name="required_discord_role",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="users.discordrole",
            ),
        ),
    ]
