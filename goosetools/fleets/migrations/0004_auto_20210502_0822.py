# Generated by Django 3.1.4 on 2021-05-02 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fleets", "0003_auto_20210502_0808"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fleetanom",
            name="next_repeat",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
