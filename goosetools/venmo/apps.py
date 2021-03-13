from django.apps import AppConfig


class VenmoConfig(AppConfig):
    name = "goosetools.venmo"

    def ready(self):
        # pylint: disable=unused-import
        import goosetools.venmo.signals
