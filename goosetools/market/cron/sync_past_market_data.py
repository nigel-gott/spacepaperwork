from django.core.management import call_command
from django_cron import CronJobBase, Schedule

from goosetools.utils import cron_header_line


class SyncPastMarketData(CronJobBase):
    RUN_EVERY_MINS = 7 * 60 * 24

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "market.sync_past_market_data"

    def do(self):
        cron_header_line(self.code)
        call_command("sync_past_market_data", "--lookback_days=8")
