# Generated by Django 3.1.2 on 2020-12-10 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_auto_20201210_1205"),
    ]

    operations = [
        migrations.AddField(
            model_name="corp",
            name="required_discord_role",
            field=models.TextField(blank=True, null=True),
        ),
    ]