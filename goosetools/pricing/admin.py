from django.contrib import admin

from goosetools.pricing.models import DataSet, ItemMarketDataEvent

admin.site.register(ItemMarketDataEvent)
admin.site.register(DataSet)
