from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse

from goosetools.users.models import AuthConfig


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


def core_splash(request):
    if hasattr(request.user, "gooseuser"):
        return HttpResponseRedirect(reverse("core:home"))
    else:
        return render(
            request,
            "core/splash.html",
        )


def core_home(request):
    if (
        not hasattr(request.user, "gooseuser")
        or not request.gooseuser.is_authed_and_approved()
        and not request.gooseuser.latest_app()
    ):
        return HttpResponseRedirect(reverse("core:splash"))
    context = {}
    if not settings.SINGLE_TENANT:
        context[
            "share_url"
        ] = f"{settings.BASE_URL}{settings.TENANT_SUBFOLDER_PREFIX}/{request.tenant.name}/"

    return render(request, "core/home.html", context)


def core_help(request):
    if not hasattr(request.user, "gooseuser") or not request.gooseuser.is_approved():
        return forbidden(request)

    return render(request, "core/help.html")


def core_conduct(request):
    code_of_conduct = AuthConfig.get_active().code_of_conduct
    if code_of_conduct:
        return render(
            request,
            "core/conduct.html",
            {"code_of_conduct": code_of_conduct},
        )
    else:
        return HttpResponseRedirect(reverse("corp_select"))


def core_handler500(request):
    return render(request, "core/500.html", status=500)
