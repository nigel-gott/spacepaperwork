from rest_framework import serializers

from goosetools.pricing.models import (
    DataSet,
    ItemMarketDataEvent,
    LatestItemMarketDataEvent,
)


class PriceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSet
        fields = [
            "id",
            "owner",
            "name",
            "tags",
            "api_type",
            "price_type",
            "default",
        ]


class ItemMarketDataEventSerializer(serializers.ModelSerializer):
    item_sub_sub_type = serializers.CharField(source="item.item_type.name")
    item_sub_type = serializers.CharField(source="item.item_type.item_sub_type.name")
    item_type = serializers.CharField(
        source="item.item_type.item_sub_type.item_type.name"
    )
    item_id = serializers.IntegerField(source="item.id")
    item = serializers.CharField(source="item.name")
    eve_echoes_market_id = serializers.CharField(source="item.eve_echoes_market_id")

    class Meta:
        model = ItemMarketDataEvent
        fields = [
            "id",
            "time",
            "item_id",
            "item",
            "item_type",
            "item_sub_type",
            "item_sub_sub_type",
            "eve_echoes_market_id",
            "manual_override_price",
            "unique_user_id",
            "sell",
            "buy",
            "lowest_sell",
            "highest_buy",
            "volume",
        ]


class LatestItemMarketDataEventSerializer(serializers.ModelSerializer):
    event = ItemMarketDataEventSerializer()

    class Meta:
        model = LatestItemMarketDataEvent
        fields = ["id", "event"]
