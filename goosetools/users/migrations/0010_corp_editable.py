# Generated by Django 3.1.4 on 2021-02-16 21:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_discordguild_has_manage_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="corp",
            name="editable",
            field=models.BooleanField(default=True),
        ),
    ]
