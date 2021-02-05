from rest_framework import serializers

from goosetools.industry.models import Ship, ShipOrder


# pylint: disable=abstract-method
class AssigneeOnlyContractCodeField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        user = self.context["request"].user.gooseuser
        if user in (instance.assignee, instance.recipient_character.user):
            return super().get_attribute(instance)
        return None


class ShipOrderSerializer(serializers.ModelSerializer):
    recipient_character_name = serializers.CharField(
        source="recipient_character.ingame_name", read_only=True
    )
    recipient_user_pk = serializers.CharField(
        source="recipient_character.user.pk", read_only=True
    )
    assignee_name = serializers.CharField(
        source="assignee.discord_username", read_only=True
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
            "recipient_user_pk",
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


class ShipSerializer(serializers.ModelSerializer):
    order_limit_group_name = serializers.CharField(
        source="order_limit_group.name", read_only=True
    )
    last_order = serializers.DateTimeField()

    class Meta:
        model = Ship
        fields = [
            "name",
            "tech_level",
            "free",
            "order_limit_group",
            "order_limit_group_name",
            "isk_price",
            "eggs_price",
            "prices_last_updated",
            "total_order_quantity",
            "total_order_quantity_last_month",
            "last_order",
            "total_isk_and_eggs_quantity",
            "total_isk_and_eggs_quantity_last_month",
        ]
