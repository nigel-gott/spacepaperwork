from django.utils import timezone
from django_cron import CronJobBase, Schedule
from django_tenants.utils import tenant_context

from goosetools.industry.models import ShipOrder
from goosetools.tenants.models import Client
from goosetools.utils import cron_header_line


class CleanUpOldOrders(CronJobBase):
    RUN_EVERY_MINS = 24 * 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "industry.cleanup_old_orders"

    def do(self):
        cron_header_line(self.code)
        now = timezone.now()
        now_minus_98_hours = now - timezone.timedelta(hours=98)
        for tenant in Client.objects.all():
            if tenant.name != "public":
                with tenant_context(tenant):
                    stats = ShipOrder.objects.filter(
                        contract_made=False, created_at__lt=now_minus_98_hours
                    ).delete()
                    print(f"Deleted {stats} old contracts")
