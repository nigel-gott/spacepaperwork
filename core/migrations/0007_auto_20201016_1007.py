# Generated by Django 3.1.2 on 2020-10-16 10:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_auto_20201016_1003"),
    ]

    operations = [
        migrations.RenameField(
            model_name="character",
            old_name="avatar_url",
            new_name="discord_avatar_url",
        ),
        migrations.RenameField(
            model_name="character",
            old_name="discord_name",
            new_name="discord_username",
        ),
    ]
