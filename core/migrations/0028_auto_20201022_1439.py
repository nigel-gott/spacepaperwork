# Generated by Django 3.1.2 on 2020-10-22 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20201022_0806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='isktransaction',
            name='notes',
            field=models.TextField(default=''),
        ),
    ]