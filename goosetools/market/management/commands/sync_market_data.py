import csv

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django_tenants.utils import tenant_context
from items.models import Item
from market.jobs.hourly.get_market_data import decimal_or_none
from pricing.models import ItemMarketDataEvent
from tenants.models import Client


class Command(BaseCommand):
    COMMAND_NAME = "repeat_groups"
    help = "Deletes all existing market data, redownloads from source and updates."

    def handle(self, *args, **options):
        r = requests.get("https://api.eve-echoes-market.com/market-stats/stats.csv")
        content = r.content
        decoded_content = content.decode("UTF-8")
        csv_lines = csv.reader(decoded_content.splitlines(), delimiter=",")
        for tenant in Client.objects.all():
            with tenant_context(tenant):
                if tenant.name != "public":
                    for line in list(csv_lines)[1:]:
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
                                f"WARNING: Market Data Found for Item not in {settings.SITE_NAME}- id:{market_id}"
                            )
