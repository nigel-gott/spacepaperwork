# Generated by Django 3.1.2 on 2020-10-14 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0002_fleettype_material_icon")]

    operations = [
        migrations.AddField(
            model_name="fleettype",
            name="material_colour",
            field=models.TextField(default="lime lighten-3"),
            preserve_default=False,
        )
    ]
