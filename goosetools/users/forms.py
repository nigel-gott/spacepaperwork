from dal import autocomplete
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from tinymce.widgets import TinyMCE

from goosetools.user_forms.models import DynamicForm
from goosetools.users.fields import TimeZoneFormField
from goosetools.users.models import (
    Character,
    Corp,
    DiscordRole,
    GooseGroup,
    GoosePermission,
    GooseUser,
    PermissibleEntity,
)


class DiscordForm(forms.Form):
    guild_id = forms.CharField(
        help_text=f"The Discord Server ID to Link {settings.SITE_NAME} To:",
        label="Discord Server ID",
        required=False,
    )


class CodeOfConductForm(forms.Form):
    code_of_conduct = forms.CharField(
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
        required=False,
        help_text="The Code of Conduct new users must agree to when applying. Leave blank to disable.",
    )


class SignupFormWithTimezone(forms.Form):
    existing_character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        help_text=f"You already have characters in {settings.SITE_NAME}, select which one will be applying to this corp or leave blank and fill in In Game Name for a new character.",
    )
    ingame_name = forms.CharField(
        help_text="The exact in-game name of one of your characters. Later you can add more characters by going to Settings->Characters."
    )
    prefered_pronouns = forms.ChoiceField(
        choices=[
            ("blank", "----"),
            ("they", "They/Them"),
            ("she", "She/Her"),
            ("he", "He/Him"),
        ],
        help_text="Your Prefered Pronouns, feel free not to say and leave this blank.",
        required=False,
    )
    timezone = TimeZoneFormField(
        help_text="Your Timezone",
        display_GMT_offset=True,
        widget=forms.Select(attrs={"class": "browser-default"}),
    )
    transaction_tax = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Transaction Tax %",
        initial=15,
        help_text=f"Your ingame Transaction Tax - Used to calculate fees when you sell loot in {settings.SITE_NAME}.",
    )
    broker_fee = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Broker Fee %",
        initial=8,
        help_text="Your ingame Broker Fee.",
    )

    def _disable_field(self, field_name):
        self.fields.pop(field_name)

    def __init__(self, *args, **kwargs):
        existing_characters = kwargs.pop(
            "existing_characters", Character.objects.none()
        )
        super().__init__(*args, **kwargs)

        if not settings.PRONOUN_ROLES:
            self._disable_field("prefered_pronouns")

        self.fields["existing_character"].queryset = existing_characters
        if existing_characters.count() == 0:
            self._disable_field(
                "existing_character",
            )
        else:
            self.fields["ingame_name"].required = False
            self.fields["existing_character"].required = False
            self.fields[
                "ingame_name"
            ].help_text = "Only fill this in if you don't want to apply with one of the existing characters above. This should be the EXACT IN GAME name of the character. Once approved you will be able to auth alts under Settings->Characters."


class SettingsForm(forms.Form):
    timezone = TimeZoneFormField(
        help_text="Your Timezone",
        display_GMT_offset=True,
        widget=forms.Select(attrs={"class": "browser-default"}),
    )
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %", initial=15
    )
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %", initial=8
    )
    default_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), initial=0, required=False
    )


class UserApplicationUpdateForm(forms.Form):
    notes = forms.CharField(required=False)


class AddEditCharacterForm(forms.Form):
    ingame_name = forms.CharField()
    corp = forms.ModelChoiceField(queryset=Corp.objects.all(), initial=0)


class AdminEditCharacterForm(forms.Form):
    ingame_name = forms.CharField()
    corp = forms.ModelChoiceField(queryset=Corp.objects.all(), initial=0)
    gooseuser = forms.ModelChoiceField(
        queryset=GooseUser.objects.all(),
        widget=autocomplete.ModelSelect2(url="username-autocomplete"),
    )


class AdminEditUserForm(forms.Form):
    notes = forms.CharField(required=False)
    status = forms.ChoiceField(
        choices=GooseUser.USER_STATUS_CHOICES,
    )
    manual_groups = forms.ModelMultipleChoiceField(
        GooseGroup.objects.filter(manually_given=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class CorpForm(forms.Form):
    full_name = forms.CharField()
    description = forms.CharField(
        help_text="This description will be shown to users when they are deciding which corp to apply for:",
        required=False,
    )
    public_corp = forms.BooleanField(
        help_text="Anyone regardless of discord roles can apply for this corp if ticked:",
        required=False,
    )
    auto_approve = forms.BooleanField(
        help_text="If ticked users will have their applications instantly accepted and be let into this corp, if not ticked a user admin will have to approve any applications:",
        required=False,
    )
    sign_up_form = forms.ModelChoiceField(
        queryset=DynamicForm.objects.all(), required=False
    )
    ticker = forms.CharField()
    discord_role_given_on_approval = forms.ModelChoiceField(
        queryset=DiscordRole.objects.all().order_by("name"), required=False
    )
    manual_group_given_on_approval = forms.ModelChoiceField(
        queryset=GooseGroup.objects.filter(manually_given=True).order_by("name"),
        required=False,
    )
    discord_roles_allowing_application = forms.ModelMultipleChoiceField(
        DiscordRole.objects.all().order_by("name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="If any roles below are ticked then the user must have one or more of those roles to apply for this corp, UNLESS the corp is public which overrides anything you set here:",
    )


class CharacterUserSearchForm(forms.Form):
    name = forms.CharField()


class CharacterForm(forms.Form):
    FACTIONS = [
        ("All", "All"),
        ("Guristas", "Guritas"),
        ("Angel", "Angel"),
        ("Blood", "Blood"),
        ("Sansha", "Sansha"),
        ("Serpentis", "Serpentis"),
    ]
    faction = forms.ChoiceField(
        choices=FACTIONS,
        required=False,
        initial="All",
        label="Item Faction Filter",
    )
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="user-character-autocomplete"),
    )


class EditGroupForm(forms.Form):
    name = forms.CharField()
    description = forms.CharField()
    manually_given = forms.BooleanField(
        initial=True,
        required=False,
        help_text=f"When ticked this group can only be given manually via the Admin Menus on {settings.SITE_NAME}.",
    )
    required_discord_role_id = forms.ModelChoiceField(
        queryset=DiscordRole.objects.all().order_by("name"),
        required=False,
        help_text="When selected this group is only given to people with the role in discord, this is automatically checked every hour, it cannot be manually given.",
    )
    permissions = forms.ModelMultipleChoiceField(
        GoosePermission.objects.all(), widget=forms.CheckboxSelectMultiple
    )


class PermissibleEntityForm(forms.Form):
    existing_entity = forms.ModelChoiceField(
        PermissibleEntity.objects.all(), required=False, widget=forms.HiddenInput()
    )
    control = forms.ChoiceField(
        choices=[
            ("view", "Viewing"),
            ("use", "Using"),
            ("edit", "Editing"),
            ("admin", "Admining"),
            ("delete", "Deleting"),
        ],
        label="access type",
        help_text="The type of access to allow or deny.",
    )
    allow_or_deny = forms.ChoiceField(
        choices=[("allow", "Allow Access "), ("deny", "Deny Access")],
        help_text="Whether to allow access or deny access to the users who match.",
    )
    permission = forms.ModelChoiceField(
        GoosePermission.objects.all(),
        required=False,
        empty_label="Any Permission",
        help_text="Match users who have this global permission type.",
    )
    corp = forms.ModelChoiceField(
        Corp.objects.all(),
        required=False,
        empty_label="Any Corp",
        help_text="Match users in this corp.",
    )
    user = forms.ModelChoiceField(
        queryset=GooseUser.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="username-autocomplete", attrs={"class": "mat_select_ignore"}
        ),
        required=False,
        empty_label="Any User",
        help_text="Match this specific user, leave blank to match any user.",
    )


PermissibleEntityFormSet = formset_factory(
    form=PermissibleEntityForm, extra=0, can_delete=True
)


def control_to_relation(
    control,
    controller,
):
    if control == "view":
        return controller.viewable_by
    elif control == "use":
        return controller.usable_by
    elif control == "edit":
        return controller.editable_by
    elif control == "admin":
        return controller.adminable_by
    elif control == "delete":
        return controller.deletable_by
    raise ValidationError(f"Unknown control {control}")


def setup_new_permissible_entity_formset(owner, controllable_class, request):
    initials = []
    for control, initial in controllable_class.default_permissible_entities(None):
        initials.append(
            {
                "control": control,
                "allow_or_deny": "allow" if initial.allow_or_deny else "deny",
                "user": initial.user,
                "corp": initial.corp,
                "permission": initial.permission,
            }
        )
    if request.method == "POST":
        form_set = PermissibleEntityFormSet(
            request.POST, request.FILES, initial=initials
        )
    else:
        form_set = PermissibleEntityFormSet(initial=initials)
    form_set.builtin_wrapper = controllable_class.built_in_permissible_entities(
        None, owner
    )
    return form_set


def setup_existing_permissible_entity_formset(
    owner, controllable_instance, request=None
):
    controller = controllable_instance.access_controller
    bys = {
        "view": controller.viewable_by,
        "edit": controller.editable_by,
        "use": controller.usable_by,
        "delete": controller.deletable_by,
        "admin": controller.adminable_by,
    }
    initials = []
    for control, qs in bys.items():
        for e in qs.filter(built_in=False):
            initials.append(
                {
                    "existing_entity": e,
                    "control": control,
                    "allow_or_deny": "allow" if e.allow_or_deny else "deny",
                    "user": e.user,
                    "corp": e.corp,
                    "permission": e.permission,
                }
            )
    if request.method == "POST":
        form_set = PermissibleEntityFormSet(
            request.POST, request.FILES, initial=initials
        )
    else:
        form_set = PermissibleEntityFormSet(initial=initials)
    form_set.builtin_wrapper = controllable_instance.built_in_permissible_entities(
        owner
    )
    return form_set


def handle_permissible_entity_formset(owning_user, formset, controllable_instance):
    controller = controllable_instance.access_controller
    if formset.is_valid():
        for form in formset.deleted_forms:
            existing = form.cleaned_data["existing_entity"]
            if existing:
                if existing.built_in:
                    raise ValidationError("Cannot edit a built in permissible entity")
                existing.delete()

        for form in formset:
            if "DELETE" in form.cleaned_data and form.cleaned_data["DELETE"]:
                continue
            by = control_to_relation(form.cleaned_data["control"], controller)
            existing = form.cleaned_data["existing_entity"]
            permission = form.cleaned_data["permission"]
            corp = form.cleaned_data["corp"]
            user = form.cleaned_data["user"]
            allow_or_deny = form.cleaned_data["allow_or_deny"] == "allow"
            existing_qs = by.filter(
                permission=permission, corp=corp, user=user, allow_or_deny=allow_or_deny
            )
            already = existing_qs.exists()
            if existing and existing.built_in:
                raise ValidationError("Cannot edit a built in permissible entity")
            if not already and existing:
                controller.viewable_by.remove(existing)
                controller.adminable_by.remove(existing)
                controller.editable_by.remove(existing)
                controller.usable_by.remove(existing)
                controller.deletable_by.remove(existing)
                existing.permission = permission
                existing.corp = corp
                existing.user = user
                existing.allow_or_deny = allow_or_deny
                existing.reset_order_to_level()
                existing.save()
                by.add(existing)

            if already and existing:
                if not existing_qs.filter(id=existing.id).exists():
                    existing.delete()
            if not already and not existing:
                entity = PermissibleEntity(
                    permission=permission,
                    corp=corp,
                    user=user,
                    allow_or_deny=allow_or_deny,
                    built_in=False,
                )
                entity.reset_order_to_level()
                entity.save()
                by.add(entity)

        for attr_name, items in controllable_instance.built_in_permissible_entities(
            owning_user
        ).items():
            for item in items:
                qs = getattr(controller, attr_name)
                built_in_exists = qs.filter(
                    permission=item.permission,
                    corp=item.corp,
                    user=item.user,
                    allow_or_deny=item.allow_or_deny,
                    built_in=True,
                ).exists()
                if not built_in_exists:
                    item.reset_order_to_level()
                    item.save()
                    qs.add(item)
