# Generated by Django 3.1.2 on 2020-10-23 19:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0037_eggtransaction_debt"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="fleetmember",
            unique_together={("character", "fleet")},
        ),
    ]
