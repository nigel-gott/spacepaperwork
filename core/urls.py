from django.urls import path

from .autocomplete import *
from .views import *

urlpatterns = [
    path('', fleet, name='home'),
    path('fleet/', fleet, name='fleet'),
    path('fleet/past', fleet_past, name='fleet_past'),
    path('fleet/future', fleet_future, name='fleet_future'),
    path('settings/', settings_view, name='settings'),
    path('fleet/create/', fleet_create, name='fleet_create'),
    path('fleet/<int:pk>/', fleet_view, name='fleet_view'),
    path('fleet/<int:pk>/join/', fleet_join, name='fleet_join'),
    path('fleet/add/<int:pk>/', fleet_add, name='fleet_add'),
    path('fleet/make_admin/<int:pk>/', fleet_make_admin, name='fleet_make_admin'),
    path('fleet/remove_admin/<int:pk>/', fleet_remove_admin, name='fleet_remove_admin'),
    path('fleet/leave/<int:pk>/', fleet_leave, name='fleet_leave'),
    path('fleet/end/<int:pk>/', fleet_end, name='fleet_end'),
    path('fleet/edit/<int:pk>/', fleet_edit, name='fleet_edit'),
    path('fleet/<int:pk>/loot_group/create/', loot_group_create, name='loot_group_create'),
    path('fleet/<int:fleet_pk>/loot_group/<int:loot_bucket_pk>/create/', loot_group_add, name='loot_group_add'),
    path('loot_group/<int:pk>', loot_group_view, name='loot_group_view'),
    path('loot_group/<int:pk>/join/', loot_share_join, name='loot_share_join'),
    path('loot_group/<int:pk>/add_share/', loot_share_add, name='loot_share_add'),
    path('loot_group/<int:pk>/add_share_fleet_members/', loot_share_add_fleet_members, name='loot_share_add_fleet_members'),
    path('loot_share/<int:pk>/edit', loot_share_edit, name='loot_share_edit'),
    path('loot_share/<int:pk>/delete', loot_share_delete, name='loot_share_delete'),
    path('loot_group/<int:pk>/item/create', item_add, name='item_add'),
    path('item/<int:pk>/sell', item_sell, name='item_sell'),
    path('item/<int:pk>/edit', item_edit, name='item_edit'),
    path('item/<int:pk>/delete', item_delete, name='item_delete'),
    path('item/<int:pk>/', item_view, name='item_view'),
    path('order/<int:pk>/sold', order_sold, name='order_sold'),
    path('item/', items, name='items'),
    path('orders/', orders, name='orders'),
    path('sold/', sold, name='sold'),
    path('junk/', junk, name='junk'),

    path(
        r'character-autocomplete/',
        CharacterAutocomplete.as_view(),
        name='character-autocomplete',
    ),
    path(
        r'discord-username-autocomplete/',
        DiscordUsernameAutocomplete.as_view(),
        name='discord-username-autocomplete',
    ),
    path(
        r'system-autocomplete/',
        SystemAutocomplete.as_view(),
        name='system-autocomplete',
    ),
    path(
        r'item-autocomplete/',
        ItemAutocomplete.as_view(),
        name='item-autocomplete',
    ),
    path(
        r'item-type-autocomplete/',
        ItemTypeAutocomplete.as_view(),
        name='item-type-autocomplete',
    ),
    path(
        r'item-sub-type-autocomplete/',
        ItemSubTypeAutocomplete.as_view(),
        name='item-sub-type-autocomplete',
    ),
    path(
        r'item-sub-sub-type-autocomplete/',
        ItemSubSubTypeAutocomplete.as_view(),
        name='item-sub-sub-type-autocomplete',
    ),
]
