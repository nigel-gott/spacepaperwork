# Generated by Django 3.1.4 on 2021-03-06 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("venmo", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="virtualcurrency",
            name="api_type",
            field=models.TextField(
                choices=[("space_venmo", "space_venmo")], default="space_venmo"
            ),
        ),
    ]
