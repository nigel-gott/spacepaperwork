# Generated by Django 3.1.4 on 2021-07-18 10:33

from django.db import migrations, models
import django.db.models.deletion
import goosetools.venmo.models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_auto_20210508_1403"),
        ("pricing", "0008_auto_20210715_1917"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pricelist",
            name="access_controller",
            field=models.ForeignKey(
                default=goosetools.venmo.models.create_access_controller,
                on_delete=django.db.models.deletion.CASCADE,
                to="users.crudaccesscontroller",
            ),
        ),
        migrations.AlterField(
            model_name="pricelist",
            name="default",
            field=models.BooleanField(default=False),
        ),
    ]
