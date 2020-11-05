import logging
import sys

import pytz
from django.contrib import auth
from django.utils import timezone

import sys
import cProfile
from django.conf import settings
from io import StringIO

logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = auth.get_user(request)
        if hasattr(user, "timezone"):
            tzname = user.timezone
        else:
            tzname = pytz.timezone("UTC")
        if tzname:
            timezone.activate(tzname)
        else:
            timezone.deactivate()
        return self.get_response(request)


class ProfilerMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        if settings.DEBUG and "prof" in request.GET:
            self.profiler.create_stats()
            out = StringIO()
            old_stdout, sys.stdout = sys.stdout, out
            self.profiler.print_stats(1)
            sys.stdout = old_stdout
            response.content = "<pre>%s</pre>" % out.getvalue()
        return response
        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and "prof" in request.GET:
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)
