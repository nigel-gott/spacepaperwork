from django.urls import path

from goosetools.ownership.views import (
    completed_egg_transfers,
    fleet_shares,
    item_add,
    loot_group_add,
    loot_group_close,
    loot_group_create,
    loot_group_edit,
    loot_group_open,
    loot_group_view,
    loot_share_add,
    loot_share_add_fleet_members,
    loot_share_delete,
    loot_share_edit,
    loot_share_join,
    loot_share_minus,
    loot_share_plus,
    mark_transfer_as_done,
    transfer_eggs,
    transfered_items,
    view_transfer_log,
    your_fleet_shares,
)

urlpatterns = [
    path(
        "fleet/<int:pk>/loot_group/create/", loot_group_create, name="loot_group_create"
    ),
    path(
        "fleet/<int:fleet_pk>/loot_group/<int:loot_bucket_pk>/create/",
        loot_group_add,
        name="loot_group_add",
    ),
    path("loot_group/<int:pk>", loot_group_view, name="loot_group_view"),
    path(
        "loot_group/<int:pk>/edit",
        loot_group_edit,
        name="loot_group_edit",
    ),
    path("loot_group/<int:pk>/close/", loot_group_close, name="loot_group_close"),
    path("loot_group/<int:pk>/open/", loot_group_open, name="loot_group_open"),
    path("loot_group/<int:pk>/join/", loot_share_join, name="loot_share_join"),
    path("loot_group/<int:pk>/add_share/", loot_share_add, name="loot_share_add"),
    path(
        "loot_group/<int:pk>/add_share_fleet_members/",
        loot_share_add_fleet_members,
        name="loot_share_add_fleet_members",
    ),
    path("loot_share/<int:pk>/edit", loot_share_edit, name="loot_share_edit"),
    path("loot_share/<int:pk>/delete", loot_share_delete, name="loot_share_delete"),
    path("loot_share/<int:pk>/plus/", loot_share_plus, name="loot_share_plus"),
    path("loot_share/<int:pk>/minus/", loot_share_minus, name="loot_share_minus"),
    path("loot_group/<int:lg_pk>/item/create", item_add, name="item_add"),
    path("fleet_shares/", your_fleet_shares, name="your_fleet_shares"),
    path("fleet_shares/<int:pk>/", fleet_shares, name="fleet_shares"),
    path(
        "transfer_log/<int:pk>/all_done",
        mark_transfer_as_done,
        name="mark_transfer_as_done",
    ),
    path("transfer_eggs/", transfer_eggs, name="transfer_eggs"),
    path("transfered/", transfered_items, name="transfered_items"),
    path("transfer_log/<int:pk>/", view_transfer_log, name="view_transfer_log"),
    path(
        "completed_egg_transfers/",
        completed_egg_transfers,
        name="completed_egg_transfers",
    ),
]
