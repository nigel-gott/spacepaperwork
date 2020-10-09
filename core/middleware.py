import pytz

from django.utils import timezone

from django.contrib import auth
import logging

logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = auth.get_user(request)
        tzname = user.timezone
        if tzname:
            timezone.activate(tzname)
        else:
            timezone.deactivate()
        return self.get_response(request)
