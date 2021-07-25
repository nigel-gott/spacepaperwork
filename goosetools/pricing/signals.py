from django.db.models.signals import post_save
from django.dispatch import receiver

from goosetools.pricing.models import ItemMarketDataEvent, LatestItemMarketDataEvent


# noinspection PyUnusedLocal
# pylint: disable=unused-argument
@receiver(post_save, sender=ItemMarketDataEvent)
def new_market_data(sender, instance, **kwargs):
    try:
        existing = LatestItemMarketDataEvent.objects.get(
            price_list=instance.price_list, item=instance.item
        )
    except LatestItemMarketDataEvent.DoesNotExist:
        existing = None

    if (
        existing is None
        or existing.time < instance.time
        or instance.manual_override_price
    ):
        LatestItemMarketDataEvent.objects.update_or_create(
            price_list=instance.price_list,
            item=instance.item,
            defaults={
                "time": instance.time,
                "event": instance,
            },
        )
