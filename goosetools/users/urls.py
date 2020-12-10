from django.urls import path

from goosetools.users.autocomplete import (
    CharacterAutocomplete,
    DiscordUsernameAutocomplete,
)
from goosetools.users.views import (
    UserApplicationListView,
    application_update,
    settings_view,
)

urlpatterns = [
    path("settings/", settings_view, name="settings"),
    path("applications/", UserApplicationListView.as_view(), name="applications"),
    path(
        "applications/update/<int:pk>/", application_update, name="application_update"
    ),
    path(
        r"character-autocomplete/",
        CharacterAutocomplete.as_view(),
        name="character-autocomplete",
    ),
    path(
        r"discord-username-autocomplete/",
        DiscordUsernameAutocomplete.as_view(),
        name="discord-username-autocomplete",
    ),
]
