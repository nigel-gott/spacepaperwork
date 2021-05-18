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

# The root of this projects git repo
ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# All apps are kept in the goosetools folder following the pattern found in the cookie
# cutter django project (https://github.com/pydanny/cookiecutter-django/tree/master/%7B%7Bcookiecutter.project_slug%7D%7D)
APPS_DIR = ROOT_DIR / "goosetools"

env = environ.Env()

# Read in the env file located in the project root called ".env" first to populate
# any variables below before checking the set environment variables.
env.read_env(str(ROOT_DIR / ".env"))

# Set SINGLE_TENANT to True if you want only one organization to use your deployment of
# spacepaperwork.
# When True new tenant sign up is disabled and url conf is changed so the single tenant
# can just be reached at / . Architecturally this variable does not disable the fact
# that spacepaperwork is multi-tenant under the hood.
SINGLE_TENANT = env.bool("SINGLE_TENANT", default=False)
VAR_ROOT = env.str("VAR_ROOT", default="/var/")
WITHDRAW_INGAME_CHAR = env.str("WITHDRAW_INGAME_CHAR", default="a corp admin")
PRONOUN_ROLES = env.bool("PRONOUN_ROLES", default=False)
PRONOUN_THEY_DISCORD_ROLE = env.str("PRONOUN_THEY_DISCORD_ROLE", default=None)
PRONOUN_SHE_DISCORD_ROLE = env.str("PRONOUN_SHE_DISCORD_ROLE", default=None)
PRONOUN_HE_DISCORD_ROLE = env.str("PRONOUN_HE_DISCORD_ROLE", default=None)
WIKI_NAME = env.str("WIKI_NAME", default=None)
WIKI_URL = env.str("WIKI_URL", default=None)
SHARING_BASE_URL = env.str("SHARING_BASE_URL", default="http://localhost")
SHIP_PRICE_GOOGLE_SHEET_ID = env.str("SHIP_PRICE_GOOGLE_SHEET_ID", default=None)
SHIP_PRICE_GOOGLE_SHEET_CELL_RANGE = env.str(
    "SHIP_PRICE_GOOGLE_SHEET_CELL_RANGE", default=None
)
RUN_WEEKLY_MARKET_DATA_FULL_SYNC = env.bool(
    "RUN_WEEKLY_MARKET_DATA_FULL_SYNC", default=False
)
# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(ROOT_DIR / "locale")]

SITE_ID = env.int("SITE_ID", default=1)
URL_PREFIX = env.str("URL_PREFIX", default="")

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

SHARED_APPS = [
    "django_tenants",  # mandatory
    "dal",
    "dal_select2",
    "goosetools.tenants.apps.TenantsConfig",
    "goosetools.global_items.apps.GlobalItemsConfig",
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
    "django_cron",
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
    "mptt",
    "hordak",
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
    "goosetools.notifications.apps.NotificationsConfig",
    "goosetools.venmo.apps.VenmoConfig",
    "goosetools.mapbot.apps.MapBotConfig",
    "goosetools.industry.apps.IndustryConfig",
    "goosetools.discord_bot.apps.DiscordBotConfig",
]

if not SINGLE_TENANT:
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
    "tenants:about",
    "tenants:privacy",
    "tenants:help",
    "tenants:pricing",
    "tenants:login_cancelled",
    "socialaccount_login_cancelled",
]
LOGIN_REQUIRED_UNAPPROVED_USER_REDIRECT = "tenants:splash"

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
if SINGLE_TENANT:
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
    "config.middleware.LocaleMiddleware",
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
DBBACKUP_STORAGE_OPTIONS = {
    "location": env.str("DB_BACKUP_LOCATION", default=ROOT_DIR / "dbbackups")
}

REST_FRAMEWORK = {
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M",
}

VENMO_HOST_URL = env.str("VENMO_HOST_URL", default=None)
VENMO_BASE_PATH = env.str("VENMO_BASE_PATH", default=None)
VENMO_API_TOKEN = env.str("VENMO_API_TOKEN", default=None)
BOT_TOKEN = env.str("BOT_TOKEN", default=None)
SITE_NAME = env.str("SITE_NAME", default="GooseTools")
LOGIN_URL = env.str("LOGIN_URL", default="/accounts/discord/login/")
DISCORD_OAUTH_URL = env.str("DISCORD_OAUTH_URL", default=None)
DISCORD_OAUTH_URL_WITHOUT_MANAGE = env.str(
    "DISCORD_OAUTH_URL_WITHOUT_MANAGE", default=None
)
BOT_USER_ID = env.str("BOT_USER_ID", default=None)

HORDAK_DECIMAL_PLACES = 0
HORDAK_MAX_DIGITS = 16

CRON_CLASSES = [
    "goosetools.industry.cron.lookup_ship_prices.LookupShipPrices",
    "goosetools.industry.cron.cleanup_old_orders.CleanUpOldOrders",
    "goosetools.market.cron.get_market_data.GetMarketData",
    "goosetools.users.cron.update_discord_roles.UpdateDiscordRoles",
    "goosetools.fleets.cron.repeat_groups.RepeatGroups",
]

if RUN_WEEKLY_MARKET_DATA_FULL_SYNC:
    CRON_CLASSES.append(
        "goosetools.market.cron.sync_past_market_data.SyncPastMarketData"
    )
