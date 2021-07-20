from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from goosetools.industry.cron.lookup_ship_prices import import_price_list
from goosetools.pricing.forms import PriceListForm
from goosetools.pricing.models import PriceList
from goosetools.utils import PassRequestToFormViewMixin


def pricing_data_dashboard(request):
    from_date = request.GET.get("from_date", None)
    to_date = request.GET.get("to_date", None)
    params = []
    if from_date is not None:
        params.append(f"from_date={from_date}")
    if to_date is not None:
        params.append(f"to_date={to_date}")

    param_string = ""
    if params:
        param_string = "?" + "&".join(params)
    return render(
        request,
        "pricing/item_prices_db.html",
        {
            "page_data": {
                "gooseuser_id": request.gooseuser.id,
                "site_prefix": f"/{request.site_prefix}",
                "ajax_url": reverse("pricing:itemmarketdataevent-list") + param_string,
                # "edit_url": reverse("pricing:pricelist-update", args=[0]),
                # "view_url": reverse("pricing:pricelist-detail", args=[0]),
            },
            "gooseuser": request.gooseuser,
            "latest_checked": from_date is None and to_date is None,
            "from_date": from_date,
            "to_date": to_date,
        },
    )


def pricing_dashboard(request):
    return render(
        request,
        "pricing/pricing_dashboard.html",
        {
            "page_data": {
                "gooseuser_id": request.gooseuser.id,
                "site_prefix": f"/{request.site_prefix}",
                "ajax_url": reverse("pricing:pricelist-list"),
                "edit_url": reverse("pricing:pricelist-update", args=[0]),
                "view_url": reverse("pricing:pricelist-detail", args=[0]),
                "view_data_url": reverse("pricing:pricing_data_dashboard"),
            },
            "gooseuser": request.gooseuser,
        },
    )


class PriceListDetailView(DetailView):
    model = PriceList

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get("test_google", False):
            if not self.object.access_controller.can_admin(self.request.gooseuser):
                raise PermissionDenied()

            if self.object.api_type != "google_sheet":
                raise SuspiciousOperation(
                    "You can only test google_sheet api price " "lists."
                )

            context["testing_results"] = import_price_list(self.object)
        return context


class PriceListDeleteView(DeleteView):
    model = PriceList
    success_url = reverse_lazy("pricing:pricing_dashboard")
    queryset = PriceList.objects.exclude(deletable=False)


class PriceListCreateView(SuccessMessageMixin, PassRequestToFormViewMixin, CreateView):
    model = PriceList
    form_class = PriceListForm
    success_message = "%(name)s was created successfully"


class PriceListUpdateView(SuccessMessageMixin, PassRequestToFormViewMixin, UpdateView):
    model = PriceList
    form_class = PriceListForm
    success_message = "%(name)s was edited successfully"
