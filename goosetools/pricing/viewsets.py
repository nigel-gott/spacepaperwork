import re
from collections import OrderedDict

from dateutil.parser import parse
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import F, TextField
from django.forms import CharField
from django.utils import timezone
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from goosetools.pricing.models import (
    DataSet,
    ItemMarketDataEvent,
    LatestItemMarketDataEvent,
)
from goosetools.pricing.serializers import (
    ItemMarketDataEventSerializer,
    LatestItemMarketDataEventSerializer,
    PriceListSerializer,
)
from goosetools.users.models import BASIC_ACCESS, HasGooseToolsPerm


class DataTablesServerSidePagination(LimitOffsetPagination):
    offset_query_param = "start"
    default_limit = 50
    limit_query_param = "length"
    pre_filtered_count = None

    def paginate_queryset(self, queryset, request, view=None):
        self.pre_filtered_count = self.get_count(queryset)
        search_term = request.GET.get("search[value]", False)
        if search_term and view and hasattr(view, "searchable_fields"):
            search_vector = SearchVector(*view.searchable_fields)
            queryset = queryset.annotate(search=search_vector).filter(
                search=SearchQuery(search_term, search_type="websearch")
            )
        if view and hasattr(view, "orderable_fields"):
            orders = []
            for field in request.GET.keys():
                if field.startswith("order["):
                    result = re.search(r"order\[([0-9]+)]\[dir]", field, re.IGNORECASE)
                    if result:
                        order_id = int(result.group(1))
                        col_id = request.GET.get(f"order[{order_id}][column]", False)
                        direction = request.GET.get(f"order[{order_id}][dir]", False)
                        if direction and col_id:
                            data = request.GET.get(f"columns[{col_id}][data]", False)
                            if data and data in view.orderable_fields:
                                order_field = view.orderable_fields[data]
                                f = F(order_field)
                                if direction == "desc":
                                    f = f.desc(nulls_last=True)
                                else:
                                    f = f.asc(nulls_last=True)
                                orders.append(f)
            queryset = queryset.order_by(*orders)

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("recordsTotal", self.pre_filtered_count),
                    ("recordsFiltered", self.count),
                    ("draw", int(self.request.GET.get("draw"))),
                    ("data", data),
                ]
            )
        )


class LatestItemMarketDataEventViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    pagination_class = DataTablesServerSidePagination
    permission_classes = [HasGooseToolsPerm.of(BASIC_ACCESS)]
    searchable_fields = [
        "item__name",
        "time",
        "item__eve_echoes_market_id",
        "event__unique_user_id",
    ]
    orderable_fields = {
        "event.time": "time",
        "event.item": "item__name",
        "event.eve_echoes_market_id": "item__eve_echoes_market_id",
        "event.unique_user_id": "event__unique_user_id",
        "event.buy": "event__buy",
        "event.sell": "event__sell",
        "event.highest_buy": "event__highest_buy",
        "event.lowest_sell": "event__lowest_sell",
        "event.volume": "event__volume",
    }

    serializer_class = LatestItemMarketDataEventSerializer
    queryset = LatestItemMarketDataEvent.objects.all()

    def get_queryset(self):
        pricelist_id = self.request.GET.get("pricelist_id", None)
        if pricelist_id is None:
            pricelist = DataSet.objects.get(default=True)
        else:
            pricelist = DataSet.objects.get(id=pricelist_id)

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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50


def _searchable(f):
    not_searchable_types = [TextField, CharField]
    for t in not_searchable_types:
        if isinstance(f, t):
            return True
    return False


class ItemMarketDataEventViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    pagination_class = DataTablesServerSidePagination
    permission_classes = [HasGooseToolsPerm.of(BASIC_ACCESS)]
    searchable_fields = [
        "item__name",
        "time",
        "item__eve_echoes_market_id",
        "unique_user_id",
    ]
    orderable_fields = {
        "time": "time",
        "item": "item__name",
        "eve_echoes_market_id": "item__eve_echoes_market_id",
        "unique_user_id": "unique_user_id",
        "buy": "buy",
        "sell": "sell",
        "highest_buy": "highest_buy",
        "lowest_sell": "lowest_sell",
        "volume": "volume",
    }

    serializer_class = ItemMarketDataEventSerializer
    queryset = ItemMarketDataEvent.objects.all()

    def get_queryset(self):
        pricelist_id = self.request.GET.get("pricelist_id", None)
        if pricelist_id is None:
            pricelist = DataSet.objects.get(default=True)
        else:
            pricelist = DataSet.objects.get(id=pricelist_id)

        query_dict = {"price_list": pricelist}

        from_date_str = self.request.GET.get("from_date", None)
        to_date_str = self.request.GET.get("to_date", None)
        if from_date_str or to_date_str:
            from_date = None
            to_date = None

            if from_date_str:
                from_date = timezone.make_aware(parse(from_date_str))
                query_dict["time__gte"] = from_date

            if to_date_str:
                to_date = timezone.make_aware(parse(to_date_str))
                query_dict["time__lte"] = to_date

            if from_date and to_date and from_date > to_date:
                raise ValidationError("From must be before to date.")
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
    queryset = DataSet.objects.all()

    serializer_class = PriceListSerializer
