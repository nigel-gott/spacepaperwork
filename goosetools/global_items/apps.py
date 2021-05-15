from django.apps import AppConfig
from django.db.models.signals import post_migrate


# pylint: disable=unused-argument
def _run_global_items_import(sender, **kwargs):
    from goosetools.global_items.management.commands.item_data import (
        import_global_items_from_global_files,
    )

    import_global_items_from_global_files()


class GlobalItemsConfig(AppConfig):
    name = "goosetools.global_items"
    verbose_name = "Global Items"

    def ready(self) -> None:
        post_migrate.connect(_run_global_items_import, sender=self)
