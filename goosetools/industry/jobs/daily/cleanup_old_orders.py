from django.utils import timezone
from django_extensions.management.jobs import DailyJob

from goosetools.industry.models import ShipOrder


class Job(DailyJob):
    help = "Delete old invalid orders"

    def execute(self):
        now = timezone.now()
        now_minus_98_hours = now - timezone.timedelta(hours=98)
        stats = ShipOrder.objects.filter(
            contract_made=False, created_at__lt=now_minus_98_hours
        ).delete()
        print(f"Deleted {stats} old contracts")
