from itertools import groupby

from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.aggregates import StringAgg
from django.db import transaction
from django.db.models.expressions import F, Value
from django.db.models.fields import CharField
from django.db.models.functions import Concat
from django.db.models.query_utils import Q
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from goosetools.users.forms import (
    AddEditCharacterForm,
    AdminEditCharacterForm,
    AdminEditUserForm,
    AuthConfigForm,
    CharacterUserSearchForm,
    CorpForm,
    EditGroupForm,
    SettingsForm,
    SignupFormWithTimezone,
    UserApplicationUpdateForm,
)
from goosetools.users.jobs.hourly.update_discord_roles import refresh_from_discord
from goosetools.users.models import (
    ALL_CORP_ADMIN,
    SINGLE_CORP_ADMIN,
    USER_ADMIN_PERMISSION,
    USER_GROUP_ADMIN_PERMISSION,
    AuthConfig,
    Character,
    Corp,
    CorpApplication,
    DiscordGuild,
    GooseGroup,
    GoosePermission,
    GooseUser,
    HasGooseToolsPerm,
    UserApplication,
    has_perm,
)
from goosetools.users.serializers import CharacterSerializer, GooseUserSerializer


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
                gooseuser.cache_fields_from_social_account()
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


@has_perm(perm=USER_ADMIN_PERMISSION)
def auth_settings_view(request):
    auth_config = AuthConfig.get_active()
    if request.method == "POST":
        form = AuthConfigForm(request.POST)
        if form.is_valid():
            messages.success(request, "Updated your settings!")
            auth_config.code_of_conduct = form.data["code_of_conduct"]
            auth_config.full_clean()
            auth_config.save()
            return HttpResponseRedirect(reverse("auth_settings"))
    else:
        form = AuthConfigForm(initial={"code_of_conduct": auth_config.code_of_conduct})

    return render(
        request, "users/auth_config.html", {"form": form, "auth_config": auth_config}
    )


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


@has_perm(USER_ADMIN_PERMISSION)
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

            application.approve(request.gooseuser)
        elif "reject" in request.POST:
            application.reject(request.gooseuser)
        else:
            return HttpResponseBadRequest()

        form = UserApplicationUpdateForm(request.POST)
        if form.is_valid():
            application.user.notes = form.cleaned_data["notes"]
            application.user.save()
        return HttpResponseRedirect(reverse("applications"))
    else:
        return HttpResponseNotAllowed("POST")


@has_perm([SINGLE_CORP_ADMIN, ALL_CORP_ADMIN])
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
                corp = form.cleaned_data["corp"]
                if character.corp != corp:
                    messages.info(
                        request,
                        f"Corp application for {character} to {corp} registered in goosetools pending approval from @AuthTeam.",
                    )
                    CorpApplication.objects.create(
                        character=character, status="unapproved", corp=corp
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
            corp = form.cleaned_data["corp"]
            character = Character.objects.create(
                ingame_name=form.cleaned_data["ingame_name"],
                corp=Corp.unknown_corp(),
                user=request.user.gooseuser,
            )
            messages.info(
                request,
                f"Corp application for {character} to {corp} registered in goosetools pending approval from @AuthTeam.",
            )
            CorpApplication.objects.create(
                character=character, status="unapproved", corp=corp
            )
            return HttpResponseRedirect(reverse("characters"))

    else:
        form = AddEditCharacterForm()
    return render(request, "users/character_new.html", {"form": form})


class UserApplicationListView(ListView):
    model = UserApplication

    def get_queryset(self):
        return UserApplication.unapproved_applications()


@has_perm([SINGLE_CORP_ADMIN, ALL_CORP_ADMIN])
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


@has_perm([USER_ADMIN_PERMISSION])
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


@has_perm(perm=USER_ADMIN_PERMISSION)
def user_dashboard(request):
    return render(
        request,
        "users/user_dashboard.html",
        {
            "page_data": {
                "gooseuser_id": request.gooseuser.id,
                "site_prefix": f"/{settings.URL_PREFIX}",
                "ajax_url": reverse("gooseuser-list"),
                "user_admin_view_url": reverse("user_admin_view", args=[0]),
                "all_group_names": list(
                    GooseGroup.objects.all().values_list("name", flat=True)
                ),
                "group_filter": request.GET.get("group_filter", ""),
                "status_filter": request.GET.get("status_filter", ""),
            },
            "gooseuser": request.gooseuser,
        },
    )


@has_perm(perm=[ALL_CORP_ADMIN, SINGLE_CORP_ADMIN])
def character_dashboard(request):
    return render(
        request,
        "users/character_dashboard.html",
        {
            "page_data": {
                "gooseuser_id": request.gooseuser.id,
                "edit_url": reverse("admin_character_edit", args=[0]),
                "ajax_url": reverse("character-list"),
                "site_prefix": f"/{settings.URL_PREFIX}",
                "all_corp_names": list(
                    Corp.objects.all().values_list("name", flat=True)
                ),
                "corp_filter": request.GET.get("corp_filter", ""),
            },
            "gooseuser": request.gooseuser,
        },
    )


def build_query_for_all_users_annotated_with_their_characters():
    q = GooseUser.objects.annotate(
        char_names=StringAgg(
            Concat(
                Value("["),
                F("character__corp"),
                Value("] "),
                F("character__ingame_name"),
                output_field=CharField(),
            ),
            delimiter=", ",
        ),
    ).all()
    return q


class CharacterQuerySet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    permission_classes = [HasGooseToolsPerm.of([ALL_CORP_ADMIN, SINGLE_CORP_ADMIN])]
    queryset = Character.objects.all()

    serializer_class = CharacterSerializer

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def delete(self, request, pk=None):
        char = self.get_object()
        char.corp = Corp.deleted_corp()
        char.save()
        serializer = self.get_serializer(char)
        return Response(serializer.data)

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def unknown(self, request, pk=None):
        char = self.get_object()
        char.corp = Corp.unknown_corp()
        char.save()
        serializer = self.get_serializer(char)
        return Response(serializer.data)


class GooseUserQuerySet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    permission_classes = [HasGooseToolsPerm.of(USER_ADMIN_PERMISSION)]
    queryset = build_query_for_all_users_annotated_with_their_characters()

    serializer_class = GooseUserSerializer

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def ban(self, request, pk=None):
        return self._change_status(request, "rejected")

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def approve(self, request, pk=None):
        return self._change_status(request, "approved")

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def unapprove(self, request, pk=None):
        return self._change_status(request, "unapproved")

    def _change_status(self, request, status):
        goose_user = self.get_object()
        requesting_gooseuser = request.gooseuser
        goose_user.change_status(requesting_gooseuser, status)
        goose_user.save()
        serializer = self.get_serializer(goose_user)
        return Response(serializer.data)


@has_perm(perm=USER_GROUP_ADMIN_PERMISSION)
def groups_view(request):
    groups = [
        {
            "name": g.name,
            "id": g.id,
            "member_count": g.groupmember_set.count(),
            "description": g.description,
            "linked_discord_role": g.linked_discord_role,
            "editable": g.editable,
            "permissions": ", ".join(g.permissions()),
        }
        for g in GooseGroup.objects.all().order_by("editable", "name")
    ]
    return render(
        request,
        "users/goosegroup_view.html",
        {"groups": groups},
    )


@has_perm(perm=USER_GROUP_ADMIN_PERMISSION)
def edit_group(request, pk):
    group = get_object_or_404(GooseGroup, pk=pk)
    if not group.editable:
        return HttpResponseForbidden()
    if request.method == "POST":
        form = EditGroupForm(request.POST)
        if form.is_valid():
            delete = request.POST.get("delete", False)
            if delete:
                group.delete()
                messages.success(request, f"Succesfully deleted group {group.name}")
            else:
                group.name = form.cleaned_data["name"]
                group.description = form.cleaned_data["description"]
                group.linked_discord_role = form.cleaned_data["linked_discord_role_id"]
                group.grouppermission_set.all().delete()
                group.save()
                for perm in form.cleaned_data["permissions"]:
                    group.link_permission(perm.name)
                messages.success(request, f"Succesfully edited group {group.name}")
            return HttpResponseRedirect(reverse("groups_view"))
    else:
        permissions = list(
            GoosePermission.objects.filter(grouppermission__group=group).values_list(
                "pk", flat=True
            )
        )

        form = EditGroupForm(
            initial={
                "name": group.name,
                "description": group.description,
                "linked_discord_role_id": group.linked_discord_role,
                "permissions": permissions,
            }
        )
    return render(request, "users/edit_group.html", {"form": form})


@has_perm(perm=USER_GROUP_ADMIN_PERMISSION)
def new_group(request):
    if request.method == "POST":
        form = EditGroupForm(request.POST)
        if form.is_valid():
            group = GooseGroup(
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                linked_discord_role=form.cleaned_data["linked_discord_role_id"],
            )
            group.save()
            for p in form.cleaned_data["permissions"]:
                group.link_permission(p.name)
            messages.success(request, f"Succesfully created group {group.name}")

            return HttpResponseRedirect(reverse("groups_view"))
    else:
        form = EditGroupForm()
    return render(request, "users/new_group.html", {"form": form})


@has_perm(perm=USER_GROUP_ADMIN_PERMISSION)
def refresh_discord_groups(request):
    output = False
    if request.method == "POST":
        output = refresh_from_discord()
    return render(request, "users/refresh_discord_groups.html", {"output": output})


@has_perm(perm=[ALL_CORP_ADMIN, SINGLE_CORP_ADMIN])
def admin_character_edit(request, pk):
    character = get_object_or_404(Character, pk=pk)
    initial = {
        "ingame_name": character.ingame_name,
        "corp": character.corp,
        "gooseuser": character.user,
    }
    if request.method == "POST":
        form = AdminEditCharacterForm(request.POST, initial=initial)
        if form.is_valid():
            if not form.has_changed():
                messages.error(request, "You must make a change to the character!")
            else:
                character.ingame_name = form.cleaned_data["ingame_name"]
                character.corp = form.cleaned_data["corp"]
                character.user_id = form.cleaned_data["gooseuser"]
                character.save()
                messages.success(request, "Succesfully Editted the User")
                return HttpResponseRedirect(reverse("character_dashboard"))

    else:
        form = AdminEditCharacterForm(initial=initial)
    form.fields["gooseuser"].initial = character.user
    return render(request, "users/admin_character_edit.html", {"form": form})


@has_perm(perm=USER_ADMIN_PERMISSION)
def user_admin_view(request, pk):
    user = get_object_or_404(GooseUser, pk=pk)
    if request.method == "POST":
        form = AdminEditUserForm(request.POST)
        if form.is_valid():
            user.notes = form.cleaned_data["notes"]
            user.change_status(request.gooseuser, form.cleaned_data["status"])
            user.save()
            messages.success(request, "Succesfully Editted the User")
            return HttpResponseRedirect(reverse("user_admin_view", args=[user.pk]))
    else:
        form = AdminEditUserForm(initial={"notes": user.notes, "status": user.status})
    return render(
        request,
        "users/user_admin_view.html",
        {"viewed_user": user, "form": form},
    )


@has_perm(perm=[ALL_CORP_ADMIN, SINGLE_CORP_ADMIN])
def corps_list(request):
    corps = [
        {
            "name": c.name,
            "full_name": c.full_name,
            "name_with_ticker": c.name_with_corp_tag(),
            "member_count": c.character_set.count(),
            "required_discord_role": c.required_discord_role,
        }
        for c in Corp.objects.all().order_by("name")
    ]
    return render(
        request,
        "users/corp_list.html",
        {"corps": corps},
    )


@has_perm(perm=[ALL_CORP_ADMIN, SINGLE_CORP_ADMIN])
def new_corp(request):
    if request.method == "POST":
        form = CorpForm(request.POST)
        if form.is_valid():
            corp = Corp(
                full_name=form.cleaned_data["full_name"],
                name=form.cleaned_data["ticker"],
                required_discord_role=form.cleaned_data["required_discord_role"],
            )
            corp.save()
            messages.success(request, f"Succesfully Created {corp.name}")
            return HttpResponseRedirect(reverse("corps_list"))
    else:
        form = CorpForm()
    return render(
        request,
        "users/corp_new.html",
        {"form": form},
    )


@has_perm(perm=[ALL_CORP_ADMIN, SINGLE_CORP_ADMIN])
def edit_corp(request, pk):
    corp = get_object_or_404(Corp, pk=pk)
    if request.method == "POST":
        form = CorpForm(request.POST)
        form.fields["ticker"].disabled = True
        form.fields["ticker"].required = False
        if form.is_valid():
            delete = request.POST.get("delete", False)
            if delete:
                if corp.character_set.count() == 0:
                    corp.delete()
                    messages.success(request, f"Succesfully deleted corp {corp.name}")
                else:
                    messages.error(
                        request,
                        f"Cannot delete {corp.name} until all characters in goosetools with that corp have been moved to a new corp.",
                    )
            else:
                corp.full_name = form.cleaned_data["full_name"]
                corp.required_discord_role = form.cleaned_data["required_discord_role"]
                corp.save()
                messages.success(request, f"Succesfully Edited {corp.name}")

            return HttpResponseRedirect(reverse("corps_list"))
    else:
        form = CorpForm(
            initial={
                "ticker": corp.name,
                "full_name": corp.full_name,
                "required_discord_role": corp.required_discord_role,
            }
        )
        form.fields["ticker"].disabled = True
        form.fields["ticker"].required = False
    return render(
        request,
        "users/corp_edit.html",
        {"form": form},
    )
