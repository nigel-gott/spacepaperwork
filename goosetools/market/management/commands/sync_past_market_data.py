import csv
from datetime import datetime, timedelta

import requests
import requests_cache
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from django_tenants.utils import tenant_context

from goosetools.items.models import Item
from goosetools.pricing.models import ItemMarketDataEvent
from goosetools.tenants.models import Client

session = requests_cache.CachedSession(
    "past_market_data_sync", expire_after=timedelta(hours=1)
)


class Command(BaseCommand):
    COMMAND_NAME = "sync_past_market_data"
    help = "Ensures all past market data is in the API"

    def handle(self, *args, **options):
        r = requests.get("https://api.eve-echoes-market.com/market-stats/stats.csv")
        content = r.content
        decoded_content = content.decode("UTF-8")
        csv_lines = csv.reader(decoded_content.splitlines(), delimiter=",")

        for tenant in Client.objects.all():
            with tenant_context(tenant):
                if tenant.name != "public":
                    cursor = connection.cursor()
                    cursor.execute("TRUNCATE TABLE pricing_itemmarketdataevent")
                    for line in list(csv_lines)[1:]:
                        market_id = line[0]
                        print(f"Sync {market_id}...")
                        url = f"https://api.eve-echoes-market.com/market-stats/{market_id}"
                        item_data = requests.get(url).json()
                        latest_item_data = item_data[-1]
                        item_obj = Item.objects.get(eve_echoes_market_id=market_id)
                        item_obj.cached_lowest_sell = decimal_or_none(
                            latest_item_data["lowest_sell"]
                        )
                        item_obj.save()

                        for item in item_data:
                            time_str = timezone.make_aware(
                                datetime.utcfromtimestamp(int(item["time"]))
                            )
                            ItemMarketDataEvent.objects.update_or_create(
                                item=item_obj,
                                time=time_str,
                                defaults={
                                    "sell": decimal_or_none(item["sell"]),
                                    "buy": decimal_or_none(item["buy"]),
                                    "lowest_sell": decimal_or_none(item["lowest_sell"]),
                                    "highest_buy": decimal_or_none(item["highest_buy"]),
                                    "volume": decimal_or_none(item["volume"]),
                                },
                            )


def decimal_or_none(val):
    return val
