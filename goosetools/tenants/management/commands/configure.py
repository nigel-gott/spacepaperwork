from allauth.socialaccount.models import SocialAccount, SocialApp
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from goosetools.stub_discord_auth.views import get_current_stub_discord_uid
from goosetools.tenants.models import Client, Domain, SiteUser
from goosetools.users.handlers import setup_tenant


def _setup_simple_starting_tenant():
    with transaction.atomic():
        print("Setting up an initial local tenant.")
        if not Site.objects.exists():
            print("Setting up a django site @ 0.0.0.0")
            site = Site.objects.create(domain="0.0.0.0", name="localhost")
        else:
            site = Site.objects.first()
            print(f"Using first existing django site {site}")

        superusers = SiteUser.objects.filter(is_superuser=True)
        if not superusers.exists():
            print("Creating new superuser")
            site_user = SiteUser.objects.create(
                is_superuser=True,
                is_staff=True,
                date_joined=timezone.now(),
                username="test_user#1234",
            )
        else:
            site_user = superusers.first()
            print(f"Using existing first superuser {site_user}")

        if not SocialApp.objects.exists():
            print("Creating discord social app with fake bot config")
            app = SocialApp.objects.create(
                provider="discord",
                name="discord",
                client_id=123456,
                secret="test_fake_local_key",
                key="",
            )
        else:
            app = SocialApp.objects.first()
            print(f"Using existing social app {app}")

        if not site_user.socialaccount_set.exists():
            print(
                "Connecting superuser to stub discord social account to "
                "enable local login."
            )
            stub_discord_uid = get_current_stub_discord_uid()
            SocialAccount.objects.create(
                user=site_user,
                provider="discord",
                uid=stub_discord_uid,
                extra_data={
                    "id": stub_discord_uid,
                    "username": site_user.username,
                    "avatar": "",
                    "discriminator": "1234",
                },
            )

        app.sites.add(site)

        print("Creating initial spacepaperwork organization")
        tenant = Client.objects.create(
            name="spacepaperwork",
            schema_name="spacepaperwork",
            paid_until="3030-01-01",
            created_on="3030-01-01",
            on_trial=False,
        )
        Domain.objects.create(domain="0.0.0.0", is_primary=True, tenant=tenant)
        Domain.objects.create(domain="localhost", is_primary=False, tenant=tenant)
        Domain.objects.create(domain="127.0.0.1", is_primary=False, tenant=tenant)
        setup_tenant(
            tenant,
            site_user,
            {
                "timezone": "Europe/London",
                "broker_fee": 10,
                "transaction_tax": 5,
                "ingame_name": "Test Char",
            },
        )


def _setup_public_tenant():
    with transaction.atomic():
        print("Creating initial public tenant")
        tenant = Client.objects.create(
            name="public",
            schema_name="public",
            paid_until="3030-01-01",
            created_on="3030-01-01",
            on_trial=False,
        )
        Domain.objects.create(domain="0.0.0.0", is_primary=True, tenant=tenant)
        Domain.objects.create(domain="localhost", is_primary=False, tenant=tenant)
        Domain.objects.create(domain="127.0.0.1", is_primary=False, tenant=tenant)


class Command(BaseCommand):
    COMMAND_NAME = "configure"
    help = "Creates an initial tenant if in single tenant mode"

    def add_arguments(self, parser):
        parser.add_argument("--auto_first_time_local_setup", action="store_true")

    def handle(self, *args, **options):
        if options["auto_first_time_local_setup"]:
            if not Client.objects.exists() and settings.SINGLE_TENANT:
                _setup_public_tenant()
            else:
                print(
                    "Tenant already setup or not in single tenant mode so "
                    "skipping auto setup."
                )
        else:
            pass
