import csv

import requests
from django_extensions.management.jobs import HourlyJob

from core.models import Item, ItemMarketDataEvent
from django.utils.dateparse import parse_datetime
from decimal import Decimal
from django.utils.timezone import make_aware
from django.utils import timezone


class Job(HourlyJob):
    help = "Market Data Download Job"

    def execute(self):
        print("Run")
        r = requests.get("https://api.eve-echoes-market.com/market-stats/stats.csv")
        content = r.content
        decoded_content = content.decode("UTF-8")
        csv_lines = csv.reader(decoded_content.splitlines(), delimiter=",")
        for line in list(csv_lines)[1:]:
            market_id = line[0]
            time = make_aware(parse_datetime(line[2]), timezone=timezone.utc)
            item = Item.objects.get(eve_echoes_market_id=market_id)
            lowest_sell = decimal_or_none(line[5])
            event = ItemMarketDataEvent(
                item=item,
                time=time,
                sell=decimal_or_none(line[3]),
                buy=decimal_or_none(line[4]),
                lowest_sell=lowest_sell,
                highest_buy=decimal_or_none(line[6]),
            )
            item.cached_lowest_sell = lowest_sell
            item.save()

            event.full_clean()
            event.save()


def decimal_or_none(val):
    if not val.strip():
        return None
    else:
        return Decimal(val.strip())
