# Generated by Django 3.1.4 on 2021-02-09 16:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0023_auto_20210209_1244"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="authconfig",
            name="connected_discord_server_id",
        ),
        migrations.RemoveField(
            model_name="authconfig",
            name="new_user_discord_role",
        ),
        migrations.RemoveField(
            model_name="authconfig",
            name="sign_up_introduction",
        ),
        migrations.RemoveField(
            model_name="authconfig",
            name="signup_required",
        ),
        migrations.RemoveField(
            model_name="discordguild",
            name="bot_token",
        ),
        migrations.RemoveField(
            model_name="discordguild",
            name="member_role_id",
        ),
    ]