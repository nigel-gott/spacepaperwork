# pylint: disable=no-member
from __future__ import print_function

import os.path
import pickle

from django.conf import settings
from django.utils import timezone
from django_cron import CronJobBase, Schedule
from django_tenants.utils import tenant_context
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from goosetools.industry.models import Ship, to_isk
from goosetools.tenants.models import Client
from goosetools.utils import cron_header_line

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class LookupShipPrices(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "industry.lookup_ship_prices"

    def do(self):
        cron_header_line(self.code)
        if (
            settings.SHIP_PRICE_GOOGLE_SHEET_ID
            and settings.SHIP_PRICE_GOOGLE_SHEET_CELL_RANGE
        ):
            for tenant in Client.objects.all():
                if tenant.name != "public":
                    with tenant_context(tenant):
                        creds = None
                        # The file token.pickle stores the user's access and refresh tokens, and is
                        # created automatically when the authorization flow completes for the first
                        # time.
                        if os.path.exists("token.pickle"):
                            with open("token.pickle", "rb") as token:
                                creds = pickle.load(token)
                        # If there are no (valid) credentials available, let the user log in.
                        if not creds or not creds.valid:
                            if creds and creds.expired and creds.refresh_token:
                                creds.refresh(Request())
                            else:
                                flow = InstalledAppFlow.from_client_secrets_file(
                                    ".google.credentials.json", SCOPES
                                )
                                creds = flow.run_local_server(port=0)
                            # Save the credentials for the next run
                            with open("token.pickle", "wb") as token:
                                pickle.dump(creds, token)

                    service = build("sheets", "v4", credentials=creds)

                    # Call the Sheets API
                    sheet = service.spreadsheets()
                    result = (
                        sheet.values()
                        .get(
                            spreadsheetId=settings.SHIP_PRICE_GOOGLE_SHEET_ID,
                            range=settings.SHIP_PRICE_GOOGLE_SHEET_CELL_RANGE,
                        )
                        .execute()
                    )
                    values = result.get("values", [])

                    if not values:
                        print("No data found.")
                    else:
                        i = 0
                        for row in values:
                            try:
                                if len(row) > 2:
                                    ship_name = row[0]
                                    ship = Ship.objects.get(name=ship_name.strip())
                                    try:
                                        isk_price = parse_price(row[1])
                                        eggs_price = parse_price(row[2])
                                        ship.isk_price = to_isk(isk_price)
                                        ship.eggs_price = to_isk(eggs_price)
                                    except Exception as e:  # pylint: disable=broad-except
                                        ship.isk_price = None
                                        ship.eggs_price = None
                                        print(f"Failed parsing prices for {ship_name}")
                                        print(e)

                                    ship.prices_last_updated = timezone.now()
                                    ship.full_clean()
                                    ship.save()
                                    print(f"Added {ship}")
                            except Exception as e:  # pylint: disable=broad-except
                                print(f"Failed for row {i}")
                                print(e)
                            i = i + 1
        else:
            print(
                "Not looking up ship prices as no spreadsheet and range is "
                "configured."
            )


def parse_price(price_str: str) -> int:
    return int(price_str.replace("$", "").replace(",", "").strip())
