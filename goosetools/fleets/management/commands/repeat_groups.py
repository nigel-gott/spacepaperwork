from django.core.management.base import BaseCommand
from django.utils import timezone

from goosetools.fleets.models import FleetAnom
from goosetools.ownership.forms import LootGroupForm
from goosetools.ownership.models import LootGroup
from goosetools.ownership.views import loot_group_create_internal


class Command(BaseCommand):
    COMMAND_NAME = "repeat_groups"
    help = "Checks if any repeating groups need to be made"

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(self.style.SUCCESS(f"Running at {now}"))
        plus_5_minutes = now + timezone.timedelta(minutes=5)
        plus_5_minutes = plus_5_minutes.replace(second=0, microsecond=0)
        anoms = FleetAnom.objects.filter(
            minute_repeat_period__isnull=False, next_repeat__lt=plus_5_minutes
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Found {anoms.count()} anoms to repeat with a next repeat upto {plus_5_minutes}"
            )
        )
        for anom in anoms:
            lootgroup = anom.lootgroup_set.get()
            if lootgroup.closed:
                anom.minute_repeat_period = None
                anom.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Unsetting repeat on {anom} as it was manually closed"
                    )
                )
                continue
            new_rep_count = anom.repeat_count + 1
            timedelta = timezone.timedelta(minutes=anom.minute_repeat_period)
            next_repeat = anom.next_repeat + timedelta
            start = anom.next_repeat
            if next_repeat <= timezone.now():
                # Catchup Old groups
                next_repeat = timezone.now() + timedelta
                self.stdout.write(
                    self.style.SUCCESS(f"Catching up {anom} to {next_repeat}")
                )
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

            self.stdout.write(self.style.SUCCESS(f"Successfully repeated {new_group}"))

        minus_9_minutes = now - timezone.timedelta(minutes=9)
        old_groups = LootGroup.objects.filter(
            fleet_anom__minute_repeat_period__isnull=True,
            fleet_anom__next_repeat__lte=minus_9_minutes,
            closed=False,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Found {old_groups.count()} to be cleaned up who finished before {minus_9_minutes}."
            )
        )
        for old in old_groups:
            has_been_used = old.lootshare_set.exists() or old.inventoryitem_set.exists()
            if has_been_used:
                old.closed = True
                old.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Closing {old} as it has been used.")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Deleting {old} as it has not been used.")
                )
                old.delete()
