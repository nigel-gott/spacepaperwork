from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.viewsets import GenericViewSet

from goosetools.pricing.models import ItemMarketDataEvent, PriceList
from goosetools.pricing.serializers import (
    ItemMarketDataEventSerializer,
    PriceListSerializer,
)
from goosetools.users.models import BASIC_ACCESS, HasGooseToolsPerm


class ItemMarketDataEventViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    permission_classes = [HasGooseToolsPerm.of(BASIC_ACCESS)]

    serializer_class = ItemMarketDataEventSerializer
    queryset = ItemMarketDataEvent.objects.all()

    def get_queryset(self):
        pricelist_id = self.request.GET.get("pricelist_id", None)
        if pricelist_id is None:
            pricelist = PriceList.objects.get(default=True)
        else:
            pricelist = PriceList.objects.get(id=pricelist_id)

        query_dict = {"price_list": pricelist}

        from_date_str = self.request.GET.get("from", None)
        to_date_str = self.request.GET.get("to", None)
        if from_date_str is None and to_date_str is None:
            sq = ItemMarketDataEvent.objects.filter(
                price_list=pricelist, item=OuterRef("item")
            ).order_by("-time")
            return (
                ItemMarketDataEvent.objects.prefetch_related(
                    "item",
                    "item__item_type",
                    "item__item_type__item_sub_type",
                    "item__item_type__item_sub_type__item_type",
                )
                .filter(pk=Subquery(sq.values("pk")[:1]))
                .all()
            )
        else:
            if from_date_str is None:
                from_date = timezone.now() - timezone.timedelta(days=3)
            else:
                from_date = parse_date(from_date_str)

            if to_date_str is None:
                to_date = timezone.now()
            else:
                to_date = parse_date(to_date_str)

            if from_date > to_date:
                raise ValidationError("From must be before to date.")

            query_dict["time__gte"] = from_date
            query_dict["time__lte"] = to_date

        if not pricelist.access_controller.can_view(self.request.gooseuser):
            raise PermissionDenied()

        return (
            ItemMarketDataEvent.objects.prefetch_related(
                "item",
                "item__item_type",
                "item__item_type__item_sub_type",
                "item__item_type__item_sub_type__item_type",
            )
            .filter(**query_dict)
            .all()
        )


class PriceListViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    permission_classes = [HasGooseToolsPerm.of([BASIC_ACCESS])]
    queryset = PriceList.objects.all()

    serializer_class = PriceListSerializer
