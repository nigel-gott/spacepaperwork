from django.utils import timezone
from django_cron import CronJobBase, Schedule
from django_tenants.utils import tenant_context

from goosetools.fleets.models import FleetAnom
from goosetools.ownership.forms import LootGroupForm
from goosetools.ownership.models import LootGroup
from goosetools.ownership.views import loot_group_create_internal
from goosetools.tenants.models import Client
from goosetools.utils import cron_header_line


def _run_for_tenant(now):
    plus_5_minutes = now + timezone.timedelta(minutes=5)
    plus_5_minutes = plus_5_minutes.replace(second=0, microsecond=0)
    anoms = FleetAnom.objects.filter(
        minute_repeat_period__isnull=False,
        next_repeat__lt=plus_5_minutes,
    )
    print(
        f"Found {anoms.count()} anoms to repeat with a next repeat upto {plus_5_minutes}"
    )
    for anom in anoms:
        lootgroup = anom.lootgroup_set.get()
        fleet_closed = lootgroup.fleet() and lootgroup.fleet().closed
        if lootgroup.closed or fleet_closed:
            anom.minute_repeat_period = None
            anom.save()
            print(f"Unsetting repeat on {anom} as it was manually closed")
            continue
        new_rep_count = anom.repeat_count + 1
        timedelta = timezone.timedelta(minutes=anom.minute_repeat_period)
        next_repeat = anom.next_repeat + timedelta
        start = anom.next_repeat
        if next_repeat <= timezone.now():
            # Catchup Old groups
            next_repeat = timezone.now() + timedelta
            print(f"Catching up {anom} to {next_repeat}")
        new_group = loot_group_create_internal(
            anom.fleet,
            LootGroupForm.ANOM_LOOT_GROUP,
            anom.anom_type.level,
            anom.anom_type.type,
            anom.anom_type.faction,
            lootgroup.bucket.pk,
            start,
            anom.system,
            lootgroup.name,
            anom.minute_repeat_period,
            next_repeat,
            new_rep_count,
        )
        anom.minute_repeat_period = None
        anom.save()

        print(f"Successfully repeated {new_group}")
    minus_9_minutes = now - timezone.timedelta(minutes=9)
    old_groups = LootGroup.objects.filter(
        fleet_anom__minute_repeat_period__isnull=True,
        fleet_anom__next_repeat__lte=minus_9_minutes,
        closed=False,
    )
    print(
        f"Found {old_groups.count()} to be cleaned up who finished before {minus_9_minutes}."
    )
    for old in old_groups:
        has_been_used = old.lootshare_set.exists() or old.inventoryitem_set.exists()
        if has_been_used:
            old.closed = True
            old.save()
            print(f"Closing {old} as it has been used.")
        else:
            print(f"Deleting {old} as it has not been used.")
            old.delete()


class RepeatGroups(CronJobBase):
    # We run the cron job every 5 minutes, if we set this to 5 minutes then django_cron
    # can skip 5 minute intervals. This way as 4 < 5 we are guaranteed that the job will
    # run every time we do runcrons.
    RUN_EVERY_MINS = 4

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "fleets.repeat_groups"

    def do(self):
        cron_header_line(self.code)
        now = timezone.now()
        for tenant in Client.objects.all():
            with tenant_context(tenant):
                if tenant.name != "public":
                    print(f"Repeating for tenant {tenant.name}")
                    _run_for_tenant(now)
