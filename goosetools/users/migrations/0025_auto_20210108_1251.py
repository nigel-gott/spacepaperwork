# Generated by Django 3.1.4 on 2021-01-08 12:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0024_auto_20210108_1204"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="discorduser",
            name="old_notes",
        ),
        migrations.RemoveField(
            model_name="discorduser",
            name="sa_profile",
        ),
        migrations.RemoveField(
            model_name="discorduser",
            name="voucher",
        ),
    ]
