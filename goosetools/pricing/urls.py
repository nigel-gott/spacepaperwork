from django.urls import path
from django.urls.conf import include
from rest_framework import routers

from goosetools.pricing.views import (
    PriceListDeleteView,
    PriceListDetailView,
    PriceListQuerySet,
    PriceListUpdateView,
    pricing_dashboard,
)

router = routers.DefaultRouter()
router.register(r"pricelist", PriceListQuerySet)

app_name = "pricing"


urlpatterns = [
    path("api/", include(router.urls)),
    path("dashboard", pricing_dashboard, name="pricing_dashboard"),
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
]
