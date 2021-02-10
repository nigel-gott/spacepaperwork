from django.conf import settings
from django.http.response import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse
from django.utils import timezone
from django.views.generic.edit import CreateView

from goosetools.tenants.models import Client, Domain
from goosetools.users.signals import setup_tenant


class ClientCreate(CreateView):
    model = Client
    fields = ["name"]

    def get_success_url(self) -> str:
        return (
            settings.URL_PREFIX
            + "/"
            + settings.TENANT_SUBFOLDER_PREFIX
            + "/"
            + self.object.name
        )

    def form_valid(self, form):
        if settings.GOOSEFLOCK_FEATURES:
            return HttpResponseBadRequest()
        two_weeks_from_now = timezone.now() + timezone.timedelta(days=14)
        form.instance.on_trial = True
        form.instance.paid_until = two_weeks_from_now
        form.instance.schema_name = form.instance.name
        r = super().form_valid(form)
        Domain.objects.create(
            domain=self.object.name, is_primary=False, tenant=self.object
        )
        setup_tenant(self.object)
        return r


def splash(request):
    if settings.GOOSEFLOCK_FEATURES:
        return HttpResponseRedirect(reverse("core:splash"))
    return render(
        request,
        "tenants/splash.html",
    )
