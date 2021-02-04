from rest_framework import serializers

from goosetools.users.models import Character, GooseUser


class CharacterSerializer(serializers.ModelSerializer):
    owner_display_name = serializers.CharField(
        source="user.display_name", read_only=True
    )
    owner_uid = serializers.CharField(source="user.uid", read_only=True)
    owner_status = serializers.CharField(source="user.status", read_only=True)

    class Meta:
        model = Character
        fields = [
            "id",
            "ingame_name",
            "corp",
            "owner_uid",
            "owner_display_name",
            "owner_status",
        ]


class GooseUserSerializer(serializers.ModelSerializer):
    char_names = serializers.CharField(read_only=True)
    groups = serializers.CharField(read_only=True)
    voucher_username = serializers.CharField(source="voucher.username", read_only=True)

    class Meta:
        model = GooseUser
        fields = [
            "id",
            "uid",
            "username",
            "display_name",
            "char_names",
            "uid",
            "discord_avatar_url",
            "status",
            "notes",
            "sa_profile",
            "voucher_username",
            "groups",
        ]
