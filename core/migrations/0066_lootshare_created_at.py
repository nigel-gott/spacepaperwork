# Generated by Django 3.1.2 on 2020-11-04 07:46

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0065_auto_20201030_0837")]

    operations = [
        migrations.AddField(
            model_name="lootshare",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        )
    ]
