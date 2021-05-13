# Generated by Django 3.1.4 on 2021-05-08 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_auto_20210508_0956"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="permissibleentity",
            index=models.Index(
                fields=["user", "corp", "permission"],
                name="users_permi_user_id_361dea_idx",
            ),
        ),
    ]
