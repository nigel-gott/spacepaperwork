from django.contrib import admin

from goosetools.bank.models import EggTransaction, IskTransaction


class RawIdForItemAdmin(admin.ModelAdmin):
    raw_id_fields = ("item",)


admin.site.register(IskTransaction, RawIdForItemAdmin)
admin.site.register(EggTransaction, RawIdForItemAdmin)
