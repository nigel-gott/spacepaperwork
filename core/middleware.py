import logging
import sys

import pytz
from django.contrib import auth
from django.utils import timezone

logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = auth.get_user(request)
        if hasattr(user, 'timezone'):
            tzname = user.timezone
        else:
            tzname = pytz.timezone('UTC')
        if tzname:
            timezone.activate(tzname)
        else:
            timezone.deactivate()
        print(f"timezone = {timezone.now()}", file=sys.stderr)
        return self.get_response(request)

