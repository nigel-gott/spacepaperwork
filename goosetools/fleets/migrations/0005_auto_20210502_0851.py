# Generated by Django 3.1.4 on 2021-05-02 08:51

import django.core.validators
from django.db import migrations, models

import goosetools.fleets.models


class Migration(migrations.Migration):
    dependencies = [
        ("fleets", "0004_auto_20210502_0822"),
    ]

    operations = [
        migrations.AddField(
            model_name="fleetanom",
            name="repeat_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="fleetanom",
            name="minute_repeat_period",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MaxValueValidator(524160),
                    goosetools.fleets.models.validate_nonzero,
                ],
            ),
        ),
    ]
