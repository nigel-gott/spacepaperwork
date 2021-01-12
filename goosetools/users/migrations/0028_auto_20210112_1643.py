# Generated by Django 3.1.4 on 2021-01-12 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0027_set_gooseuser_username_to_discord"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gooseuser",
            name="username",
            field=models.CharField(
                error_messages={"unique": "A user with that username already exists."},
                max_length=150,
                unique=True,
            ),
        ),
    ]
