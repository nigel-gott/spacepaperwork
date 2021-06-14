from django.contrib import admin

from goosetools.pricing.models import ItemMarketDataEvent, PriceList

admin.site.register(ItemMarketDataEvent)
admin.site.register(PriceList)
