# Generated by Django 3.1.4 on 2021-08-07 13:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_auto_20210508_1403"),
        ("pricing", "0011_auto_20210807_1259"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="PriceList",
            new_name="DataSet",
        ),
    ]