from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.utils.crypto import get_random_string
import urllib
from django.views.decorators.csrf import csrf_exempt


def authorize_url(request):
    redirect_uri = request.GET["redirect_uri"][:-1]
    params = urllib.parse.urlencode(
        {"code": "stub_code", "state": request.GET["state"]}
    )
    return HttpResponseRedirect(redirect_uri + "?" + str(params))


def profile_url(request):
    return JsonResponse(
        {
            "id": "123456789",
            "username": "TEST USER",
            "avatar": "e71b856158d285d6ac6e8877d17bae45",
            "discriminator": "1234",
            "public_flags": 0,
            "flags": 0,
            "locale": "en-US",
            "mfa_enabled": True,
        }
    )


# Exempt as OAuth is passing along a state param and access code instead of django's csrf tokens.
@csrf_exempt
def access_token_url(request):
    if request.POST["code"] == "stub_code":
        return JsonResponse({"access_token": "stub_access_code"})
    else:
        print(
            "Code recieved from allauth discord provider didn't match the one saved in the session?"
        )
        return HttpResponseBadRequest()
