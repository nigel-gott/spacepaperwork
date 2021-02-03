from rest_framework import serializers

from goosetools.users.models import GooseUser


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
