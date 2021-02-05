from django.urls import path
from django.urls.conf import include
from rest_framework import routers

from goosetools.industry.views import (
    ShipOrderViewSet,
    ShipViewSet,
    ship_dashboard,
    shiporders_contract_confirm,
    shiporders_create,
    shiporders_view,
)

app_name = "industry"


router = routers.DefaultRouter()
router.register(r"shiporder", ShipOrderViewSet)
router.register(r"ship", ShipViewSet)

urlpatterns = [
    path(
        "shiporder/<int:pk>/contract_confirm",
        shiporders_contract_confirm,
        name="shiporders_contract_confirm",
    ),
    path("shiporder/form_create", shiporders_create, name="shiporders_create"),
    path("shiporder/", shiporders_view, name="shiporders_view"),
    path("admin/ships", ship_dashboard, name="ship_dashboard"),
    path("api/", include((router.urls))),
]
