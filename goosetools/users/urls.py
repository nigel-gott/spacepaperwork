from django.urls import path
from django.urls.conf import include
from rest_framework import routers

from goosetools.users.autocomplete import CharacterAutocomplete, UsernameAutocomplete
from goosetools.users.views import (
    GooseUserQuerySet,
    application_update,
    auth_settings_view,
    character_edit,
    character_list,
    character_new,
    character_search,
    corp_application_list,
    corp_application_update,
    edit_group,
    groups_view,
    new_group,
    refresh_discord_groups,
    settings_view,
    user_application_list,
    user_dashboard,
    user_signup,
    user_view,
)

router = routers.DefaultRouter()
router.register(r"gooseuser", GooseUserQuerySet)

urlpatterns = [
    path("auth/settings/", auth_settings_view, name="auth_settings"),
    path("settings/", settings_view, name="settings"),
    path("user/dashboard", user_dashboard, name="user_dashboard"),
    path("user/<int:pk>", user_view, name="user_view"),
    path("characters/edit/<int:pk>", character_edit, name="character_edit"),
    path("users/new/", user_signup, name="user_signup"),
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
    path("gooseuser/", include((router.urls))),
    path("groups/", groups_view, name="groups_view"),
    path("groups/<int:pk>/edit", edit_group, name="edit_group"),
    path("groups/new", new_group, name="new_group"),
    path(
        "groups/refresh_discord", refresh_discord_groups, name="refresh_discord_groups"
    ),
]
