# Generated by Django 3.1.4 on 2021-05-03 08:20

from django.db import migrations, models
import django.db.models.deletion

# noinspection PyPep8Naming
# pylint: disable=unused-argument
def populate_fk(apps, schema_editor):
    EchoesItem = apps.get_model("items", "EchoesItem")
    InventoryItem = apps.get_model("items", "InventoryItem")
    for i in InventoryItem.objects.all():
        new_item = EchoesItem.objects.get(name=i.item.name)
        i.item = new_item
        i.save()


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0003_auto_20210503_0802"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventoryitem",
            name="echoes_item",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="items.echoesitem",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_fk),
    ]
