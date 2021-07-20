import debug_toolbar
from django.conf.urls import include
from django.urls.conf import path

# pylint: disable=unused-wildcard-import,wildcard-import
from .base import *
from .base import env

SECRET_KEY = env("SECRET_KEY")

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
INTERNAL_IPS = ["127.0.0.1"]

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "django"]

MAPBOT_HOST = "http://localhost:5000"

GRAPH_MODELS = {"all_applications": True, "group_models": True}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

STUB_DISCORD = env.bool("STUB_DISCORD", default=False)

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

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

LOGIN_REQUIRED_IGNORE_VIEW_NAMES = LOGIN_REQUIRED_IGNORE_VIEW_NAMES + [
    "authorize_url",
    "access_token_url",
    "profile_url",
    "set_uid",
]
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "local-cache",
    }
}
