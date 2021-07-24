from django.urls import path
from django.urls.conf import include
from rest_framework import routers

from goosetools.pricing.views import (
    PriceListCreateView,
    PriceListDeleteView,
    PriceListDetailView,
    PriceListUpdateView,
    pricing_dashboard,
    pricing_data_dashboard,
)
from goosetools.pricing.viewsets import (
    ItemMarketDataEventViewSet,
    LatestItemMarketDataEventViewSet,
    PriceListViewSet,
)

router = routers.DefaultRouter()
router.register(r"pricelist", PriceListViewSet)
router.register(r"itemprice", ItemMarketDataEventViewSet)
router.register(r"latest_itemprice", LatestItemMarketDataEventViewSet)

app_name = "pricing"


urlpatterns = [
    path("api/", include(router.urls)),
    path("pricing_dashboard/", pricing_dashboard, name="pricing_dashboard"),
    path(
        "pricing_data_dashboard/", pricing_data_dashboard, name="pricing_data_dashboard"
    ),
    path(
        "pricelist/<int:pk>/update/",
        PriceListUpdateView.as_view(),
        name="pricelist-update",
    ),
    path(
        "pricelist/<int:pk>/delete/",
        PriceListDeleteView.as_view(),
        name="pricelist-delete",
    ),
    path(
        "pricelist/<int:pk>/",
        PriceListDetailView.as_view(),
        name="pricelist-detail",
    ),
    path(
        "pricelist/create/",
        PriceListCreateView.as_view(),
        name="pricelist-create",
    ),
]
