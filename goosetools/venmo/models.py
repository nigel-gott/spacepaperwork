from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls.base import reverse
from hordak.models.core import Account

from goosetools.users.models import Character, Corp

FOG_VENMO_API_TYPE = "fog_venmo"
SPACE_VENMO_API_TYPE = "space_venmo"
api_choices = [(SPACE_VENMO_API_TYPE, "space_venmo")]
if settings.GOOSEFLOCK_FEATURES:
    api_choices.append((FOG_VENMO_API_TYPE, "Fog Venmo"))


class VirtualCurrency(models.Model):
    name = models.TextField(
        unique=True,
        validators=[
            RegexValidator(
                r"^[a-z0-9]+$",
                message="Currency Name must be all lowercase Alphanumeric with no spaces",
            )
        ],
    )
    description = models.TextField(blank=True)
    withdrawal_characters = models.ManyToManyField(Character, blank=True)
    api_type = models.TextField(choices=api_choices, default="space_venmo")
    corps = models.ManyToManyField(Corp, through="VirtualCurrencyStorageAccount")
    default = models.BooleanField(default=False, blank=True)

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, null=True, blank=True
    )

    def get_absolute_url(self):
        return reverse("venmo:currency-detail", kwargs={"pk": self.pk})

    def __str__(self) -> str:
        return self.name

    def balance(self):
        if not self.account:
            raise ValidationError("Missing account")
        monies = self.account.balance().monies()
        if len(monies) > 1:
            raise ValidationError("Multiple ccy found in account")
        return monies[0].amount

    @staticmethod
    def get_default() -> Optional["VirtualCurrency"]:
        try:
            return VirtualCurrency.objects.get(default=True)
        except VirtualCurrency.DoesNotExist:
            return None

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        try:
            other_default = VirtualCurrency.objects.get(default=True)
            if self.default and self != other_default:
                other_default.default = False
                other_default.save()
        except VirtualCurrency.DoesNotExist:
            self.default = True
        super().save(*args, **kwargs)


class VirtualCurrencyStorageAccount(models.Model):
    currency = models.ForeignKey(VirtualCurrency, on_delete=models.CASCADE)
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, blank=True, null=True
    )
    pending_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="pending_for",
    )

    def balance(self):
        if not self.account:
            raise ValidationError("Missing account")
        monies = self.account.balance().monies()
        if len(monies) > 1:
            raise ValidationError("Multiple ccy found in account")
        return monies[0].amount

    def setup(self):
        self.account, _ = Account.objects.update_or_create(
            name=f"{self.currency}_{self.corp}",
            defaults={
                "parent": self.currency.account,
                "type": Account.TYPES.asset,
                "is_bank_account": True,
                "currencies": ["EEI"],
            },
        )
        self.pending_account, _ = Account.objects.update_or_create(
            name=f"{self.currency}_{self.corp}_pending",
            defaults={
                "parent": self.account,
                "type": Account.TYPES.asset,
                "is_bank_account": True,
                "currencies": ["EEI"],
            },
        )
        self.save()
