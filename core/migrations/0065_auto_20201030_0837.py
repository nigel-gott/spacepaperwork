# Generated by Django 3.1.2 on 2020-10-30 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0064_item_cached_lowest_sell"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="item",
            index=models.Index(
                fields=["-cached_lowest_sell"], name="core_item_cached__c12820_idx"
            ),
        ),
    ]
