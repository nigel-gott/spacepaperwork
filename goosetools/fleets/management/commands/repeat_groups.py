from django.core.management.base import BaseCommand
from django.utils import timezone

from goosetools.fleets.models import FleetAnom
from goosetools.ownership.forms import LootGroupForm
from goosetools.ownership.views import loot_group_create_internal


class Command(BaseCommand):
    COMMAND_NAME = "repeat_groups"
    help = "Checks if any repeating groups need to be made"

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(self.style.SUCCESS(f"Running at {now}"))
        anoms = FleetAnom.objects.filter(
            minute_repeat_period__isnull=False, next_repeat__lte=now
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
            now = timezone.now()
            new_rep_count = anom.repeat_count + 1
            next_repeat = now + timezone.timedelta(minutes=anom.minute_repeat_period)
            new_group = loot_group_create_internal(
                anom.fleet,
                LootGroupForm.ANOM_LOOT_GROUP,
                anom.anom_type.level,
                anom.anom_type.type,
                anom.anom_type.faction,
                lootgroup.bucket.pk,
                anom.next_repeat,
                anom.system,
                lootgroup.name,
                anom.minute_repeat_period,
                next_repeat,
                new_rep_count,
            )
            has_been_used = (
                lootgroup.lootshare_set.exists() or lootgroup.inventoryitem_set.exists()
            )
            if has_been_used:
                anom.minute_repeat_period = None
                anom.save()
                lootgroup.closed = True
                lootgroup.save()
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Deleting old group {anom.lootgroup_set.get().display_name()} as it has not been used."
                    )
                )
                anom.delete()

            self.stdout.write(self.style.SUCCESS(f"Successfully repeated {new_group}"))
