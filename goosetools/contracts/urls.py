from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from goosetools.contracts.views import (
    ContractQuerySet,
    accept_contract,
    cancel_contract,
    contract_dashboard,
    contracts,
    create_contract_for_fleet,
    create_contract_for_loc,
    create_contract_item,
    create_contract_item_stack,
    item_move_all,
    pending_contract,
    reject_contract,
    view_contract,
)

router = routers.DefaultRouter()
router.register(r"contract", ContractQuerySet)

urlpatterns = [
    path("contract/dashboard", contract_dashboard, name="contracts"),
    path("contract/create/", contracts, name="create_contract"),
    path(
        "contract/create/fleet/<int:fleet_pk>/<int:loc_pk>/",
        create_contract_for_fleet,
        name="item_contract_fleet",
    ),
    path(
        "contract/create/loc/<int:pk>/",
        create_contract_for_loc,
        name="contract_items_in_loc",
    ),
    path("contract/create/item/<int:pk>/", create_contract_item, name="item_contract"),
    path(
        "contract/create/item_stack/<int:pk>/",
        create_contract_item_stack,
        name="item_contract_stack",
    ),
    path("contract/<int:pk>/view", view_contract, name="view_contract"),
    path("contract/<int:pk>/reject", reject_contract, name="reject_contract"),
    path("contract/<int:pk>/accept", accept_contract, name="accept_contract"),
    path("contract/<int:pk>/cancel", cancel_contract, name="cancel_contract"),
    path("contract/<int:pk>/pending", pending_contract, name="pending_contract"),
    path("item/move/all", item_move_all, name="item_move_all"),
    path("api/", include(router.urls)),
]
