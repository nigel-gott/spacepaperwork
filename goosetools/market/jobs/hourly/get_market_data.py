import csv
from decimal import Decimal

import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from django_extensions.management.jobs import HourlyJob

from goosetools.items.models import Item
from goosetools.pricing.models import ItemMarketDataEvent


class Job(HourlyJob):
    help = "Market Data Download Job"

    def execute(self):
        r = requests.get("https://api.eve-echoes-market.com/market-stats/stats.csv")
        content = r.content
        decoded_content = content.decode("UTF-8")
        csv_lines = csv.reader(decoded_content.splitlines(), delimiter=",")
        for line in list(csv_lines)[1:]:
            market_id = line[0]
            datetime_str = line[2]
            datetime_from_csv = parse_datetime(datetime_str)
            if datetime_from_csv is None:
                raise Exception(
                    f"Invalid datetime recieved from stats.csv: {datetime_str}"
                )
            time = make_aware(datetime_from_csv, timezone=timezone.utc)
            try:
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
            except Item.DoesNotExist:
                print(
                    f"WARNING: Market Data Found for Item not in Goosetools - id:{market_id}"
                )


def decimal_or_none(val):
    if not val.strip():
        return None
    else:
        return Decimal(val.strip())
