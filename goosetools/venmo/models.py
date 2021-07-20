from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls.base import reverse
from hordak.models.core import Account

from goosetools.discord_bot.models import DiscordChannel
from goosetools.users.models import (
    LOOT_TRACKER,
    VENMO_ADMIN,
    AccessControlledModel,
    Character,
    Corp,
    CrudAccessController,
    PermissibleEntity,
)

TRANSFER_TYPES = [
    ("contract", "Via In Game Contracts"),
    ("generate_command", "Generates a command for the user to send"),
]

FOG_VENMO_API_TYPE = "fog_venmo"
SPACE_VENMO_API_TYPE = "space_venmo"
api_choices = [(SPACE_VENMO_API_TYPE, "space_venmo")]
if settings.VENMO_HOST_URL:
    api_choices.append((FOG_VENMO_API_TYPE, "Fog Venmo"))


class VirtualCurrency(models.Model):
    name = models.TextField(
        unique=True,
        validators=[
            RegexValidator(
                r"^[a-z0-9]+$",
                message="Currency Name must be all lowercase Alphanumeric with no "
                "spaces",
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


def create_access_controller():
    return CrudAccessController.objects.create()


def create_access_controller_id():
    return CrudAccessController.objects.create().id


def _generate_commands_under_length(
    message_sender, prefix, postfix, command_generator, data
):
    commands = []
    max_char_length = 1500
    fixed_length = len(prefix) + len(postfix)
    if fixed_length > max_char_length:
        warning = (
            "Just the prefix and postfix combined go over the discord "
            "single message length limit of 1500 characters. Ignoring "
            "the length limit and just generating a massive command for "
            "you."
        )
        message_sender(warning)
        max_char_length = float("inf")

    current_command_char_length = fixed_length
    parts = []
    for datum in data:
        next_part = command_generator(datum)
        if next_part is not None:
            next_length = len(next_part)
            if next_length + current_command_char_length > max_char_length:
                commands.append(f"{prefix}{''.join(parts)}{postfix}")
                parts = []
                current_command_char_length = fixed_length
            current_command_char_length += next_length
            parts.append(next_part)

    if len(parts) > 0:
        commands.append(f"{prefix}{''.join(parts)}{postfix}")

    return commands


def _transfer_vars(user, amount):
    return {
        "USER_TO_TRANSFER_TO": f"<@{user}>",
        "USER_TRANSFER_AMOUNT": str(int(amount)),
    }


def _deposit_vars(transferring_discord_uid, total_amount):
    return {
        "TRANSFERRING_DISCORD_USER": f"<@{transferring_discord_uid}>",
        "TOTAL_TRANSFER_AMOUNT": str(int(total_amount)),
    }


def _replace_vars(template, vars_dict):
    for key, val in vars_dict.items():
        template = template.replace(key, val)
    return template


def transfer_variable_names():
    return ", ".join(_transfer_vars(0, 0).keys())


def deposit_variable_names():
    return ", ".join(_deposit_vars(0, 0).keys())


class TransferMethod(AccessControlledModel, models.Model):
    name = models.TextField(
        help_text="The name users will see when choosing a transfer method"
    )
    transfer_type = models.TextField(choices=TRANSFER_TYPES)
    virtual_currency = models.ForeignKey(
        VirtualCurrency,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The virtual currency to perform an automatic transfer with",
    )
    via_contract = models.BooleanField(
        default=False, help_text="Whether to transfer using in-game contracts instead"
    )
    default = models.BooleanField(
        default=False, help_text="If this should become the default transfer method"
    )

    generated_command_help_text = models.TextField(
        null=True,
        blank=True,
        help_text="This will be displayed before any commands generated for a "
        "transferring user and should explain where to send the commands and "
        "how to use them.",
    )
    deposit_command_format = models.TextField(
        null=True,
        blank=True,
        help_text="This is the template used to generate an initial 'deposit' command "
        "the user should send before doing the transfer. If you include any"
        "of the following pieces of text they will be replaced with their "
        f"corresponding value when a command is generated: {deposit_variable_names()}",
    )
    transfer_prefix_command_format = models.TextField(
        null=True,
        blank=True,
        help_text="This is the template used to generate the start of a 'transfer' "
        "command the user should send to actually perform the transfer. If you "
        "include any of the following pieces of text they will be replaced with their "
        f"corresponding value when a command is generated: {deposit_variable_names()}",
    )
    transfer_user_command_format = models.TextField(
        null=True,
        blank=True,
        help_text="This is the template used per user who is being transfered profit "
        "and will be repeated between the prefix and postfix for every user "
        "to generate the entire transfer command."
        "If you include any of the following pieces of text they will be "
        "replaced with their corresponding value when a command is "
        f"generated: {transfer_variable_names()}",
    )
    transfer_postfix_command_format = models.TextField(
        null=True,
        blank=True,
        help_text="This is the template used to generate the end of a 'transfer' "
        "command the user should send to actually perform the transfer. If you "
        "include any of the following pieces of text they will be replaced with their "
        f"corresponding value when a command is generated: {deposit_variable_names()}",
    )

    auto_send_channel = models.ForeignKey(
        DiscordChannel, on_delete=models.CASCADE, null=True, blank=True
    )

    access_controller = models.ForeignKey(
        CrudAccessController,
        on_delete=models.CASCADE,
        default=create_access_controller,
    )

    def built_in_permissible_entities(self, _):
        return CrudAccessController.wrapper(
            adminable_by=[
                PermissibleEntity.allow_perm(VENMO_ADMIN, built_in=True),
            ],
        )

    def default_permissible_entities(self):
        return [
            ("view", PermissibleEntity.allow_perm(LOOT_TRACKER)),
            ("use", PermissibleEntity.allow_perm(LOOT_TRACKER)),
        ]

    @staticmethod
    def get_default() -> Optional["TransferMethod"]:
        try:
            return TransferMethod.objects.get(default=True)
        except TransferMethod.DoesNotExist:
            return None

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        try:
            other_default = TransferMethod.objects.get(default=True)
            if self.default and self != other_default:
                other_default.default = False
                other_default.save()
        except TransferMethod.DoesNotExist:
            self.default = True
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("venmo:transfer-detail", kwargs={"pk": self.pk})

    def make_deposit_command(self, transferring_discord_uid, total_amount):
        return _replace_vars(
            self.deposit_command_format,
            _deposit_vars(transferring_discord_uid, total_amount),
        )

    def make_transfer_command(
        self,
        transferring_discord_uid,
        total_amount,
        user_transfer_tuples,
        message_sender,
    ):
        d_vars = _deposit_vars(transferring_discord_uid, total_amount)
        prefix = _replace_vars(
            self.transfer_prefix_command_format,
            d_vars,
        )
        postfix = _replace_vars(
            self.transfer_postfix_command_format,
            d_vars,
        )

        def generate_user_transfer_line(data):
            user, amount = data

            # Don't generate transfers for the user who is doing the transfer!
            if user == transferring_discord_uid:
                return None

            user_line = _replace_vars(
                self.transfer_user_command_format, _transfer_vars(user, amount)
            )
            return user_line

        commands = _generate_commands_under_length(
            message_sender,
            prefix,
            postfix,
            generate_user_transfer_line,
            user_transfer_tuples,
        )
        if len(user_transfer_tuples) == 0:
            postfix_warning = (
                "\n\n No users were transferred isk by this command as "
                "you were the only person with shares."
            )
        else:
            postfix_warning = ""
        return (
            "\n\n SPLIT INTO SEPARATE DISCORD COMMAND DUE TO DISCORD CHARACTER LIMIT "
            "\n\n".join(commands) + postfix_warning
        )

    def example_deposit(self):
        return self.make_deposit_command("12345678", 100)

    def example_transfer(self):
        return self.make_transfer_command(
            "12345678",
            100,
            [("12345678", 10), ("22", 20), ("33", 30)],
            lambda x: None,
        )

    # noinspection PyMethodMayBeStatic
    # pylint: disable=no-self-use
    def deposit_variable_names(self):
        return deposit_variable_names()

    # noinspection PyMethodMayBeStatic
    # pylint: disable=no-self-use
    def transfer_variable_names(self):
        return transfer_variable_names()

    def example_huge_transfer(self):
        user_transfers = [(str(i), i) for i in range(300)]
        return self.make_transfer_command(
            "12345678",
            100,
            user_transfers,
            lambda x: None,
        )

    def __str__(self):
        return f"{self.name} ({self.transfer_type})"
