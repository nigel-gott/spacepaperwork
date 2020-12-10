from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import ListView

from goosetools.users.forms import SettingsForm
from goosetools.users.models import Character, UserApplication


def settings_view(request):
    goose_user = request.user
    if request.method == "POST":
        form = SettingsForm(request.POST)
        if form.is_valid():
            messages.success(request, "Updated your settings!")
            goose_user.default_character = form.cleaned_data["default_character"]
            goose_user.timezone = form.cleaned_data["timezone"]
            goose_user.broker_fee = form.cleaned_data["broker_fee"]
            goose_user.transaction_tax = form.cleaned_data["transaction_tax"]
            goose_user.full_clean()
            goose_user.save()
            return HttpResponseRedirect(reverse("settings"))
    else:
        form = SettingsForm(
            initial={
                "default_character": goose_user.default_character,
                "timezone": goose_user.timezone,
                "broker_fee": goose_user.broker_fee,
                "transaction_tax": goose_user.transaction_tax,
            }
        )

    form.fields["default_character"].queryset = Character.objects.filter(
        discord_user=goose_user.discord_user
    )
    return render(request, "users/settings.html", {"form": form})


@permission_required("users.change_userapplication")
@transaction.atomic
def application_update(request, pk):
    application = get_object_or_404(UserApplication, pk=pk)
    if request.method == "POST":
        if "approve" in request.POST:
            application.approve()
        elif "reject" in request.POST:
            application.reject()
        else:
            return HttpResponseBadRequest()
        return HttpResponseRedirect(reverse("applications"))
    else:
        return HttpResponseNotAllowed("POST")


class UserApplicationListView(ListView):
    model = UserApplication
