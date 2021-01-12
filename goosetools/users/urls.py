from django.urls import path

from goosetools.users.autocomplete import CharacterAutocomplete, UsernameAutocomplete
from goosetools.users.views import (
    application_update,
    character_edit,
    character_list,
    character_new,
    character_search,
    corp_application_list,
    corp_application_update,
    settings_view,
    user_application_list,
    user_view,
)

urlpatterns = [
    path("settings/", settings_view, name="settings"),
    path("user/<int:pk>", user_view, name="user_view"),
    path("characters/edit/<int:pk>", character_edit, name="character_edit"),
    path("characters/new/", character_new, name="character_new"),
    path("characters/", character_list, name="characters"),
    path("characters/search", character_search, name="character_search"),
    path("applications/", user_application_list, name="applications"),
    path("applications/corp", corp_application_list, name="corp_applications"),
    path(
        "applications/update/<int:pk>/", application_update, name="application_update"
    ),
    path(
        "applications/update/corp/<int:pk>/",
        corp_application_update,
        name="corp_application_update",
    ),
    path(
        r"character-autocomplete/",
        CharacterAutocomplete.as_view(),
        name="character-autocomplete",
    ),
    path(
        r"username-autocomplete/",
        UsernameAutocomplete.as_view(),
        name="username-autocomplete",
    ),
]
