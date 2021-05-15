import os
import subprocess
from collections import OrderedDict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

TABLES = OrderedDict(
    {
        "core_region": "region",
        "core_system": "system",
        "items_itemtype": "itemtype",
        "items_itemsubtype": "itemsubtype",
        "items_itemsubsubtype": "itemsubsubtype",
        "items_item": "item",
    }
)


def import_tenant_items_from_global():
    print("IMPORTING TENANT ITEMS FROM GLOBAL?")
    with connection.cursor() as cursor:
        for table, name in TABLES.items():
            cursor.execute(
                f"INSERT INTO {table}(SELECT * FROM public.global_items_global{name});"
            )


def clear_tenant_items():
    with connection.cursor() as cursor:
        for table in TABLES.values():
            cursor.execute(f"TRUNCATE {table} ;")


def import_global_items_from_global_files():
    if connection.schema_name != "public":
        print(
            f"Skipping import as schema name is not public but instead {connection.schema_name}"
        )
        return
    with connection.cursor() as cursor:
        dir_path = data_dir()
        for table, table_name in TABLES.items():
            import_file = os.path.abspath(os.path.join(dir_path, f"{table}.csv"))
            print(f"Global importing {table_name} from {import_file}")
            cursor.execute(f"TRUNCATE public.global_items_global{table_name} CASCADE;")
            copy_cmd = (
                f"\\copy public.global_items_global{table_name} "
                f"FROM '{os.path.abspath(import_file)}' "
                "WITH (FORMAT CSV, DELIMITER ',', NULL '', HEADER 1)"
            )
            run_cmd(copy_cmd)


def run_cmd(copy_cmd):
    host = settings.DATABASES["default"]["HOST"]
    port = settings.DATABASES["default"]["PORT"]
    username = settings.DATABASES["default"]["USER"]
    password = settings.DATABASES["default"]["PASSWORD"]
    name = settings.DATABASES["default"]["NAME"]
    env_with_pwd = os.environ.copy()
    env_with_pwd["PGPASSWORD"] = password
    subprocess.Popen(
        [
            "psql",
            f"--host={host}",
            f"--port={port}",
            f"--dbname={name}",
            f"--username={username}",
            "ON_ERROR_STOP=1",
            "-qAtX",
            "-c",
            copy_cmd,
        ],
        env=env_with_pwd,
    )


def export_tenant_items_to_global_files():
    dir_path = data_dir()
    for table, _ in TABLES.items():
        export_file_path = os.path.abspath(os.path.join(dir_path, f"{table}.csv"))
        copy_cmd = (
            f"\\copy {connection.schema_name}.{table} "
            f"TO '{os.path.abspath(export_file_path)}' "
            " WITH (FORMAT CSV, DELIMITER ',', NULL '', HEADER 1)"
        )
        run_cmd(copy_cmd)


class Command(BaseCommand):
    COMMAND_NAME = "item_data"
    help = "Syncs and loads item data"

    def add_arguments(self, parser):
        parser.add_argument("--export_tenant", action="store_true")
        parser.add_argument("--import_global", action="store_true")
        parser.add_argument("--import_tenant", action="store_true")
        parser.add_argument("--clear_tenant", action="store_true")
        parser.add_argument("--sync_global_schema_from_tenant", action="store_true")

    def handle(self, *args, **options):

        if options["export_tenant"]:
            export_tenant_items_to_global_files()

        if options["import_global"]:
            import_global_items_from_global_files()

        if options["clear_tenant"]:
            clear_tenant_items()

        if options["import_tenant"]:
            import_tenant_items_from_global()


def data_dir():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, "../../data")
