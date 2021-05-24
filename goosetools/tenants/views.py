from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse
from django.utils import timezone
from django.views.generic.edit import CreateView
from django_tenants.utils import tenant_context

from goosetools.tenants.forms import ClientForm
from goosetools.tenants.models import Client, Domain
from goosetools.users.forms import SignupFormWithTimezone
from goosetools.users.handlers import setup_tenant
from goosetools.users.models import GooseUser


def _is_spacepaperwork_in_local_only_mode():
    return settings.STUB_DISCORD


def _is_spacepaperwork_setup():
    if not SocialApp.objects.exists():
        return False
    else:
        return (
            not settings.SINGLE_TENANT or Client.objects.exclude(name="public").exists()
        )


def redirect_single_tenant(f):
    def _wrapped_view(request, *args, **kwargs):
        if settings.SINGLE_TENANT:
            if Client.objects.exclude(name="public").exists():
                return HttpResponseRedirect(reverse("core:splash"))
            else:
                return HttpResponseRedirect(reverse("tenants:setup_install"))
        else:
            return f(request, *args, **kwargs)

    return _wrapped_view


def find_tenants_for_user(request, excluding=None):
    owners_orgs = []
    member_orgs = []
    if excluding:
        qs = Client.objects.exclude(id=excluding.id).all()
    else:
        qs = Client.objects.all()
    for tenant in qs:
        if tenant.name != "public" and request.user.is_authenticated:
            with tenant_context(tenant):
                if tenant.owner == request.user:
                    owners_orgs.append(tenant)
                elif GooseUser.objects.filter(site_user=request.user).count() > 0:
                    member_orgs.append(tenant)
    return owners_orgs, member_orgs


def _single_tenant_missing():
    return settings.SINGLE_TENANT and not Client.objects.exclude(name="public").exists()


class FirstClientCreate(CreateView):
    model = Client
    form_class = ClientForm

    def get_success_url(self) -> str:
        return (
            settings.URL_PREFIX
            + "/"
            + settings.TENANT_SUBFOLDER_PREFIX
            + "/"
            + self.object.name
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["signup_form"] = SignupFormWithTimezone(self.request.POST)
        else:
            data["signup_form"] = SignupFormWithTimezone()
        return data

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        owner_orgs, _ = find_tenants_for_user(self.request)
        if len(owner_orgs) == 0:
            return super().get(request, args, kwargs)
        else:
            messages.error(
                self.request,
                f"You already own the {settings.SITE_NAME} organization '{owner_orgs[0].name}' and cannot create another.",
            )
            return HttpResponseRedirect(reverse("tenants:splash"))

    def post(self, request, *args, **kwargs):
        owner_orgs, _ = find_tenants_for_user(self.request)
        if len(owner_orgs) == 0:
            return super().post(request, *args, **kwargs)
        else:
            messages.error(
                self.request,
                f"You already own the {settings.SITE_NAME} organization '{owner_orgs[0].name}' and cannot create another.",
            )
            return HttpResponseRedirect(reverse("tenants:splash"))

    def form_valid(self, form):
        context = self.get_context_data()
        signup_form = context["signup_form"]
        if signup_form.is_valid():
            two_weeks_from_now = timezone.now() + timezone.timedelta(days=14)
            form.instance.on_trial = True
            form.instance.paid_until = two_weeks_from_now
            form.instance.owner = self.request.user
            form.instance.schema_name = form.instance.name
            r = super().form_valid(form)
            if form.is_valid():
                Domain.objects.create(
                    domain=self.object.name, is_primary=False, tenant=self.object
                )
                setup_tenant(self.object, self.request.user, signup_form.cleaned_data)
                return r
        return super().form_invalid(form)


class ClientCreate(CreateView):
    model = Client
    form_class = ClientForm

    def get_success_url(self) -> str:
        return (
            settings.URL_PREFIX
            + "/"
            + settings.TENANT_SUBFOLDER_PREFIX
            + "/"
            + self.object.name
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["signup_form"] = SignupFormWithTimezone(self.request.POST)
        else:
            data["signup_form"] = SignupFormWithTimezone()
        return data

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        owner_orgs, _ = find_tenants_for_user(self.request)
        if len(owner_orgs) == 0:
            return super().get(request, args, kwargs)
        else:
            messages.error(
                self.request,
                f"You already own the {settings.SITE_NAME} organization '{owner_orgs[0].name}' and cannot create another.",
            )
            return HttpResponseRedirect(reverse("tenants:splash"))

    def post(self, request, *args, **kwargs):
        owner_orgs, _ = find_tenants_for_user(self.request)
        if len(owner_orgs) == 0:
            return super().post(request, *args, **kwargs)
        else:
            messages.error(
                self.request,
                f"You already own the {settings.SITE_NAME} organization '{owner_orgs[0].name}' and cannot create another.",
            )
            return HttpResponseRedirect(reverse("tenants:splash"))

    def form_valid(self, form):
        context = self.get_context_data()
        signup_form = context["signup_form"]
        if signup_form.is_valid():
            two_weeks_from_now = timezone.now() + timezone.timedelta(days=14)
            form.instance.on_trial = True
            form.instance.paid_until = two_weeks_from_now
            form.instance.owner = self.request.user
            form.instance.schema_name = form.instance.name
            r = super().form_valid(form)
            if form.is_valid():
                Domain.objects.create(
                    domain=self.object.name, is_primary=False, tenant=self.object
                )
                setup_tenant(self.object, self.request.user, signup_form.cleaned_data)
                return r
        return super().form_invalid(form)


@redirect_single_tenant
def splash(request):
    owner_orgs, member_orgs = find_tenants_for_user(request)
    return render(
        request,
        "tenants/splash.html",
        {
            "tenant_subfolder_prefix": settings.TENANT_SUBFOLDER_PREFIX,
            "owner_orgs": owner_orgs,
            "member_orgs": member_orgs,
            "orgs": owner_orgs + member_orgs,
        },
    )


@redirect_single_tenant
def help_page(request):
    owner_orgs, member_orgs = find_tenants_for_user(request)
    return render(
        request,
        "tenants/help.html",
        {
            "tenant_subfolder_prefix": settings.TENANT_SUBFOLDER_PREFIX,
            "owner_orgs": owner_orgs,
            "member_orgs": member_orgs,
            "orgs": owner_orgs + member_orgs,
        },
    )


def login_cancelled(request):
    messages.error(
        request,
        f"Sorry you cannot Login without Discord. {settings.SITE_NAME} authenticates who you are using Discord. We only request the minimum amount of data from Discord which is your username and avatar. This way is more secure for everybody as we do not need to store personal data about you such as having you enter a password and email address.",
    )
    return HttpResponseRedirect(reverse("tenants:splash"))
