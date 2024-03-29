from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from goosetools.tenants.models import Client, Domain, SiteUser
from goosetools.users.handlers import setup_tenant


class Command(BaseCommand):
    COMMAND_NAME = "setup_tenants"
    help = "Creates an initial tenant if in single tenant mode"

    def add_arguments(self, parser):
        parser.add_argument("--extra_domains", type=str, action="store")

    def handle(self, *args, **options):
        if not Client.objects.exists() and settings.SINGLE_TENANT:
            with transaction.atomic():
                tenant = Client.objects.create(
                    name="spacepaperwork",
                    schema_name="spacepaperwork",
                    paid_until="3030-01-01",
                    created_on="3030-01-01",
                    on_trial=False,
                )
                d = Domain(domain="localhost", is_primary=True, tenant=tenant)
                d.save()
                for domain in options.get("extra_domains", "").split(","):
                    d = Domain(domain=domain, is_primary=False, tenant=tenant)
                    d.save()
                setup_tenant(
                    tenant,
                    SiteUser.objects.first(),
                    {
                        "timezone": "Europe/London",
                        "broker_fee": 10,
                        "transaction_tax": 5,
                        "ingame_name": "Test Char",
                    },
                )
