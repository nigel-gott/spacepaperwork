# Generated by Django 3.1.2 on 2020-11-20 10:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0080_loot_group_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="character",
            name="verified",
        ),
    ]
