# Generated by Django 3.1.2 on 2020-10-26 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0045_auto_20201026_2020")]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="log",
            field=models.JSONField(blank=True, null=True),
        )
    ]
