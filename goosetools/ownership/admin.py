from django.contrib import admin

from goosetools.fleets.models import AnomType, FleetAnom
from goosetools.ownership.models import LootBucket, LootGroup, LootShare, TransferLog

admin.site.register(FleetAnom)
admin.site.register(AnomType)
admin.site.register(LootGroup)
admin.site.register(LootBucket)
admin.site.register(LootShare)
admin.site.register(TransferLog)
