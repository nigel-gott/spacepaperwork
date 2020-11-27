from django.db import migrations


# pylint: disable=unused-argument
def apply_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    ShipOrder = apps.get_model("industry", "ShipOrder")
    new_group, _ = Group.objects.get_or_create(name=u"industry")
    content_type = ContentType.objects.get_for_model(ShipOrder)
    change_ship_order, _ = Permission.objects.get_or_create(
        codename="change_shiporder", content_type=content_type
    )
    new_group.permissions.add(change_ship_order)


# pylint: disable=unused-argument
def revert_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=[
            u"industry",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("industry", "0001_initial"),
    ]

    operations = [migrations.RunPython(apply_migration, revert_migration)]
