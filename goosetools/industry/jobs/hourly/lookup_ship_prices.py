# pylint: disable=no-member
from __future__ import print_function

import os.path
import pickle

from django.utils import timezone
from django_extensions.management.jobs import HourlyJob
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from goosetools.industry.models import Ship, to_isk

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "1YlJsd_HnHSRQBtmqkfGpB83Wle6PpbP0s5NGX_8PScw"
SAMPLE_RANGE_NAME = "Profit Analysis!E13:N500"


class Job(HourlyJob):
    help = "Downloads ship prices from walmarx"

    def execute(self):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
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
            .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
        else:
            i = 0
            for row in values:
                try:
                    if len(row) > 9:
                        ship_name = row[9]
                        ship = Ship.objects.get(name=ship_name.strip())
                        try:
                            print(f"Attempting to parse prices for {ship_name}")
                            isk_price = parse_price(row[0])
                            eggs_price = parse_price(row[1])
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


def parse_price(price_str: str) -> int:
    return int(price_str.replace("$", "").replace(",", "").strip())
