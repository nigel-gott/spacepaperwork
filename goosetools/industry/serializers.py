from rest_framework import serializers

from goosetools.industry.models import ShipOrder


# pylint: disable=abstract-method
class AssigneeOnlyContractCodeField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        user = self.context["request"].user
        if (
            instance.assignee == user
            or instance.recipient_character.discord_user == user.discord_user
        ):
            return super().get_attribute(instance)
        return None


class ShipOrderSerializer(serializers.ModelSerializer):
    recipient_character_name = serializers.CharField(
        source="recipient_character.ingame_name", read_only=True
    )
    recipient_discord_user_pk = serializers.CharField(
        source="recipient_character.discord_user.pk", read_only=True
    )
    assignee_name = serializers.CharField(
        source="assignee.discord_user.gooseuser.username", read_only=True
    )
    currently_blocked = serializers.BooleanField(read_only=True)
    needs_manual_price = serializers.BooleanField(read_only=True)
    payment_taken = serializers.BooleanField(
        source="payment_actually_taken", read_only=True
    )
    uid = AssigneeOnlyContractCodeField()

    availible_transition_names = serializers.ReadOnlyField()

    class Meta:
        model = ShipOrder
        fields = [
            "id",
            "uid",
            "blocked_until",
            "created_at",
            "currently_blocked",
            "ship",
            "quantity",
            "assignee",
            "recipient_discord_user_pk",
            "payment_method",
            "state",
            "notes",
            "recipient_character_name",
            "assignee_name",
            "availible_transition_names",
            "payment_taken",
            "price",
            "needs_manual_price",
        ]
