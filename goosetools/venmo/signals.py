from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from hordak.models.core import Account

from goosetools.venmo.models import VirtualCurrency, VirtualCurrencyStorageAccount


# noinspection PyUnusedLocal
@receiver(pre_save, sender=VirtualCurrency)
# pylint: disable=unused-argument
def create_root_account(sender, instance, **kwargs):
    instance.account, _ = Account.objects.update_or_create(
        name=instance.name,
        defaults={
            "parent": None,
            "type": Account.TYPES.asset,
            "is_bank_account": True,
            "currencies": ["EEI"],
        },
    )


# noinspection PyUnusedLocal
@receiver(post_delete, sender=VirtualCurrencyStorageAccount)
# pylint: disable=unused-argument
def delete_storage_account(sender, instance, **kwargs):
    if instance.pending_account:
        instance.pending_account.delete()
    if instance.account:
        instance.account.delete()


# noinspection PyUnusedLocal
@receiver(post_delete, sender=VirtualCurrency)
# pylint: disable=unused-argument
def delete_root_account(sender, instance, **kwargs):
    if instance.account:
        instance.account.delete()
