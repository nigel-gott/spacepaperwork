from django.apps import AppConfig


class GlobalItemsConfig(AppConfig):
    name = "goosetools.global_items"
    verbose_name = "Global Items"

    def ready(self) -> None:
        from goosetools.global_items.management.commands.item_data import (
            import_global_items_from_global_files,
        )

        import_global_items_from_global_files()
