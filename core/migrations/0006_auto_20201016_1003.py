# Generated by Django 3.1.2 on 2020-10-16 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0005_auto_20201014_1704")]

    operations = [
        migrations.AddField(
            model_name="character",
            name="avatar_url",
            field=models.TextField(default="unknown"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="character",
            name="discord_name",
            field=models.TextField(default="unknown"),
            preserve_default=False,
        ),
    ]
