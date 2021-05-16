# Generated by Django 3.1.4 on 2021-05-02 07:38

import django.core.validators
from django.db import migrations, models

import goosetools.fleets.models


class Migration(migrations.Migration):
    dependencies = [
        ("fleets", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="fleetanom",
            name="minute_repeat_period",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MaxValueValidator(1000000),
                    goosetools.fleets.models.validate_nonzero,
                ],
            ),
        ),
        migrations.AddField(
            model_name="fleetanom",
            name="next_repeat",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]