from django.contrib import admin

from goosetools.fleets.models import Fleet, FleetMember

admin.site.register(FleetMember)
admin.site.register(Fleet)
