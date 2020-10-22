# Generated by Django 3.1.2 on 2020-10-22 08:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20201021_1243'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryitem',
            name='loot_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.lootgroup'),
        ),
        migrations.DeleteModel(
            name='LootGroupShare',
        ),
    ]
