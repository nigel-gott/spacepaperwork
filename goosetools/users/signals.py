from django_tenants.utils import tenant_context

from goosetools.users.models import AuthConfig, Corp, DiscordRole, GoosePermission


def setup_tenant(tenant):
    with tenant_context(tenant):
        GoosePermission.ensure_populated()
        Corp.ensure_populated()
        AuthConfig.ensure_exists()
        DiscordRole.sync_from_discord()
