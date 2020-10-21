# Generated by Django 3.1.2 on 2020-10-17 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20201016_2019'),
    ]

    operations = [
        migrations.AddField(
            model_name='system',
            name='jumps_to_jita',
            field=models.PositiveIntegerField(default=999),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='system',
            name='security',
            field=models.TextField(default='1.0'),
            preserve_default=False,
        ),
    ]