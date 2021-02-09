import re
import sys

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http.response import HttpResponseRedirect
from django.urls import resolve
from django.urls.base import reverse

from goosetools.users.models import BASIC_ACCESS, LOOT_TRACKER, SHIP_ORDERER

IGNORE_PATHS = [re.compile(settings.LOGIN_URL)]
IGNORE_PATHS += [
    re.compile(url) for url in getattr(settings, "LOGIN_REQUIRED_IGNORE_PATHS", [])
]

IGNORE_VIEW_NAMES = getattr(settings, "LOGIN_REQUIRED_IGNORE_VIEW_NAMES", [])

APPROVED_IGNORE = [
    "user_signup",
    "corp_select",
    "core:splash",
    "core:home",
    "core:conduct",
] + IGNORE_VIEW_NAMES

UNAPPROVED_REDIRECT_VIEW = getattr(
    settings, "LOGIN_REQUIRED_UNAPPROVED_USER_REDIRECT", "discord_login"
)

APP_TO_PERMISSION_CONFIG = {
    "fleets": LOOT_TRACKER,
    "items": LOOT_TRACKER,
    "market": LOOT_TRACKER,
    "ownership": LOOT_TRACKER,
    "pricing": LOOT_TRACKER,
    "bank": LOOT_TRACKER,
    "contracts": LOOT_TRACKER,
    "industry": SHIP_ORDERER,
}


def _user_is_unapproved(user):
    return (
        not user.has_gooseuser()
        or not user.gooseuser.is_approved()
        or not user.gooseuser.has_perm(BASIC_ACCESS)
    )


# pylint: disable=inconsistent-return-statements
def _redirect_unapproved_user_to_splash_or_home_if_not_visiting_whitelist(request):
    resolver = resolve(request.path)
    views = ((name == resolver.view_name) for name in APPROVED_IGNORE)
    if not any(views):
        messages.error(request, "You are not yet approved and cannot access this page.")
        if not request.user.has_gooseuser():
            return HttpResponseRedirect(reverse("core:splash"))
        else:
            return HttpResponseRedirect(reverse("core:home"))
    return


# pylint: disable=inconsistent-return-statements
def _redirect_approved_user_to_home_if_not_permitted(request):
    # TODO set app_name in all app modules so we can instead just do (resolve(request.path).app_name) instead of this madness.
    app_name = sys.modules[resolve(request.path_info).func.__module__].__package__
    if app_name in APP_TO_PERMISSION_CONFIG:
        required_permission = APP_TO_PERMISSION_CONFIG[app_name]
        if not request.gooseuser.has_perm(required_permission):
            print(
                f"Failed for {app_name} and {required_permission} for {request.gooseuser.groups}"
            )
            messages.error(request, "You do not have permission to view this page.")
            return HttpResponseRedirect(reverse("core:home"))
    return


# pylint: disable=inconsistent-return-statements
def _redirect_unauthed_user_to_discord_login_if_not_visiting_whitelist(request):
    resolver = resolve(request.path)
    views = ((name == resolver.view_name) for name in IGNORE_VIEW_NAMES)

    if not any(views) and not any(url.match(request.path) for url in IGNORE_PATHS):
        return HttpResponseRedirect(reverse("discord_login"))


class LoginAndApprovedUserMiddleware(AuthenticationMiddleware):
    # pylint: disable=unused-argument,no-self-use
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.gooseuser = (
            hasattr(request.user, "gooseuser") and request.user.gooseuser
        )
        if request.user.is_authenticated:
            if _user_is_unapproved(request.user):
                return _redirect_unapproved_user_to_splash_or_home_if_not_visiting_whitelist(
                    request
                )
            else:
                return _redirect_approved_user_to_home_if_not_permitted(request)
        else:
            return _redirect_unauthed_user_to_discord_login_if_not_visiting_whitelist(
                request
            )
