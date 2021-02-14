from rest_framework import serializers

from goosetools.contracts.models import Contract


class ContractSerializer(serializers.ModelSerializer):
    from_user_discord_avatar_url = serializers.CharField(
        source="from_user.discord_avatar_url", read_only=True
    )
    from_user_display_name = serializers.CharField(
        source="from_user.display_name", read_only=True
    )
    to_char_ingame_name = serializers.CharField(
        source="to_char.ingame_name", read_only=True
    )
    to_char_display_name = serializers.CharField(
        source="to_char.user.display_name", read_only=True
    )
    isk = serializers.CharField(source="isk.amount", read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "from_user",
            "from_user_display_name",
            "from_user_discord_avatar_url",
            "to_char",
            "to_char_ingame_name",
            "to_char_display_name",
            "system",
            "created",
            "status",
            "log",
            "isk",
            "isk_display",
            "total_items",
        ]
