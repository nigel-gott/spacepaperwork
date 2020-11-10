"""goldengoose URL Configuration
"""
import debug_toolbar
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.conf import settings

urlpatterns = [
    url(
        r"^goosetools/",
        include(
            [
                path("admin/", admin.site.urls),
                path("", include("core.urls")),
                path("accounts/", include("allauth.urls")),
            ]
            + settings.ENV_SPECIFIC_URLS
        ),
    ),
]
