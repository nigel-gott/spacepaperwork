# Generated by Django 3.1.2 on 2020-12-03 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("industry", "0008_auto_20201202_1102"),
    ]

    operations = [
        migrations.AddField(
            model_name="shiporder",
            name="blocked_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]