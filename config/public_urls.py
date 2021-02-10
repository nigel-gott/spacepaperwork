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
                path("", include("tenants.urls")),
                path("accounts/", include("allauth.urls")),
            ]
            + settings.ENV_SPECIFIC_URLS
        ),
    )
]
