from rest_framework import mixins
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
