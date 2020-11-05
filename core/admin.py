from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *

# Register your models here.
admin.site.register(Fleet)
admin.site.register(FleetType)
admin.site.register(LootType)
admin.site.register(Corp)
admin.site.register(Character)
admin.site.register(System)
admin.site.register(Region)
admin.site.register(Item)
admin.site.register(ItemType)
admin.site.register(ItemSubType)
admin.site.register(ItemSubSubType)
admin.site.register(FleetAnom)
admin.site.register(AnomType)
admin.site.register(LootGroup)
admin.site.register(LootBucket)
admin.site.register(InventoryItem)
admin.site.register(LootShare)
admin.site.register(CharacterLocation)
admin.site.register(ItemLocation)
admin.site.register(CorpHanger)
admin.site.register(Station)
admin.site.register(SoldItem)
admin.site.register(IskTransaction)
admin.site.register(EggTransaction)
admin.site.register(MarketOrder)
admin.site.register(JunkedItem)
admin.site.register(TransferLog)
admin.site.register(FleetMember)
admin.site.register(DiscordUser)
admin.site.register(Contract)
admin.site.register(ItemFilter)
admin.site.register(ItemFilterGroup)

# discord_user = models.onetoonefield(discorduser, on_delete=models.cascade)
# timezone = timezonefield(default='europe/london')
# broker_fee = models.decimalfield(verbose_name="your broker fee in %", max_digits=5, decimal_places=2, default=8.0)
# transaction_tax = models.decimalfield(verbose_name="your transaction tax in %", max_digits=5, decimal_places=2, default=15.0)
# default_character = models.onetoonefield(character, on_delete=models.cascade)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "timezone",
                    "transaction_tax",
                    "discord_user",
                    "default_character",
                    "broker_fee",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "timezone",
                    "transaction_tax",
                    "discord_user",
                    "default_character",
                    "broker_fee",
                )
            },
        ),
    )


admin.site.register(GooseUser, CustomUserAdmin)
