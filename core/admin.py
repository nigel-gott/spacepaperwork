# mypy: ignore-errors
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from core.models import (
    AnomType,
    Character,
    CharacterLocation,
    Contract,
    Corp,
    CorpHanger,
    DiscordUser,
    EggTransaction,
    Fleet,
    FleetAnom,
    FleetMember,
    FleetType,
    GooseUser,
    InventoryItem,
    IskTransaction,
    Item,
    ItemFilter,
    ItemFilterGroup,
    ItemLocation,
    ItemSubSubType,
    ItemSubType,
    ItemType,
    JunkedItem,
    LootBucket,
    LootGroup,
    LootShare,
    MarketOrder,
    Region,
    SoldItem,
    Station,
    System,
    TransferLog,
)

admin.site.register(Fleet)
admin.site.register(FleetType)
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
admin.site.register(LootShare)
admin.site.register(CharacterLocation)
admin.site.register(ItemLocation)
admin.site.register(CorpHanger)
admin.site.register(Station)
admin.site.register(TransferLog)
admin.site.register(FleetMember)
admin.site.register(DiscordUser)
admin.site.register(Contract)
admin.site.register(ItemFilter)
admin.site.register(ItemFilterGroup)


class RawIdForItemAdmin(admin.ModelAdmin):
    raw_id_fields = ("item",)


admin.site.register(IskTransaction, RawIdForItemAdmin)
admin.site.register(EggTransaction, RawIdForItemAdmin)
admin.site.register(InventoryItem, RawIdForItemAdmin)
admin.site.register(MarketOrder, RawIdForItemAdmin)
admin.site.register(SoldItem, RawIdForItemAdmin)
admin.site.register(JunkedItem, RawIdForItemAdmin)


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
