# Generated by Django 3.1.4 on 2021-05-01 12:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0010_corp_editable"),
        ("ownership", "0003_remove_lootbucket_fleet"),
    ]

    operations = [
        migrations.AddField(
            model_name="lootgroup",
            name="character",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="users.character",
            ),
        ),
    ]