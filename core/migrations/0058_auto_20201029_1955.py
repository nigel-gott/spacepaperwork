# Generated by Django 3.1.2 on 2020-10-29 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_auto_20201029_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='character',
            name='verified',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
