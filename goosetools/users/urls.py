from django.urls import path
from django.urls.conf import include
from rest_framework import routers

from goosetools.users.autocomplete import CharacterAutocomplete, UsernameAutocomplete
from goosetools.users.views import (
    CharacterQuerySet,
    GooseUserQuerySet,
    admin_character_edit,
    application_update,
    character_dashboard,
    character_edit,
    character_list,
    character_new,
    character_search,
    check_discord_status,
    code_of_conduct_edit,
    corp_application_list,
    corp_application_update,
    corp_select,
    corps_list,
    discord_settings,
    edit_corp,
    edit_group,
    groups_view,
    new_corp,
    new_group,
    refresh_discord_groups,
    settings_view,
    user_admin_view,
    user_application_list,
    user_dashboard,
    user_signup,
    user_view,
)

router = routers.DefaultRouter()
router.register(r"gooseuser", GooseUserQuerySet)
router.register(r"character", CharacterQuerySet)

urlpatterns = [
    path("code_of_conduct/edit", code_of_conduct_edit, name="code_of_conduct_edit"),
    path("settings/discord/check", check_discord_status, name="check_discord_status"),
    path("settings/discord", discord_settings, name="discord_settings"),
    path("settings/", settings_view, name="settings"),
    path("user/dashboard", user_dashboard, name="user_dashboard"),
    path("character/dashboard", character_dashboard, name="character_dashboard"),
    path("user/<int:pk>", user_view, name="user_view"),
    path("user/<int:pk>/admin", user_admin_view, name="user_admin_view"),
    path(
        "characters/edit/<int:pk>/admin",
        admin_character_edit,
        name="admin_character_edit",
    ),
    path("characters/edit/<int:pk>", character_edit, name="character_edit"),
    path("corp/select/", corp_select, name="corp_select"),
    path("corp/<int:pk>/apply/", user_signup, name="user_signup"),
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
    path("api/", include(router.urls)),
    path("corps/", corps_list, name="corps_list"),
    path("corps/<int:pk>/edit", edit_corp, name="edit_corp"),
    path("corps/new", new_corp, name="new_corp"),
    path("groups/", groups_view, name="groups_view"),
    path("groups/<int:pk>/edit", edit_group, name="edit_group"),
    path("groups/new", new_group, name="new_group"),
    path(
        "groups/refresh_discord", refresh_discord_groups, name="refresh_discord_groups"
    ),
]
