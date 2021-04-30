from django.db import transaction
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from goosetools.items.models import Item
from goosetools.items.serializers import ItemSerializer
from goosetools.users.models import BASIC_ACCESS, HasGooseToolsPerm


class ItemDbQuerySet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    permission_classes = [HasGooseToolsPerm.of(BASIC_ACCESS)]
    queryset = Item.objects.prefetch_related(
        "item_type", "item_type__item_sub_type", "item_type__item_sub_type__item_type"
    ).all()

    serializer_class = ItemSerializer

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def refresh(self, request, pk=None):
        goose_user = self.get_object()
        output = goose_user.refresh_discord_data()
        serializer = self.get_serializer(goose_user)
        json_response = serializer.data
        json_response["output"] = output
        return Response(json_response)

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def ban(self, request, pk=None):
        return self._change_status(request, "rejected")

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def approve(self, request, pk=None):
        return self._change_status(request, "approved")

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def unapprove(self, request, pk=None):
        return self._change_status(request, "unapproved")

    def _change_status(self, request, status):
        goose_user = self.get_object()
        requesting_gooseuser = request.gooseuser
        goose_user.change_status(requesting_gooseuser, status)
        goose_user.save()
        serializer = self.get_serializer(goose_user)
        return Response(serializer.data)
