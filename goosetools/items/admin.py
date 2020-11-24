from django.contrib import admin

from goosetools.items.models import (
    CharacterLocation,
    CorpHanger,
    InventoryItem,
    Item,
    ItemLocation,
    ItemSubSubType,
    ItemSubType,
    ItemType,
    JunkedItem,
    Station,
)

admin.site.register(Item)
admin.site.register(ItemType)
admin.site.register(ItemSubType)
admin.site.register(ItemSubSubType)


class RawIdForItemAdmin(admin.ModelAdmin):
    raw_id_fields = ("item",)


admin.site.register(InventoryItem, RawIdForItemAdmin)
admin.site.register(JunkedItem, RawIdForItemAdmin)
admin.site.register(CharacterLocation)
admin.site.register(ItemLocation)
admin.site.register(CorpHanger)
admin.site.register(Station)
