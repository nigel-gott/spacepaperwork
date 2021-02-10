from django.dispatch import receiver
from django_tenants.models import TenantMixin
from django_tenants.signals import post_schema_sync
from django_tenants.utils import tenant_context


@receiver(post_schema_sync, sender=TenantMixin)
# pylint: disable=unused-argument
def created_user_client(sender, **kwargs):
    from goosetools.users.models import AuthConfig, Corp, DiscordRole, GoosePermission

    tenant = kwargs["tenant"]
    with tenant_context(tenant):
        GoosePermission.ensure_populated()
        Corp.ensure_populated()
        AuthConfig.ensure_exists()
        DiscordRole.sync_from_discord()
