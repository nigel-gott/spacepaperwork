import csv
import select
import sys
import time
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
    "past_market_data_sync", expire_after=timedelta(hours=12)
)


class Command(BaseCommand):
    COMMAND_NAME = "sync_past_market_data"
    help = "Ensures all past market data is in the API"

    def add_arguments(self, parser):
        parser.add_argument("--lookback_days", action="store", type=int)
        parser.add_argument("--truncate", action="store_true")
        parser.add_argument("--request_sleep", action="store", type=float)

    def handle(self, *args, **options):
        r = requests.get("https://api.eve-echoes-market.com/market-stats/stats.csv")
        content = r.content
        decoded_content = content.decode("UTF-8")
        csv_lines = csv.reader(decoded_content.splitlines(), delimiter=",")

        lookback_days = options["lookback_days"] or 7
        cutoff = timezone.now() - timezone.timedelta(days=lookback_days)
        request_sleep = options["request_sleep"] or 1
        print(
            f"Looking back {lookback_days} days to {cutoff} with per request sleep "
            f"of {request_sleep} seconds."
        )

        for tenant in Client.objects.all():
            with tenant_context(tenant):
                if tenant.name != "public":
                    print(f"Syncing tenant: {tenant.name}")
                    if options["truncate"]:
                        self.truncate_if_sure()
                    for line in list(csv_lines)[1:]:
                        market_id = line[0]
                        print("------------------------------------------")
                        print(f"Syncing item id :{market_id}")
                        url = f"https://api.eve-echoes-market.com/market-stats/{market_id}"

                        time.sleep(request_sleep)
                        item_data = requests.get(url).json()
                        try:
                            self.sync_item(cutoff, item_data, market_id)
                        except Exception as e:  # pylint: disable=broad-except
                            print(f"WARNING EXCEPTION = {e}")
                    # After the first tenant we have cached all market data, turn off
                    # the sleep!
                    request_sleep = 0

    @staticmethod
    def sync_item(cutoff, item_data, market_id):
        latest_item_data = item_data[-1]
        item_obj = Item.objects.get(eve_echoes_market_id=market_id)
        item_obj.cached_lowest_sell = decimal_or_none(latest_item_data["lowest_sell"])
        item_obj.save()
        print(f"   Item is {item_obj}")
        print(f"   Found {len(item_data)} data points.")
        update_count = 0
        create_count = 0
        for item in reversed(item_data):
            event_time = timezone.make_aware(
                datetime.utcfromtimestamp(int(item["time"]))
            )
            if event_time < cutoff:
                print(f"   Cutting off at item {update_count + create_count}.")
                break
            _, created = ItemMarketDataEvent.objects.update_or_create(
                item=item_obj,
                time=event_time,
                defaults={
                    "sell": decimal_or_none(item["sell"]),
                    "buy": decimal_or_none(item["buy"]),
                    "lowest_sell": decimal_or_none(item["lowest_sell"]),
                    "highest_buy": decimal_or_none(item["highest_buy"]),
                    "volume": decimal_or_none(item["volume"]),
                },
            )
            if created:
                create_count = create_count + 1
            else:
                update_count = update_count + 1
        print(
            f"   Created {create_count} Points and Updated"
            f" {update_count} data points."
        )

    @staticmethod
    def truncate_if_sure():
        cursor = connection.cursor()
        print(
            "Are you sure you want to truncate? You have 10 seconds to enter Y to "
            "confirm."
        )
        i, _, _ = select.select([sys.stdin], [], [], 10)
        if i:
            read_input = sys.stdin.readline().strip().lower()
            if read_input == "y":
                print("!!!!!!!!!!!!! TRUNCATING MARKET DATA !!!!!!!!!!!!!!")
                cursor.execute("TRUNCATE TABLE pricing_itemmarketdataevent")
            else:
                print("Not truncating as you did not press Y")
        else:
            print("Not truncating as you did not press Y in time...")


def decimal_or_none(val):
    return val
