from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


def core_splash(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("core:home"))
    else:
        return render(
            request,
            "core/splash.html",
        )


def core_home(request):
    return render(
        request,
        "core/home.html",
    )


def core_conduct(request):
    return render(
        request,
        "core/conduct.html",
    )


def core_handler500(request):
    return render(request, "core/500.html", status=500)
