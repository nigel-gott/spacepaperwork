from django.urls import include, path
from rest_framework import routers

from goosetools.items.autocomplete import (
    ItemAutocomplete,
    ItemSubSubTypeAutocomplete,
    ItemSubTypeAutocomplete,
    ItemTypeAutocomplete,
    SystemAutocomplete,
)
from goosetools.items.querysets import ItemDbQuerySet
from goosetools.items.views import (
    ItemChangeProposalList,
    all_items,
    approve_item_change,
    create_item_change,
    create_item_change_for_item,
    delete_item_change,
    item_data,
    item_db,
    item_delete,
    item_edit,
    item_minus,
    item_plus,
    item_view,
    items_grouped,
    items_view,
    junk,
    junk_item,
    junk_items,
    junk_stack,
    select_create_item_change,
    stack_delete,
    stack_items,
    stack_view,
    unjunk_item,
    update_item_change,
)

router = routers.DefaultRouter()
router.register(r"item_db", ItemDbQuerySet)

urlpatterns = [
    path("stack/<int:pk>/junk", junk_stack, name="junk_stack"),
    path("stack/<int:pk>/view", stack_view, name="stack_view"),
    path("stack/<int:pk>/delete", stack_delete, name="stack_delete"),
    path("junk/<int:pk>/unjunk", unjunk_item, name="unjunk_item"),
    path("item_type/<str:pk>/data", item_data, name="item_data"),
    path("item/<int:pk>/junk", junk_item, name="junk_item"),
    path("item/<int:pk>/edit", item_edit, name="item_edit"),
    path("item/<int:pk>/delete", item_delete, name="item_delete"),
    path("item/<int:pk>/", item_view, name="item_view"),
    path("item/<int:pk>/plus/", item_plus, name="item_plus"),
    path("item/<int:pk>/minus/", item_minus, name="item_minus"),
    path("item/", items_view, name="items"),
    path("loc/<int:pk>/junk/all/", junk_items, name="junk_items"),
    path("loc/<int:pk>/stack/all/", stack_items, name="stack_items"),
    path("item/all/", all_items, name="all_items"),
    path("item/grouped/", items_grouped, name="grouped_items"),
    path("junk/", junk, name="junk"),
    path("itemdb/", item_db, name="item_db"),
    path("api/", include(router.urls)),
    path(
        r"system-autocomplete/",
        SystemAutocomplete.as_view(),
        name="system-autocomplete",
    ),
    path(
        r"item-type-autocomplete/",
        ItemTypeAutocomplete.as_view(),
        name="item-type-autocomplete",
    ),
    path(
        r"item-sub-type-autocomplete/",
        ItemSubTypeAutocomplete.as_view(),
        name="item-sub-type-autocomplete",
    ),
    path(
        r"item-sub-sub-type-autocomplete/",
        ItemSubSubTypeAutocomplete.as_view(),
        name="item-sub-sub-type-autocomplete",
    ),
    path(r"item-autocomplete/", ItemAutocomplete.as_view(), name="item-autocomplete"),
    path("itemchange/open/", ItemChangeProposalList.as_view(), name="item-change-list"),
    path(
        "itemchange/create/",
        select_create_item_change,
        name="item-change-create-select",
    ),
    path("itemchange/create/new", create_item_change, name="item-change-create-new"),
    path(
        "itemchange/create/<int:pk>",
        create_item_change_for_item,
        name="item-change-create-for-item",
    ),
    path("itemchange/<int:pk>/update", update_item_change, name="item-change-update"),
    path(
        "itemchange/<int:pk>/approve", approve_item_change, name="item-change-approve"
    ),
    path(
        "itemchange/<int:pk>/delete/",
        delete_item_change,
        name="item-change-delete",
    ),
]
