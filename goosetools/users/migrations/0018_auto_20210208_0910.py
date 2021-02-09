# Generated by Django 3.1.4 on 2021-02-08 09:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0017_auto_20210208_0904"),
    ]

    operations = [
        migrations.AlterField(
            model_name="character",
            name="corp",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="users.corp"
            ),
        ),
        migrations.AlterField(
            model_name="corpapplication",
            name="corp",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="users.corp"
            ),
        ),
        migrations.AlterField(
            model_name="userapplication",
            name="corp",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="users.corp"
            ),
        ),
    ]