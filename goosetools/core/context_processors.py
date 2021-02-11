from django.conf import settings  # import the settings file

from goosetools.tenants.models import Client


def setting_vars(request):
    tenant = Client.objects.get(name="public")
    login_url = tenant.reverse(request, "discord_login")
    return {
        "GOOSEFLOCK_FEATURES": settings.GOOSEFLOCK_FEATURES,
        "SITE_NAME": settings.SITE_NAME,
        "LOGIN_URL": login_url,
    }
