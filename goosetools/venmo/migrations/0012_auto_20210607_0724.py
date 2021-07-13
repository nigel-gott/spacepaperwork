# Generated by Django 3.1.4 on 2021-06-07 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("venmo", "0011_auto_20210516_1217"),
    ]

    operations = [
        migrations.AlterField(
            model_name="virtualcurrency",
            name="api_type",
            field=models.TextField(
                choices=[("space_venmo", "space_venmo"), ("fog_venmo", "Fog Venmo")],
                default="space_venmo",
            ),
        ),
    ]