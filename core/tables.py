import django_tables2 as tables
from .models import Fleet


class FleetTable(tables.Table):
    class Meta:
        model = Fleet
        fields = ("fc", "name", "fleet_type", "start")
