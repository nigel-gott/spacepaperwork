from django.db import migrations


# pylint: disable=unused-argument
def apply_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    GooseUser = apps.get_model("users", "GooseUser")
    Character = apps.get_model("users", "Character")

    new_group, _ = Group.objects.get_or_create(name=u"user_admin")
    content_type = ContentType.objects.get_for_model(GooseUser)
    change_ship_order, _ = Permission.objects.get_or_create(
        codename="change_gooseuser", content_type=content_type
    )
    new_group.permissions.add(change_ship_order)

    content_type = ContentType.objects.get_for_model(Character)
    change_ship_order, _ = Permission.objects.get_or_create(
        codename="change_character", content_type=content_type
    )
    new_group.permissions.add(change_ship_order)


# pylint: disable=unused-argument
def revert_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=[
            u"user_admin",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_auto_20201201_1442"),
    ]

    operations = [migrations.RunPython(apply_migration, revert_migration)]
