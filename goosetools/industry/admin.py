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
    list_display = ["name", "tech_level", "free"]
    actions = [make_paid, make_free]
    # recipient_character = models.ForeignKey(Character, on_delete=models.CASCADE)
    # assignee = models.ForeignKey(
    #     settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    # )
    # contract_made = models.BooleanField(default=False)
    # ship = models.ForeignKey(Ship, on_delete=models.CASCADE)
    # uid = models.TextField(unique=True)
    # quantity = models.PositiveIntegerField()
    # created_at = models.DateTimeField()
    # state = FSMField(default="not_started")
    # notes = models.TextField(blank=True)
    # payment_method = models.TextField(choices=PAYMENT_METHODS)


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


admin.site.register(ShipOrder, ShipOrderAdmin)
admin.site.register(Ship, ShipAdmin)
