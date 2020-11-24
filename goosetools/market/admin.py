from django.contrib import admin

from goosetools.market.models import MarketOrder, SoldItem


# Register your models here.
class RawIdForItemAdmin(admin.ModelAdmin):
    raw_id_fields = ("item",)


admin.site.register(MarketOrder, RawIdForItemAdmin)
admin.site.register(SoldItem, RawIdForItemAdmin)
