# Generated by Django 3.1.4 on 2021-01-14 15:31

from django.db import migrations
from goosetools.tenants.models import SiteUser


# pylint: disable=unused-argument
def apply_migration(apps, schema_editor):
    GooseUser = apps.get_model("users", "GooseUser")
    for user in GooseUser.objects.filter().all():
        SiteUser.copy_from_user(user)


# pylint: disable=unused-argument
def revert_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenants", "0002_setup_fks"),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
    ]
