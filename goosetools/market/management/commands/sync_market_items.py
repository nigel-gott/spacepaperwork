import csv
import json
import re

import requests
from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context

from goosetools.items.models import (
    Item,
    ItemChangeProposal,
    ItemSubSubType,
    ItemSubType,
    ItemType,
)
from goosetools.tenants.models import Client


class Command(BaseCommand):
    COMMAND_NAME = "sync_market_items"
    help = "Syncs goosetools items with eve echoes market."

    def add_arguments(self, parser):
        parser.add_argument("--approve", action="store_true")
        parser.add_argument("--dontsync", action="store_true")

    @staticmethod
    def get_item_names():
        js = requests.get(
            "https://eve-echoes-market.com/static/js/main.caeeb854.chunk.js",
            {
                "credentials": "include",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0",
                    "Accept": "*/*",
                    "Accept-Language": "en-GB,en;q=0.5",
                    "Cache-Control": "max-age=0",
                },
                "referrer": "https://eve-echoes-market.com/",
                "method": "GET",
                "mode": "cors",
            },
        )
        text = js.text
        result = re.search(r"e.exports=JSON.parse\('(.*)'\)},35:function", text).group(
            1
        )
        result = bytes(result, "utf-8").decode("unicode_escape")
        result = result.replace("\\'", "'")
        result = result.replace("\\x", "\\\\x")
        result = result.replace("\\u", "\\\\u")
        result = result.replace('\\\\"', "'")
        data = json.loads(result)

        return data

    @staticmethod
    def setup_groups(data):
        item_types = set()
        item_sub_types = set()
        item_sub_sub_types = set()
        item_id_to_sub_sub_type = {}
        for _, item_type_data in data["groups"].items():
            assert item_type_data["kind"] == "GROUP"
            item_type_name = item_type_data["name"]
            item_types.add(item_type_name)
            for (
                _,
                item_sub_type_data,
            ) in item_type_data["contents"].items():
                assert item_sub_type_data["kind"] == "GROUP"
                item_sub_type_name = item_sub_type_data["name"]
                item_sub_types.add((item_type_name, item_sub_type_name))
                for (
                    _,
                    item_sub_sub_type_data,
                ) in item_sub_type_data["contents"].items():
                    assert item_sub_sub_type_data["kind"] == "GROUP"
                    item_sub_sub_type_name = item_sub_sub_type_data["name"]
                    item_sub_sub_types.add((item_sub_type_name, item_sub_sub_type_name))
                    for (
                        item_id,
                        item_data,
                    ) in item_sub_sub_type_data["contents"].items():
                        assert item_data["kind"] == "ITEM"
                        assert str(item_data["id"]) == item_id
                        item_id_to_sub_sub_type[item_id] = item_sub_sub_type_name

        for item_type in item_types:
            if ItemType.objects.filter(name=item_type).count() == 0:
                ItemType.objects.create(name=item_type)
        for item_type, item_sub_type in item_sub_types:
            if ItemSubType.objects.filter(name=item_sub_type).count() == 0:
                t1 = ItemType.objects.get(name=item_type)
                ItemSubType.objects.create(name=item_sub_type, item_type=t1)
        for item_sub_type, item_sub_sub_type in item_sub_sub_types:
            if ItemSubSubType.objects.filter(name=item_sub_sub_type).count() == 0:
                t2 = ItemSubType.objects.get(name=item_sub_type)
                ItemSubSubType.objects.create(
                    item_sub_type=t2,
                    name=item_sub_sub_type,
                )
        return item_id_to_sub_sub_type

    def handle(self, *args, **options):
        r = requests.get("https://api.eve-echoes-market.com/market-stats/stats.csv")
        content = r.content
        decoded_content = content.decode("UTF-8")
        csv_lines = csv.reader(decoded_content.splitlines(), delimiter=",")
        data = self.get_item_names()

        approve = options["approve"]
        dont_sync = options["dontsync"]

        if approve:
            print("WARNING WILL AUTO APPROVE ALL ITEM CHANGES AT THE END")

        for tenant in Client.objects.all():
            with tenant_context(tenant):
                if tenant.name != "public":
                    if not dont_sync:
                        item_id_to_sub_sub_type = self.setup_groups(data)
                        self.sync_items(csv_lines, data, item_id_to_sub_sub_type)
                    if approve:
                        for p in ItemChangeProposal.open_proposals():
                            p.approve(None)

    def sync_items(self, csv_lines, data, item_id_to_sub_sub_type):
        item_names = data["item_names"]
        seen_ids = set()
        for line in list(csv_lines)[1:]:
            market_id_csv = line[0]
            if market_id_csv in seen_ids:
                raise Exception(
                    f"Already seen {market_id_csv} but it appeared again " f"in {line}"
                )
            seen_ids.add(market_id_csv)
            try:
                item = Item.objects.get(eve_echoes_market_id=market_id_csv)

                latest_name = item_names[market_id_csv]["name_en"]
                item_type_name = item_id_to_sub_sub_type[market_id_csv]
                self.add_proposal(item, latest_name, market_id_csv, item_type_name)

            except Item.DoesNotExist:
                latest_name = item_names[market_id_csv]["name_en"]
                similar_names = Item.objects.filter(name__icontains=latest_name)
                item_type_name = item_id_to_sub_sub_type[market_id_csv]
                if similar_names.count() == 1:
                    self.add_proposal(
                        similar_names.first(),
                        latest_name,
                        market_id_csv,
                        item_type_name,
                    )
                elif similar_names.count() > 1:
                    raise Exception(f"Found many matches? {similar_names}")
                else:
                    self.create_proposal(latest_name, market_id_csv, item_type_name)

    @staticmethod
    def add_proposal(item, latest_name, market_id_csv, item_type_name):
        proposal = ItemChangeProposal()
        proposal.proposed_by_process = "autoimporter"
        proposal.existing_item = item
        proposal.change = "update"
        changed = False
        if item.name != latest_name:
            proposal.name = latest_name
            changed = True
        if item.eve_echoes_market_id != market_id_csv:
            proposal.eve_echoes_market_id = market_id_csv
            changed = True
        if item.item_type.name != item_type_name:
            proposal.item_type = ItemSubSubType.objects.get(name=item_type_name)
            changed = True
        if changed:
            proposal.save()

    @staticmethod
    def create_proposal(latest_name, market_id_csv, item_type_name):
        proposal = ItemChangeProposal()
        proposal.proposed_by_process = "autoimporter"
        proposal.existing_item = None
        proposal.change = "create"
        proposal.name = latest_name
        proposal.eve_echoes_market_id = market_id_csv
        proposal.item_type = ItemSubSubType.objects.get(name=item_type_name)
        proposal.save()
