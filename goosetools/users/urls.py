from django.urls import path

from goosetools.users.autocomplete import (
    CharacterAutocomplete,
    DiscordUsernameAutocomplete,
)
from goosetools.users.views import settings_view

urlpatterns = [
    path("settings/", settings_view, name="settings"),
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
