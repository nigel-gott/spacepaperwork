# Generated by Django 3.1.4 on 2021-02-04 10:10
from django.db import migrations, models
import django.db.models.deletion

from goosetools.users.models import Character, Corp


# pylint: disable=unused-argument
def revert_migration(apps, schema_editor):
    pass


# pylint: disable=unused-argument
def apply_migration(apps, schema_editor):
    for c in Character.objects.all():
        if not hasattr(c, "corp") or not c.corp:
            c.corp = Corp.unknown_corp()
            c.save()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0013_auto_20210204_0835"),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
        migrations.AlterField(
            model_name="character",
            name="corp",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="users.corp"
            ),
        ),
    ]
