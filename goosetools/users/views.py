from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.db.models.query_utils import Q
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView

from goosetools.users.forms import (
    AddEditCharacterForm,
    CharacterUserSearchForm,
    SettingsForm,
    SignupFormWithTimezone,
    UserApplicationUpdateForm,
)
from goosetools.users.models import (
    Character,
    CorpApplication,
    DiscordGuild,
    GooseUser,
    UserApplication,
)


def user_signup(request):
    site_user = request.user
    if site_user.is_rejected():
        messages.error(
            request,
            "You cannot signup to goosetools, please contact @AuthTeam on discord for more information.",
        )
        return HttpResponseRedirect(reverse("core:splash"))
    elif site_user.is_approved():
        messages.error(request, "You have already registered on goosetools")
        return HttpResponseRedirect(reverse("core:home"))

    has_characters_already = (
        site_user.has_gooseuser() and len(site_user.gooseuser.characters()) > 0
    )

    if request.method == "POST":
        form = SignupFormWithTimezone(
            request.POST,
            socialaccount=request.user.discord_socialaccount(),
            has_characters_already=has_characters_already,
        )
        if form.is_valid():
            data = form.cleaned_data
            ingame_name = not has_characters_already and data["ingame_name"]
            if (
                ingame_name
                and Character.objects.filter(ingame_name=ingame_name).count() > 0
            ):
                error = f"You cannot apply with an in-game name of {ingame_name} as it already exists"
                messages.error(request, error)
                print(error)
            else:
                gooseuser, _ = GooseUser.objects.update_or_create(
                    site_user=site_user,
                    defaults={
                        "timezone": data["timezone"],
                        "broker_fee": data["broker_fee"],
                        "transaction_tax": data["transaction_tax"],
                    },
                )
                application = UserApplication(
                    user=gooseuser,
                    status="unapproved",
                    created_at=timezone.now(),
                    application_notes=data["application_notes"],
                    ingame_name=ingame_name or None,
                    previous_alliances=data["previous_alliances"],
                    activity=data["activity"],
                    looking_for=data["looking_for"],
                    corp=data["corp"],
                )
                _give_pronoun_roles(gooseuser.discord_uid(), data["prefered_pronouns"])
                application.full_clean()
                application.save()
                print("MADE AND SAVED")
                return HttpResponseRedirect(reverse("core:home"))
    else:
        initial = {}
        if site_user.has_gooseuser():
            gooseuser = site_user.gooseuser
            initial = {
                "timezone": gooseuser.timezone,
                "broker_fee": gooseuser.broker_fee,
                "transaction_tax": gooseuser.transaction_tax,
            }
        form = SignupFormWithTimezone(
            initial=initial,
            socialaccount=request.user.discord_socialaccount(),
            has_characters_already=has_characters_already,
        )

    return render(request, "users/signup.html", {"form": form})


def _give_pronoun_roles(uid, prefered_pronouns):
    if prefered_pronouns == "they":
        DiscordGuild.try_give_role(uid, 762405572136927242)
    elif prefered_pronouns == "she":
        DiscordGuild.try_give_role(uid, 762405484614910012)
    elif prefered_pronouns == "he":
        DiscordGuild.try_give_role(uid, 762404773512740905)


def settings_view(request):
    goose_user = request.user.gooseuser
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
        user=goose_user
    )
    return render(request, "users/settings.html", {"form": form})


@permission_required("users.change_userapplication")
@transaction.atomic
def application_update(request, pk):
    application = get_object_or_404(UserApplication, pk=pk)
    if request.method == "POST":
        if "approve" in request.POST:
            if (
                Character.objects.filter(ingame_name=application.ingame_name).count()
                > 0
            ):
                error = f"Cannot approve this application with a in-game name of {application.ingame_name} as it already exists, please talk to the user and fix the application's ingame name using the site admin page."
                messages.error(request, error)
                return HttpResponseRedirect(reverse("applications"))

            application.approve()
        elif "reject" in request.POST:
            application.reject()
        else:
            return HttpResponseBadRequest()

        form = UserApplicationUpdateForm(request.POST)
        if form.is_valid():
            application.user.notes = form.cleaned_data["notes"]
            application.user.save()
        return HttpResponseRedirect(reverse("applications"))
    else:
        return HttpResponseNotAllowed("POST")


@permission_required("users.change_userapplication")
@transaction.atomic
def corp_application_update(request, pk):
    application = get_object_or_404(CorpApplication, pk=pk)
    if request.method == "POST":
        if "approve" in request.POST:
            application.approve()
        elif "reject" in request.POST:
            application.reject()
        else:
            return HttpResponseBadRequest()

        return HttpResponseRedirect(reverse("corp_applications"))
    else:
        return HttpResponseNotAllowed("POST")


def character_edit(request, pk):
    character = get_object_or_404(Character, pk=pk)
    if character.user != request.user.gooseuser:
        messages.error(request, "You cannot edit someone elses character")
        return HttpResponseRedirect(reverse("characters"))
    initial = {"ingame_name": character.ingame_name, "corp": character.corp}
    if request.method == "POST":
        form = AddEditCharacterForm(request.POST, initial=initial)
        if form.is_valid():
            if not form.has_changed():
                messages.error(request, "You must make a change to the character!")
            else:
                character.ingame_name = form.cleaned_data["ingame_name"]
                character.save()
                new_corp = form.cleaned_data["corp"]
                if character.corp != new_corp:
                    messages.info(
                        request,
                        f"Corp application for {character} to {new_corp} registered in goosetools pending approval from @AuthTeam.",
                    )
                    CorpApplication.objects.create(
                        character=character, status="unapproved", corp=new_corp
                    )
                return HttpResponseRedirect(reverse("characters"))

    else:
        form = AddEditCharacterForm(initial=initial)
    return render(request, "users/character_edit.html", {"form": form})


def character_new(request):
    if request.method == "POST":
        form = AddEditCharacterForm(request.POST)
        if form.is_valid():
            ingame_name = form.cleaned_data["ingame_name"]
            if Character.objects.filter(ingame_name=ingame_name).count() > 0:
                error = f"Cannot create a character with a in-game name of {ingame_name} as it already exists."
                messages.error(request, error)
                return HttpResponseRedirect(reverse("characters"))
            new_corp = form.cleaned_data["corp"]
            character = Character.objects.create(
                ingame_name=form.cleaned_data["ingame_name"],
                corp=None,
                user=request.user.gooseuser,
            )
            messages.info(
                request,
                f"Corp application for {character} to {new_corp} registered in goosetools pending approval from @AuthTeam.",
            )
            CorpApplication.objects.create(
                character=character, status="unapproved", corp=new_corp
            )
            return HttpResponseRedirect(reverse("characters"))

    else:
        form = AddEditCharacterForm()
    return render(request, "users/character_new.html", {"form": form})


class UserApplicationListView(ListView):
    model = UserApplication

    def get_queryset(self):
        return UserApplication.unapproved_applications()


@permission_required("users.change_userapplication")
def corp_application_list(request):
    grouped_by_corp = {
        key: list(result)
        for key, result in groupby(
            CorpApplication.unapproved_applications(), key=lambda item: item.corp.name
        )
    }
    return render(
        request,
        "users/corpapplication_list.html",
        {"applications_by_corp": grouped_by_corp},
    )


@permission_required("users.change_userapplication")
def user_application_list(request):
    return render(
        request,
        "users/userapplication_list.html",
        {"object_list": UserApplication.unapproved_applications()},
    )


def user_view(request, pk):
    user = get_object_or_404(GooseUser, pk=pk)
    return render(
        request,
        "users/user_view.html",
        {"viewed_user": user},
    )


def character_list(request):
    return render(
        request,
        "users/character_list.html",
        {
            "characters": request.user.gooseuser.characters(),
            "corp_apps": CorpApplication.objects.filter(
                character__user=request.user.gooseuser,
            ).exclude(status="approved"),
        },
    )


def character_search(request):

    characters = None
    users = None
    if request.GET and "name" in request.GET:
        form = CharacterUserSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data["name"]
            characters = Character.objects.filter(ingame_name__icontains=name)
            users = GooseUser.objects.filter(Q(site_user__username__icontains=name))
    else:
        form = CharacterUserSearchForm()

    return render(
        request,
        "users/character_search.html",
        {"form": form, "characters": characters, "users": users},
    )
