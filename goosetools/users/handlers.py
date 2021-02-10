from django_tenants.utils import schema_context, tenant_context

from goosetools.users.models import AuthConfig, Corp, DiscordRole, GoosePermission


# pylint: disable=unused-argument
def handle_schema_migrated(sender, **kwargs):
    schema = kwargs["schema_name"]
    with schema_context(schema):
        if schema != "public":
            print("Setup for " + schema)
            setup()


def setup_tenant(tenant):
    with tenant_context(tenant):
        setup()


def setup():
    GoosePermission.ensure_populated()
    Corp.ensure_populated()
    AuthConfig.ensure_exists()
    DiscordRole.sync_from_discord()
