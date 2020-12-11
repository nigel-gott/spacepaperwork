import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http.response import HttpResponseRedirect
from django.urls import resolve
from django.urls.base import reverse

IGNORE_PATHS = [re.compile(settings.LOGIN_URL)]
IGNORE_PATHS += [
    re.compile(url) for url in getattr(settings, "LOGIN_REQUIRED_IGNORE_PATHS", [])
]

IGNORE_VIEW_NAMES = getattr(settings, "LOGIN_REQUIRED_IGNORE_VIEW_NAMES", [])

APPROVED_IGNORE = ["core:home", "settings"] + IGNORE_VIEW_NAMES

UNAPPROVED_REDIRECT_VIEW = getattr(
    settings, "LOGIN_REQUIRED_UNAPPROVED_USER_REDIRECT", "discord_login"
)


class LoginAndApprovedUserMiddleware(AuthenticationMiddleware):
    # pylint: disable=unused-argument,no-self-use,inconsistent-return-statements
    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path
        if request.user.is_authenticated:
            if not request.user.is_approved():
                resolver = resolve(path)
                views = ((name == resolver.view_name) for name in APPROVED_IGNORE)
                if not any(views):
                    print("failed for " + resolver.view_name)
                    messages.error(
                        request, "You are not yet approved and cannot access this page."
                    )
                    return HttpResponseRedirect(reverse("core:home"))
            return

        resolver = resolve(path)
        views = ((name == resolver.view_name) for name in IGNORE_VIEW_NAMES)

        if not any(views) and not any(url.match(path) for url in IGNORE_PATHS):
            return HttpResponseRedirect(reverse("core:splash"))
