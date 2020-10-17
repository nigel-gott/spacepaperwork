from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *

# Register your models here.
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
admin.site.register(InventoryItem)
admin.site.register(LootShare)


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('timezone',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('timezone',)}),
    )


admin.site.register(GooseUser, CustomUserAdmin)
