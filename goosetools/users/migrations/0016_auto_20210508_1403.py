# Generated by Django 3.1.4 on 2021-05-08 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0015_auto_20210508_1055"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="permissibleentity",
            options={"ordering": ["order"]},
        ),
        migrations.AlterField(
            model_name="permissibleentity",
            name="order",
            field=models.IntegerField(default=0),
        ),
    ]
