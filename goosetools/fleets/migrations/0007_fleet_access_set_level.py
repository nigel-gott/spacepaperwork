# Generated by Django 3.1.4 on 2021-05-08 09:58

from django.db import migrations


# noinspection PyPep8Naming
# pylint: disable=unused-argument
def create_initial_controller(apps, schema_editor):

    PermissibleEntity = apps.get_model("users", "PermissibleEntity")

    def calc_level(entity):
        if entity.user is not None:
            if entity.corp is None and entity.permission is None:
                # Just user
                level = 10
            elif entity.corp is None:
                # Permission and User
                level = 12
            elif entity.permission is None:
                # Corp and User
                level = 15
            else:
                # Corp and User and Permission
                level = 20
        elif entity.corp is not None:
            # User is none
            if entity.permission is None:
                # Just corp
                level = 5
            else:
                # Corp and Permission
                level = 7
        elif entity.permission is not None:
            # Just permission
            level = 3
        else:
            # No matcher set, matches everyone.
            level = 0

        if not entity.allow_or_deny:
            # A deny of the same level must override it.
            level = level + 1

        return level

    for e in PermissibleEntity.objects.all():
        e.order = calc_level(e)
        e.save()


class Migration(migrations.Migration):
    dependencies = [
        ("fleets", "0006_fleet_access_controller"),
    ]

    operations = [
        migrations.RunPython(create_initial_controller),
    ]
