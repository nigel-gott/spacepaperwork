import csv
from decimal import Decimal

import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django_cron import CronJobBase, Schedule
from django_tenants.utils import tenant_context

from goosetools.items.models import Item
from goosetools.pricing.models import ItemMarketDataEvent, PriceList
from goosetools.tenants.models import Client
from goosetools.utils import cron_header_line


class GetMarketData(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "market.get_market_data"

    def do(self):
        cron_header_line(self.code)
        r = requests.get("https://api.eve-echoes-market.com/market-stats/stats.csv")
        content = r.content
        decoded_content = content.decode("UTF-8")
        csv_lines = csv.reader(decoded_content.splitlines(), delimiter=",")
        lines = list(csv_lines)[1:]
        print(
            f"Found {len(lines)} lines of market data from https://api.eve-echoes-market.com/market-stats/stats.csv"
        )
        for tenant in Client.objects.all():
            with tenant_context(tenant):
                if tenant.name != "public":
                    print(f"Inserting latest market data for {tenant.name}")
                    for line in lines:
                        market_id = line[0]
                        datetime_str = line[2]
                        time = parse_datetime(datetime_str)
                        if time is None:
                            raise Exception(
                                f"Invalid datetime recieved from stats.csv: {time}"
                            )
                        try:
                            item = Item.objects.get(eve_echoes_market_id=market_id)
                            lowest_sell = decimal_or_none(line[5])
                            for ee_pl in PriceList.objects.filter(
                                api_type="eve_echoes_market"
                            ):
                                ItemMarketDataEvent.objects.update_or_create(
                                    price_list=ee_pl,
                                    item=item,
                                    time=time,
                                    defaults={
                                        "sell": decimal_or_none(line[3]),
                                        "buy": decimal_or_none(line[4]),
                                        "lowest_sell": lowest_sell,
                                        "highest_buy": decimal_or_none(line[6]),
                                    },
                                )
                            item.cached_lowest_sell = lowest_sell
                            item.save()
                        except Item.DoesNotExist:
                            print(
                                f"WARNING: Market Data Found for Item not in {settings.SITE_NAME}- id:{market_id}"
                            )


def decimal_or_none(val):
    if not val.strip():
        return None
    else:
        return Decimal(val.strip())
