from django.conf import settings
from django.core.management import call_command
from django_tenants.utils import schema_context, tenant_context
from requests.exceptions import HTTPError

from goosetools.users.models import (
    BASIC_ACCESS,
    LOOT_TRACKER,
    SHIP_ORDERER,
    SUPERUSER_GROUP_NAME,
    AuthConfig,
    Character,
    Corp,
    DiscordGuild,
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
        gooseuser.cache_fields_from_social_account()
        superuser_group = GooseGroup.objects.get(name=SUPERUSER_GROUP_NAME)
        gooseuser.give_group(superuser_group)
        default_user_group = GooseGroup.objects.create(
            name="Default User Group",
            description=f"Initial Group for Users created on Sign Up by {settings.SITE_NAME}",
            editable=True,
            manually_given=True,
        )
        default_user_group.link_permission(BASIC_ACCESS)
        default_user_group.link_permission(LOOT_TRACKER)
        default_user_group.link_permission(SHIP_ORDERER)
        default_corp = Corp.objects.create(
            name="DEFAULT",
            full_name="Default Corp",
            description=f"Initial Corp created on Sign Up by {settings.SITE_NAME}",
            auto_approve=True,
            public_corp=True,
            manual_group_given_on_approval=default_user_group,
        )
        Character.objects.create(
            ingame_name=data["ingame_name"], corp=default_corp, user=gooseuser
        )

        call_command(
            "tenant_command",
            "loaddata",
            "goosetools/core/fixtures/systems.json",
            "goosetools/items/fixtures/items.json",
            schema={tenant.schema_name},
        )


def setup():
    GoosePermission.ensure_populated()
    Corp.ensure_populated()
    AuthConfig.ensure_exists()
    try:
        DiscordRole.sync_from_discord()
    except HTTPError:
        pass
    g, _ = DiscordGuild.objects.get_or_create(active=True)
    g.check_valid()
