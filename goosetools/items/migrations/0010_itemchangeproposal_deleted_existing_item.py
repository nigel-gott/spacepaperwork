# Generated by Django 3.1.4 on 2021-05-03 13:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("items", "0009_auto_20210503_1201"),
    ]

    operations = [
        migrations.AddField(
            model_name="itemchangeproposal",
            name="deleted_existing_item",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
