"""
Base settings to build other settings files upon.
"""
import os
from decimal import ROUND_HALF_EVEN
from pathlib import Path
from typing import List

import environ
import moneyed
from django.urls.resolvers import URLResolver
from moneyed.localization import _FORMATTER

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = ROOT_DIR / "goosetools"
env = environ.Env(
    USE_NEW_VENMO_COMMANDS=(bool, False), GOOSEFLOCK_FEATURES=(bool, False)
)

env.read_env(str(ROOT_DIR / ".env"))

GOOSEFLOCK_FEATURES = env("GOOSEFLOCK_FEATURES")
# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(ROOT_DIR / "locale")]

SITE_ID = env("SITE_ID")
SECRET_KEY = env("SECRET_KEY")
URL_PREFIX = env("URL_PREFIX", default="")

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    # read os.environ['DATABASE_URL'] and raises ImproperlyConfigured exception if not found
    "default": env.db(engine="django_tenants.postgresql_backend"),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DBBACKUP_CONNECTOR_MAPPING = {
    "django_tenants.postgresql_backend": "dbbackup.db.postgresql.PgDumpConnector"
}
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
PUBLIC_SCHEMA_URLCONF = "config.public_urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
GOOSEFLOCK_APPS = [
    "goosetools.mapbot.apps.MapBotConfig",
    "goosetools.venmo.apps.VenmoConfig",
    "goosetools.industry.apps.IndustryConfig",
]

SHARED_APPS = [
    "django_tenants",  # mandatory
    "dal",
    "dal_select2",
    "goosetools.tenants.apps.TenantsConfig",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.admin",
    "django.forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.discord",
]

TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    "django.contrib.contenttypes",
    "django_extensions",
    "djmoney",
    "timezone_field",
    "materializecssform",
    "dbbackup",
    "rest_framework",
    "django_fsm",
    "django_prometheus",
    "tinymce",
    "django_comments",
    # your tenant-specific apps
    "goosetools.users.apps.UsersConfig",
    "goosetools.items.apps.ItemsConfig",
    "goosetools.fleets.apps.FleetsConfig",
    "goosetools.bank.apps.BankConfig",
    "goosetools.market.apps.MarketConfig",
    "goosetools.pricing.apps.PricingConfig",
    "goosetools.contracts.apps.ContractsConfig",
    "goosetools.ownership.apps.OwnershipConfig",
    "goosetools.core.apps.CoreConfig",
    "goosetools.goose_comments.apps.GooseCommentsConfig",
    "goosetools.user_forms.apps.UserFormsConfig",
]

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
if GOOSEFLOCK_FEATURES:
    TENANT_APPS = TENANT_APPS + GOOSEFLOCK_APPS
else:
    TENANT_SUBFOLDER_PREFIX = "t"
INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

COMMENTS_APP = "goosetools.goose_comments"

TENANT_MODEL = "tenants.Client"  # app.Model

TENANT_DOMAIN_MODEL = "tenants.Domain"  # app.Model


# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login via discord
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "tenants.SiteUser"

# django-allauth
# ------------------------------------------------------------------------------
# All Auth Social Login Config
# Replace the standard sign in form with our own with custom fields
SOCIALACCOUNT_FORMS = {"signup": "goosetools.users.forms.SignupFormWithTimezone"}
# We are identifying users based off their discord id soley so we don't need email
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "username"
SOCIALACCOUNT_AUTO_SIGNUP = True
# Override forms we want to disable in a discord auth only workflow
# See: https://github.com/pennersr/django-allauth/issues/345
ACCOUNT_FORMS = {
    "add_email": "config.forms.AddEmailForm",
    "change_password": "config.forms.ChangePasswordForm",
    "set_password": "config.forms.SetPasswordForm",
    "reset_password": "config.forms.ResetPasswordForm",
}
# Setup custom adapters to properly create the custom GooseUser and disable normal sign up
ACCOUNT_ADAPTER = "goosetools.users.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "goosetools.users.adapters.SocialAccountAdapter"
SOCIALACCOUNT_PROVIDERS = {
    "discord": {
        # Restrict down to the minimum scope to identify the user.
        # We don't need their email so don't ask to increase privacy.
        "SCOPE": ["identify"]
    }
}

ACCOUNT_LOGOUT_REDIRECT_URL = "tenants:splash"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "tenants:splash"
# LOGIN_REDIRECT_URL = 'fleet'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

ACCOUNT_EMAIL_VERIFICATION = "none"

LOGIN_REQUIRED_IGNORE_VIEW_NAMES = [
    "discord_login",
    "account_signup",
    "account_login",
    "discord_callback",
    "account_logout",
    "tenants:splash",
]
LOGIN_REQUIRED_UNAPPROVED_USER_REDIRECT = "tenants:splash"

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
if GOOSEFLOCK_FEATURES:
    MIDDLEWARE = ["django_tenants.middleware.main.TenantMainMiddleware"]
else:
    MIDDLEWARE = ["django_tenants.middleware.TenantSubfolderMiddleware"]
MIDDLEWARE = MIDDLEWARE + [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "goosetools.users.middleware.LoginAndApprovedUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # TODO Setup email and enable this to notify admins when there are broken links.
    # "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.TimezoneMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = os.path.join(ROOT_DIR, "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

ENV_SPECIFIC_URLS: List[URLResolver] = []

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR / "templates"), str(APPS_DIR / "templates" / "allauth")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "goosetools.core.context_processors.setting_vars",
            ],
        },
    }
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
# https://docs.djangoproject.com/en/3.1/ref/forms/renderers/#djangotemplates
# "If you want to render templates with customizations from your TEMPLATES setting,
# such as context processors for example, use the TemplatesSetting renderer."
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

# Money Setup
# ------------------------------------------------------------------------------
EEI = moneyed.add_currency(
    code="EEI", numeric="068", name="Eve Echoes ISK", countries=("CHINA",)
)

# Currency Formatter will output 2.000,00 Bs.
_FORMATTER.add_sign_definition("default", EEI, prefix=u"Ƶ ")

_FORMATTER.add_formatting_definition(
    "es_BO",
    group_size=3,
    group_separator=",",
    decimal_point=".",
    positive_sign="",
    trailing_positive_sign="",
    negative_sign="-",
    trailing_negative_sign="",
    rounding_method=ROUND_HALF_EVEN,
)

CURRENCIES = ["EEI"]

# DB Backup
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": env("DB_BACKUP_LOCATION")}

REST_FRAMEWORK = {
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M",
}

PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(8001, 8050)
PROMETHEUS_METRICS_EXPORT_ADDRESS = ""

VENMO_HOST_URL = env("VENMO_HOST_URL")
VENMO_BASE_PATH = env("VENMO_BASE_PATH")
VENMO_API_TOKEN = env("VENMO_API_TOKEN")
USE_NEW_VENMO_COMMANDS = env("USE_NEW_VENMO_COMMANDS")
BOT_TOKEN = env("BOT_TOKEN")
SITE_NAME = env("SITE_NAME", default="GooseTools")
LOGIN_URL = env("LOGIN_URL", default="/accounts/discord/login/")
DISCORD_OAUTH_URL = env("DISCORD_OAUTH_URL")
DISCORD_OAUTH_URL_WITHOUT_MANAGE = env("DISCORD_OAUTH_URL_WITHOUT_MANAGE")
BOT_USER_ID = env("BOT_USER_ID")
