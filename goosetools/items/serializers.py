from rest_framework import serializers

from goosetools.items.models import Item


class ItemSerializer(serializers.ModelSerializer):
    item_sub_sub_type = serializers.CharField(source="item_type.name")
    item_sub_type = serializers.CharField(source="item_type.item_sub_type.name")
    item_type = serializers.CharField(source="item_type.item_sub_type.item_type.name")

    class Meta:
        model = Item
        fields = [
            "id",
            "item_type",
            "item_sub_type",
            "item_sub_sub_type",
            "name",
            "eve_echoes_market_id",
            "cached_lowest_sell",
        ]
