from django.contrib import admin

from goosetools.industry.models import OrderLimitGroup, Ship, ShipOrder


# pylint: disable=unused-argument
def make_free(modeladmin, request, queryset):
    queryset.update(free=True)


make_free.short_description = "Mark selected ships as free"  # type:ignore


# pylint: disable=unused-argument
def make_paid(modeladmin, request, queryset):
    queryset.update(free=False)


make_paid.short_description = "Mark selected ships as not free"  # type:ignore


class ShipAdmin(admin.ModelAdmin):
    search_fields = ("name", "tech_level", "free")
    list_display = ["name", "tech_level", "free"]
    actions = [make_paid, make_free]


class ShipOrderAdmin(admin.ModelAdmin):
    search_fields = ["uid"]
    list_display = [
        "uid",
        "ship",
        "quantity",
        "state",
        "created_at",
        "notes",
        "assignee",
        "recipient_character",
        "payment_method",
    ]


class OrderLimitGroupAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "days_between_orders"]


admin.site.register(OrderLimitGroup, OrderLimitGroupAdmin)
admin.site.register(ShipOrder, ShipOrderAdmin)
admin.site.register(Ship, ShipAdmin)
