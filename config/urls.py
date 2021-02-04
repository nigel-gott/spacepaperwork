"""goldengoose URL Configuration
"""
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.urls.conf import re_path

urlpatterns = [
    re_path(
        r"^" + settings.URL_PREFIX,
        include(
            [
                path("admin/", admin.site.urls),
                # TODO Namespace the apps and put them on sub urls.
                path("", include("users.urls")),
                path("", include("fleets.urls")),
                path("", include("bank.urls")),
                path("", include("items.urls")),
                path("", include("contracts.urls")),
                path("", include("market.urls")),
                path("", include("ownership.urls")),
                path("", include("core.urls")),
                path("venmo/", include("venmo.urls")),
                path("mapbot/", include("mapbot.urls")),
                path("industry/", include("industry.urls")),
                path("accounts/", include("allauth.urls")),
                path(
                    "api/", include("rest_framework.urls", namespace="rest_framework")
                ),
                path("", include("django_prometheus.urls")),
                path("tinymce/", include("tinymce.urls")),
                path("comments/", include("django_comments.urls")),
            ]
            + settings.ENV_SPECIFIC_URLS
        ),
    )
]
