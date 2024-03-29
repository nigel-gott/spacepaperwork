# pylint: disable=unused-wildcard-import,wildcard-import
from .base import *  # noqa
from .base import env

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
USE_X_FORWARDED_HOST = env("USE_X_FORWARDED_HOST")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

# TODO: Setup and test all these https options;
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
# SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
# SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
#    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
# )
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
# SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
#  SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
#     "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
# )

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MAPBOT_HOST = "https://www.goosetools.com/mapbot"

PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(8001, 8050)
PROMETHEUS_METRICS_EXPORT_ADDRESS = ""

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # I always add this handler to facilitate separating loggings
        "log_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(VAR_ROOT, "log/goosetools/goosetools.log"),
            "maxBytes": 16777216,  # 16megabytes
            "formatter": "verbose",
        },
    },
    # you can also shortcut 'loggers' and just configure logging for EVERYTHING at once
    "root": {"handlers": ["console", "log_file"], "level": "INFO"},
}
