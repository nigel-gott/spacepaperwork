from rest_framework import serializers

from goosetools.pricing.models import ItemMarketDataEvent, PriceList


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


class ItemMarketDataEventSerializer(serializers.ModelSerializer):
    item_sub_sub_type = serializers.CharField(source="item.item_type.name")
    item_sub_type = serializers.CharField(source="item.item_type.item_sub_type.name")
    item_type = serializers.CharField(
        source="item.item_type.item_sub_type.item_type.name"
    )
    item = serializers.CharField(source="item.name")
    eve_echoes_market_id = serializers.CharField(source="item.eve_echoes_market_id")

    class Meta:
        model = ItemMarketDataEvent
        fields = [
            "id",
            "time",
            "item",
            "item_type",
            "item_sub_type",
            "item_sub_sub_type",
            "eve_echoes_market_id",
            "sell",
            "buy",
            "lowest_sell",
            "highest_buy",
            "volume",
        ]
