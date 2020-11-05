import django_tables2 as tables
from django.utils.html import format_html

from .models import Fleet


class IdColumn(tables.Column):
    def render(self, value):
        return format_html(
            "<a class='waves-effect waves-light btn orange' href='/fleet/{}'><i class='material-icons right'>cloud</i>Loot</a>",
            value,
            value,
        )


class FleetTable(tables.Table):
    id = IdColumn()

    class Meta:
        model = Fleet
