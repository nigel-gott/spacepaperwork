from rest_framework import serializers

from goosetools.pricing.models import PriceList
from goosetools.users.models import Character, GooseUser


class PriceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        fields = [
            "id",
            "owner",
            "name",
            "tags",
            "default",
        ]

