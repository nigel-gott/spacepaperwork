import urllib

from django.contrib.auth import logout
from django.core.cache import caches
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.urls.base import reverse
from django.views.decorators.csrf import csrf_exempt


def authorize_url(request):
    redirect_uri = request.GET["redirect_uri"][:-1]
    params = urllib.parse.urlencode(
        {"code": "stub_code", "state": request.GET["state"]}
    )
    return HttpResponseRedirect(redirect_uri + "?" + str(params))


def set_uid(request, uid):
    logout(request)
    caches["default"].set("uid", uid)
    if request.tenant.name == "public":
        return HttpResponseRedirect(reverse("tenants:splash"))
    else:
        return HttpResponseRedirect(reverse("core:splash"))


def profile_url(request):
    from goosetools.users.models import GooseUser

    uid = str(caches["default"].get("uid", "123456789"))
    try:
        user = GooseUser.objects.get(uid=uid)
        split = user.discord_username().split("#")
        username = split[0]
        discriminator = split[1]
        # noinspection PyProtectedMember
        # pylint: disable=protected-access
        extra_data = user._discord_account().extra_data
    except GooseUser.DoesNotExist:
        username = "TEST USER" + uid
        discriminator = "1234"
        extra_data = {}

    return JsonResponse(
        {
            "id": uid,
            "username": username,
            "avatar": "e71b856158d285d6ac6e8877d17bae45",
            "discriminator": discriminator,
            "public_flags": 0,
            "flags": 0,
            "locale": "en-US",
            "mfa_enabled": True,
            "extra_data": extra_data,
            **extra_data,
        }
    )


# Exempt as OAuth is passing along a state param and access code instead
# of django's csrf tokens.
@csrf_exempt
def access_token_url(request):
    if request.POST["code"] == "stub_code":
        return JsonResponse({"access_token": "stub_access_code"})
    print(
        "Code from allauth discord provider didn't match the one saved in the session?"
    )
    return HttpResponseBadRequest()
