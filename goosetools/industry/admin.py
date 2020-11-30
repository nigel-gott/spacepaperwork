from django.contrib import admin

from goosetools.industry.models import Ship, ShipOrder


class ShipAdmin(admin.ModelAdmin):
    search_fields = ("name", "tech_level", "free")


admin.site.register(ShipOrder)
admin.site.register(Ship, ShipAdmin)
