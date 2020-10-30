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
    path('loot_share/<int:pk>/plus/', loot_share_plus, name='loot_share_plus'),
    path('loot_share/<int:pk>/minus/', loot_share_minus, name='loot_share_minus'),
    path('loot_group/<int:lg_pk>/item/create', item_add, name='item_add'),
    path('item/move/all', item_move_all, name='item_move_all'),
    path('stack/<int:pk>/sell', stack_sell, name='stack_sell'),
    path('stack/<int:pk>/change_price', stack_change_price, name='stack_change_price'),
    path('stack/<int:pk>/sold', stack_sold, name='stack_sold'),
    path('stack/<int:pk>/view', stack_view, name='stack_view'),
    path('stack/<int:pk>/delete', stack_delete, name='stack_delete'),
    path('item/<int:pk>/sell', item_sell, name='item_sell'),
    path('item/<int:pk>/edit', item_edit, name='item_edit'),
    path('item/<int:pk>/delete', item_delete, name='item_delete'),
    path('item/<int:pk>/', item_view, name='item_view'),
    path('order/<int:pk>/edit', edit_order_price, name='edit_order_price'),
    path('order/<int:pk>/sold', order_sold, name='order_sold'),
    path('item/<int:pk>/plus/', item_plus, name='item_plus'),
    path('item/<int:pk>/minus/', item_minus, name='item_minus'),
    path('item/', items, name='items'),
    path('loc/<int:pk>/stack/all/', stack_items, name='stack_items'),
    path('item/all/', all_items, name='all_items'),
    path('item/grouped/', items_grouped, name='grouped_items'),
    path('contracts/', contracts, name='contracts'),
    path('contract/create/', contracts, name='create_contract'),
    path('contract/create/fleet/<int:fleet_pk>/<int:loc_pk>/', create_contract_for_fleet, name='item_contract_fleet'),
    path('contract/create/loc/<int:pk>/', create_contract_for_loc, name='contract_items_in_loc'),
    path('contract/create/item/<int:pk>/', create_contract_item, name='item_contract'),
    path('contract/<int:pk>/view', view_contract, name='view_contract'),
    path('contract/<int:pk>/reject', reject_contract, name='reject_contract'),
    path('contract/<int:pk>/accept', accept_contract, name='accept_contract'),
    path('contract/<int:pk>/edit', contracts, name='edit_contract'),
    path('contract/<int:pk>/delete', contracts, name='delete_contract'),
    path('fleet_shares/all/', all_fleet_shares, name='all_fleet_shares'),
    path('fleet_shares/', your_fleet_shares, name='your_fleet_shares'),
    path('fleet_shares/<int:pk>/', fleet_shares, name='fleet_shares'),
    path('orders/', orders, name='orders'),
    path('sold/', sold, name='sold'),
    path('junk/', junk, name='junk'),
    path('deposit_eggs/', deposit_eggs, name='deposit_eggs'),
    path('deposit_approved/', deposit_approved, name='deposit_approved'),
    path('transfer_eggs/', transfer_eggs, name='transfer_eggs'),
    path('transfered/', transfered_items, name='transfered_items'),
    path('transfer_log/<int:pk>/', view_transfer_log, name='view_transfer_log'),

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
    path(
        r'item-filter-group-autocomplete/',
        ItemFilterGroupAutocomplete.as_view(),
        name='item-filter-group-autocomplete',
    ),
]
