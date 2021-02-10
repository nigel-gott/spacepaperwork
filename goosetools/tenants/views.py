from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse


def splash(request):
    if settings.GOOSEFLOCK_FEATURES:
        return HttpResponseRedirect(reverse("core:splash"))
    return render(
        request,
        "tenants/splash.html",
    )
