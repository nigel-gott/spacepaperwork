from rest_framework import serializers

from goosetools.items.models import Item


class ItemSerializer(serializers.ModelSerializer):
    # corp = serializers.CharField(source="corp.name", read_only=True)
    # owner_display_name = serializers.CharField(
    #     source="user.display_name", read_only=True
    # )
    # owner_uid = serializers.CharField(source="user.uid", read_only=True)
    item_sub_sub_type = serializers.CharField(source="item_type.name")
    item_sub_type = serializers.CharField(source="item_type.item_sub_type.name")
    item_type = serializers.CharField(source="item_type.item_sub_type.item_type.name")

    class Meta:
        model = Item
        fields = [
            "item_type",
            "item_sub_type",
            "item_sub_sub_type",
            "name",
            "eve_echoes_market_id",
            "cached_lowest_sell",
        ]
