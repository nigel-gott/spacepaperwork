from django.urls import path

from goosetools.contracts.views import (
    accept_contract,
    cancel_contract,
    contracts,
    create_contract_for_fleet,
    create_contract_for_loc,
    create_contract_item,
    item_move_all,
    reject_contract,
    view_contract,
)

urlpatterns = [
    path("contracts/", contracts, name="contracts"),
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
    path("contract/<int:pk>/view", view_contract, name="view_contract"),
    path("contract/<int:pk>/reject", reject_contract, name="reject_contract"),
    path("contract/<int:pk>/accept", accept_contract, name="accept_contract"),
    path("contract/<int:pk>/cancel", cancel_contract, name="cancel_contract"),
    path("item/move/all", item_move_all, name="item_move_all"),
]
