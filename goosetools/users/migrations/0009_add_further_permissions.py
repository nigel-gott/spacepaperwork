from django.db import migrations


# pylint: disable=unused-argument
def apply_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    GooseUser = apps.get_model("users", "GooseUser")

    new_group, _ = Group.objects.get_or_create(name=u"user_admin")
    content_type = ContentType.objects.get_for_model(GooseUser)
    change_ship_order, _ = Permission.objects.get_or_create(
        codename="change_userapplication", content_type=content_type
    )
    new_group.permissions.add(change_ship_order)


# pylint: disable=unused-argument
def revert_migration(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Permission.objects.filter(
        codename__in=[
            u"change_userapplication",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0008_userapplication"),
    ]

    operations = [migrations.RunPython(apply_migration, revert_migration)]
