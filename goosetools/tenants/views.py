from django.conf import settings
from django.http.response import HttpResponseBadRequest, HttpResponseRedirect
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

    def form_valid(self, form):
        if settings.GOOSEFLOCK_FEATURES:
            return HttpResponseBadRequest()
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
                setup_tenant(self.object, self.request, signup_form)
            return r
        else:
            return super().form_invalid(form)


def splash(request):
    if settings.GOOSEFLOCK_FEATURES:
        return HttpResponseRedirect(reverse("core:splash"))
    member_orgs = []
    owners_orgs = []
    for tenant in Client.objects.all():
        if tenant.name != "public" and request.user.is_authenticated:
            with tenant_context(tenant):
                if tenant.owner == request.user:
                    owners_orgs.append(tenant)
                elif GooseUser.objects.filter(site_user=request.user).count() > 0:
                    member_orgs.append(tenant)
    return render(
        request,
        "tenants/splash.html",
        {
            "owner_orgs": owners_orgs,
            "member_orgs": member_orgs,
            "tenant_subfolder_prefix": settings.TENANT_SUBFOLDER_PREFIX,
        },
    )
