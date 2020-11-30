# Generated by Django 3.1.2 on 2020-11-24 16:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("ownership", "0001_initial"),
        ("items", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventoryitem",
            name="loot_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="ownership.lootgroup",
            ),
        ),
        migrations.AddField(
            model_name="inventoryitem",
            name="stack",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="items.stackedinventoryitem",
            ),
        ),
    ]