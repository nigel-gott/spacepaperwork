import logging

import pytz
from django.contrib import auth
from django.utils import timezone

from core.models import GooseUser

logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user: GooseUser = auth.get_user(request)  # type: ignore
        if hasattr(user, "timezone"):
            tzname = user.timezone
        else:
            tzname = pytz.timezone("UTC")
        if tzname:
            timezone.activate(tzname)
        else:
            timezone.deactivate()
        return self.get_response(request)
