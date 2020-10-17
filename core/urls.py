from django.urls import path

from .autocomplete import *
from .views import *

urlpatterns = [
    path('', fleet, name='home'),
    path('fleet/', fleet, name='fleet'),
    path('fleet/past', fleet_past, name='fleet_past'),
    path('fleet/future', fleet_future, name='fleet_future'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('fleet/create/', fleet_create, name='fleet_create'),
    path('fleet/<int:pk>/', fleet_view, name='fleet_view'),
    path('fleet/join/<int:pk>/', fleet_join, name='fleet_join'),
    path('fleet/add/<int:pk>/', fleet_add, name='fleet_add'),
    path('fleet/make_admin/<int:pk>/', fleet_make_admin, name='fleet_make_admin'),
    path('fleet/remove_admin/<int:pk>/', fleet_remove_admin, name='fleet_remove_admin'),
    path('fleet/leave/<int:pk>/', fleet_leave, name='fleet_leave'),
    path('fleet/end/<int:pk>/', fleet_end, name='fleet_end'),
    path('fleet/edit/<int:pk>/', fleet_edit, name='fleet_edit'),
    path('fleet/<int:pk>/loot_group/create/', loot_group_create, name='loot_group_create'),
    path('loot_group/<int:pk>', loot_group_view, name='loot_group_view'),
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
]
