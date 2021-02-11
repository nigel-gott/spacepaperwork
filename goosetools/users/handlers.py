from django.conf import settings
from django_tenants.utils import schema_context, tenant_context

from goosetools.users.models import (
    SUPERUSER_GROUP_NAME,
    AuthConfig,
    Character,
    Corp,
    DiscordRole,
    GooseGroup,
    GoosePermission,
    GooseUser,
)


# pylint: disable=unused-argument
def handle_schema_migrated(sender, **kwargs):
    schema = kwargs["schema_name"]
    with schema_context(schema):
        if schema != "public":
            setup()


def setup_tenant(tenant, request, signup_form):
    with tenant_context(tenant):
        setup()
        data = signup_form.cleaned_data
        gooseuser = GooseUser.objects.create(
            site_user=request.user,
            timezone=data["timezone"],
            broker_fee=data["broker_fee"],
            transaction_tax=data["transaction_tax"],
            status="approved",
        )
        superuser_group = GooseGroup.objects.get(name=SUPERUSER_GROUP_NAME)
        gooseuser.give_group(superuser_group)
        default_corp = Corp.objects.create(
            name="DEFAULT",
            full_name="Default Corp",
            description=f"Initial Corp created on Sign Up by {settings.SITE_NAME}",
            auto_approve=True,
            public_corp=True,
        )
        Character.objects.create(
            ingame_name=data["ingame_name"], corp=default_corp, user=gooseuser
        )


def setup():
    GoosePermission.ensure_populated()
    Corp.ensure_populated()
    AuthConfig.ensure_exists()
    DiscordRole.sync_from_discord()
