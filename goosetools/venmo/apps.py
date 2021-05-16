from django.apps import AppConfig


class VenmoConfig(AppConfig):
    name = "goosetools.venmo"

    def ready(self):
        # pylint: disable=unused-import
        # noinspection PyUnresolvedReferences
        import goosetools.venmo.signals
