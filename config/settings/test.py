import debug_toolbar
from django.conf.urls import include
from django.urls.conf import path

# pylint: disable=unused-wildcard-import,wildcard-import
from .base import *
from .base import env

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
INTERNAL_IPS = ["127.0.0.1"]

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "django"]


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}
SECRET_KEY = env.str(
    "DJANGO_SECRET_KEY",
    default="!!!STUB DJANGO_SECRET_KEY FOR TEST ONLY!!!",
)

STUB_DISCORD = env.bool("STUB_DISCORD", True)

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa

ENV_SPECIFIC_URLS = [
    path("__debug__/", include(debug_toolbar.urls)),
]

if STUB_DISCORD:
    ENV_SPECIFIC_URLS.append(
        path("stub_discord_auth/", include("stub_discord_auth.urls")),
    )
    SHARED_APPS.append("goosetools.stub_discord_auth.apps.StubDiscordAuthConfig")
    INSTALLED_APPS.append("goosetools.stub_discord_auth.apps.StubDiscordAuthConfig")

if env.bool("USE_DOCKER", default=False):
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

LOGIN_REQUIRED_IGNORE_VIEW_NAMES = LOGIN_REQUIRED_IGNORE_VIEW_NAMES + [
    "authorize_url",
    "access_token_url",
    "profile_url",
    "set_uid",
]

URL_PREFIX = ""
SINGLE_TENANT = True
