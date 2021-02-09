from django.conf import settings  # import the settings file


def setting_vars(request):
    return {
        "GOOSEFLOCK_FEATURES": settings.GOOSEFLOCK_FEATURES,
        "SITE_NAME": settings.SITE_NAME,
    }
