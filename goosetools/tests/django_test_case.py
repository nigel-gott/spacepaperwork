import json
from typing import Any, Dict, List, Set, Tuple

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

    def assert_messages(
        self, r: HttpResponse, expected_messages: List[Tuple[str, str]]
    ):
        self.assertEqual(
            [(m.level_tag, m.message) for m in get_messages(r.wsgi_request)],
            expected_messages,
        )

    def json_matches(self, r: HttpResponse, expected_json: str):
        keys_to_ignore = find_keys_to_ignore(expected_json)
        actual_json = str(r.content, encoding="utf-8")
        self.assertEqual(
            nowhitespace_json(actual_json, keys_to_ignore),
            nowhitespace_json(expected_json, keys_to_ignore),
            # pretty_json(actual_json),
        )


def nowhitespace_json(json_str: str, keys_to_ignore: Set[str]):
    parsed = filter_out_keys(json_str, keys_to_ignore)
    return json.dumps(parsed, indent=4, sort_keys=True)


def pretty_json(json_str: str) -> str:
    parsed = json.loads(json_str)
    return json.dumps(parsed, indent=4, sort_keys=True)


def filter_out_keys(json_str: str, keys_to_filter_out: Set[str]) -> Any:
    parsed = json.loads(json_str)
    return filter_out_keys_recursive(parsed, keys_to_filter_out)


def filter_out_keys_recursive(json_obj: Any, keys_to_filter: Set[str]) -> Any:
    if isinstance(json_obj, list):
        new_list = []
        for item in json_obj:
            new_list.append(filter_out_keys_recursive(item, keys_to_filter))
        return new_list
    elif isinstance(json_obj, dict):
        new_dict: Dict[str, Any] = dict()
        for key, item in json_obj.items():
            if key not in keys_to_filter:
                new_dict[key] = filter_out_keys_recursive(item, keys_to_filter)
        return new_dict
    else:
        return json_obj


def find_keys_to_ignore(json_str: str) -> Set[str]:
    parsed = json.loads(json_str)
    return finds_keys_to_ignore_recursive(parsed, set())


def finds_keys_to_ignore_recursive(json_obj: Any, keys_so_far: Set[str]) -> Set[str]:
    if isinstance(json_obj, list):
        for item in json_obj:
            keys_so_far = finds_keys_to_ignore_recursive(item, keys_so_far)
    elif isinstance(json_obj, dict):
        for key, item in json_obj.items():
            if item == "IGNORE":
                keys_so_far.add(key)
            else:
                keys_so_far = finds_keys_to_ignore_recursive(item, keys_so_far)
    return keys_so_far
