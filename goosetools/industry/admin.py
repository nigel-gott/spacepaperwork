from django.contrib import admin

from goosetools.industry.models import Ship, ShipOrder


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
    actions = [make_paid, make_free]


admin.site.register(ShipOrder)
admin.site.register(Ship, ShipAdmin)
