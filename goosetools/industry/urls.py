from django.urls import path
from django.urls.conf import include
from rest_framework import routers

from goosetools.industry.views import (
    ShipOrderViewSet,
    ShipViewSet,
    edit_olg,
    edit_ship,
    new_olg,
    new_ship,
    olg_list,
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
    path("admin/olg", olg_list, name="olg_list"),
    path("admin/olg/new", new_olg, name="new_olg"),
    path("admin/olg/<int:pk>/edit", edit_olg, name="edit_olg"),
    path("admin/ship/new", new_ship, name="new_ship"),
    path("admin/ship/<int:pk>/edit", edit_ship, name="edit_ship"),
    path("admin/ships", ship_dashboard, name="ship_dashboard"),
    path("shiporder/", include((router.urls))),
]
