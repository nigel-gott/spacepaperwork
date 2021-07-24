from dateutil.parser import parse
from django.utils import timezone
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.viewsets import GenericViewSet

from goosetools.pricing.models import (
    ItemMarketDataEvent,
    LatestItemMarketDataEvent,
    PriceList,
)
from goosetools.pricing.serializers import (
    ItemMarketDataEventSerializer,
    LatestItemMarketDataEventSerializer,
    PriceListSerializer,
)
from goosetools.users.models import BASIC_ACCESS, HasGooseToolsPerm


class LatestItemMarketDataEventViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    permission_classes = [HasGooseToolsPerm.of(BASIC_ACCESS)]

    serializer_class = LatestItemMarketDataEventSerializer
    queryset = LatestItemMarketDataEvent.objects.all()

    def get_queryset(self):
        pricelist_id = self.request.GET.get("pricelist_id", None)
        if pricelist_id is None:
            pricelist = PriceList.objects.get(default=True)
        else:
            pricelist = PriceList.objects.get(id=pricelist_id)

        query_dict = {"price_list": pricelist}

        if not pricelist.access_controller.can_view(self.request.gooseuser):
            raise PermissionDenied()

        return (
            LatestItemMarketDataEvent.objects.prefetch_related(
                "event",
                "event__item",
                "event__item__item_type",
                "event__item__item_type__item_sub_type",
                "event__item__item_type__item_sub_type__item_type",
            )
            .filter(**query_dict)
            .all()
        )


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

        from_date_str = self.request.GET.get("from_date", None)
        to_date_str = self.request.GET.get("to_date", None)
        if not (from_date_str or to_date_str):

            if not from_date_str:
                from_date = timezone.now() - timezone.timedelta(days=3)
            else:
                from_date = parse(from_date_str)

            if not to_date_str:
                to_date = timezone.now()
            else:
                to_date = parse(to_date_str)

            if from_date > to_date:
                raise ValidationError("From must be before to date.")

            query_dict["time__gte"] = from_date
            query_dict["time__lte"] = to_date
        else:
            raise ValidationError("At least one of from_date or to_date must be given.")

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
