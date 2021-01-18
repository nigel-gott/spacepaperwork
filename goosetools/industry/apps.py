from django.apps import AppConfig
from django.db.models.signals import post_migrate


# pylint: disable=unused-argument
def populate_models(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from goosetools.industry.models import ShipOrder

    Group.objects.get_or_create(name="industry")
    Group.objects.get_or_create(name="industry_semi_admin")
    new_group, _ = Group.objects.get_or_create(name=u"industry")
    content_type = ContentType.objects.get_for_model(ShipOrder)
    change_ship_order, _ = Permission.objects.get_or_create(
        codename="change_shiporder", content_type=content_type
    )
    new_group.permissions.add(change_ship_order)


class IndustryConfig(AppConfig):
    name = "goosetools.industry"

    def ready(self):
        post_migrate.connect(populate_models, sender=self)
