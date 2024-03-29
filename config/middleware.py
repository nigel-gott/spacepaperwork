import logging

import pytz
from django.contrib import auth
from django.urls import resolve
from django.utils import timezone, translation

from goosetools.users.models import SiteUser

logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TODO Move timezone upto SiteUser. Not done now as it would have to mean
        #  creating a SiteUser specific settings page?
        user: SiteUser = auth.get_user(request)
        if (
            request.tenant.name != "public"
            and hasattr(user, "has_gooseuser")
            and user.has_gooseuser()
            and hasattr(user.gooseuser, "timezone")
        ):
            tzname = user.gooseuser.timezone
        else:
            tzname = pytz.timezone("UTC")
        if tzname:
            timezone.activate(tzname)
        else:
            timezone.deactivate()
        return self.get_response(request)


class LocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language_code = translation.get_language_from_request(request)

        translation.activate(language_code)
        url_name = resolve(request.path).url_name
        request.url_name = url_name

        response = self.get_response(request)

        translation.deactivate()

        return response
