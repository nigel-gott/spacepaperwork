from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from goosetools.industry.cron.lookup_ship_prices import import_price_list
from goosetools.pricing.forms import EventForm, PriceListForm
from goosetools.pricing.models import DataSet, ItemMarketDataEvent
from goosetools.utils import PassRequestToFormViewMixin


def pricing_data_dashboard(request):

    from_date = request.GET.get("from_date", None)
    to_date = request.GET.get("to_date", None)
    pricelist_id = request.GET.get("pricelist_id", None)
    params = []
    if from_date is not None:
        params.append(f"from_date={from_date}")
    if to_date is not None:
        params.append(f"to_date={to_date}")
    if pricelist_id is not None:
        params.append(f"pricelist_id={pricelist_id}")
        pricelist = get_object_or_404(DataSet, pk=pricelist_id)
    else:
        pricelist = DataSet.objects.get(default=True)

    pricelist.access_controller.can_view(request.gooseuser, strict=True)

    if not from_date and not to_date:
        endpoint_url = reverse("pricing:latestitemmarketdataevent-list")
    else:
        endpoint_url = reverse("pricing:itemmarketdataevent-list")

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
                "ajax_url": endpoint_url + param_string,
                "latest_checked": not from_date and not to_date,
                "price_list_id": pricelist.id,
                "graph_url": reverse("item_data", args=[0]),
                "edit_url": reverse("pricing:event-update", args=[0]),
            },
            "gooseuser": request.gooseuser,
            "latest_checked": not from_date and not to_date,
            "from_date": from_date,
            "to_date": to_date,
            "pricelist": pricelist,
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
    model = DataSet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.access_controller.can_view(self.request.gooseuser, strict=True)
        if self.request.GET.get("test_google", False):
            self.object.access_controller.can_admin(self.request.gooseuser, strict=True)

            if self.object.api_type != "google_sheet":
                raise SuspiciousOperation(
                    "You can only test google_sheet api price " "lists."
                )

            context["testing_results"] = import_price_list(self.object)
        return context


class PriceListDeleteView(DeleteView):
    model = DataSet
    success_url = reverse_lazy("pricing:pricing_dashboard")
    queryset = DataSet.objects.exclude(deletable=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.access_controller.can_delete(self.request.gooseuser, strict=True)
        return context


class PriceListCreateView(SuccessMessageMixin, PassRequestToFormViewMixin, CreateView):
    model = DataSet
    form_class = PriceListForm
    success_message = "%(name)s was created successfully"


class PriceListUpdateView(SuccessMessageMixin, PassRequestToFormViewMixin, UpdateView):
    model = DataSet
    form_class = PriceListForm
    success_message = "%(name)s was edited successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.access_controller.can_edit(self.request.gooseuser, strict=True)
        return context


class EventDetailView(DetailView):
    model = ItemMarketDataEvent
    template_name = "pricing/event_detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.price_list.access_controller.can_view(
            self.request.gooseuser, strict=True
        )
        return context


class EventDeleteView(DeleteView):
    model = ItemMarketDataEvent
    template_name = "pricing/event_confirm_delete.html"
    context_object_name = "event"

    def get_success_url(self):
        price_list_id = self.object.price_list.id
        return (
            reverse_lazy("pricing:pricing_data_dashboard")
            + f"?pricelist_id={price_list_id}"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.object.price_list.access_controller.can_delete(
            self.request.gooseuser, strict=True
        )
        return context


class EventCreateView(SuccessMessageMixin, PassRequestToFormViewMixin, CreateView):
    model = ItemMarketDataEvent
    form_class = EventForm
    template_name = "pricing/event_form.html"
    success_message = "Price for %(item)s was created successfully"
    context_object_name = "event"

    def get_initial(self):
        initial = super().get_initial()
        initial["price_list"] = get_object_or_404(DataSet, pk=self.kwargs.get("pk"))
        initial["price_time"] = timezone.now().time()
        initial["price_date"] = timezone.now().date()
        return initial


class EventUpdateView(SuccessMessageMixin, PassRequestToFormViewMixin, UpdateView):
    model = ItemMarketDataEvent
    template_name = "pricing/event_form.html"
    form_class = EventForm
    success_message = "Price for %(item)s was edited successfully"
    context_object_name = "event"

    def get_initial(self):
        return {
            "price_time": self.object.time.time(),
            "price_date": self.object.time.date(),
        }
