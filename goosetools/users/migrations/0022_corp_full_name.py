# Generated by Django 3.1.2 on 2020-12-12 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0021_auto_20201212_1657"),
    ]

    operations = [
        migrations.AddField(
            model_name="corp",
            name="full_name",
            field=models.TextField(blank=True, null=True, unique=True),
        ),
    ]
