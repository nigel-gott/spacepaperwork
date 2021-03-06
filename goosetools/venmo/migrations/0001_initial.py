# Generated by Django 3.1.4 on 2021-03-06 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0010_corp_editable"),
    ]

    operations = [
        migrations.CreateModel(
            name="VirtualCurrency",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.TextField(unique=True)),
                ("description", models.TextField(blank=True)),
                ("corps", models.ManyToManyField(to="users.Corp")),
            ],
        ),
    ]
