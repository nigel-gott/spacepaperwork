from django.apps import AppConfig


class PricingConfig(AppConfig):
    name = "goosetools.pricing"

    def ready(self) -> None:
        # noinspection PyUnresolvedReferences
        import goosetools.pricing.signals  # pylint: disable=unused-import
