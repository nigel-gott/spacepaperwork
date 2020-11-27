from typing import Any, Dict, List

from django.contrib.messages.api import get_messages
from django.http.response import HttpResponse
from django.test import TestCase


class DjangoTestCase(TestCase):
    @staticmethod
    def get_errors_from_response(response: HttpResponse) -> List[str]:
        return [
            m.message
            for m in list(get_messages(response.wsgi_request))
            if m.level_tag == "error"
        ]

    def assert_no_error_messages(self, response: HttpResponse):
        self.assertEqual(self.get_errors_from_response(response), [])

    def get(self, url: str) -> HttpResponse:
        response = self.client.get(url)
        self.assert_no_error_messages(response)
        self.assertIn(response.status_code, [302, 200])
        return response

    def _query(
        self,
        method,
        url: str,
        args: Dict[str, Any] = None,
        content_type: str = None,
    ) -> HttpResponse:
        if content_type:
            response = method(url, args, content_type=content_type)
        else:
            response = method(url, args)
        self.assert_no_error_messages(response)
        self.assertIn(response.status_code, [302, 200], str(response.content))
        if response.context and "form" in response.context:
            form = response.context["form"]
            self.assertTrue(form.is_valid(), f"Errors in form: {form.errors}")
        return response

    def post(
        self, url: str, args: Dict[str, Any] = None, content_type=None
    ) -> HttpResponse:
        return self._query(self.client.post, url, args, content_type)

    def patch(
        self, url: str, args: Dict[str, Any] = None, content_type=None
    ) -> HttpResponse:
        return self._query(self.client.patch, url, args, content_type)

    def put(
        self, url: str, args: Dict[str, Any] = None, content_type=None
    ) -> HttpResponse:
        return self._query(self.client.put, url, args, content_type)

    def post_expecting_error(self, url: str, args: Dict[str, Any] = None) -> List[str]:
        response = self.client.post(url, args)
        return self.get_errors_from_response(response)
