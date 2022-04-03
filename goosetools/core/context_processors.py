from django.conf import settings  # import the settings file


def setting_vars(request):
    return {
        "SINGLE_TENANT": settings.SINGLE_TENANT,
        "WIKI_NAME": settings.WIKI_NAME,
        "WIKI_URL": settings.WIKI_URL,
        "SITE_NAME": settings.SITE_NAME,
        "LOGIN_URL": settings.LOGIN_URL,
        "tenant": request.tenant,
        "PRICE_CONTACT_INFO": settings.PRICE_CONTACT_INFO,
    }
