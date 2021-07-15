from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from goosetools.pricing.forms import PriceListForm
from goosetools.pricing.models import PriceList
from goosetools.pricing.serializers import PriceListSerializer
from goosetools.users.models import BASIC_ACCESS, HasGooseToolsPerm
from goosetools.utils import PassRequestToFormViewMixin


class PriceListQuerySet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    permission_classes = [HasGooseToolsPerm.of([BASIC_ACCESS])]
    queryset = PriceList.objects.all()

    serializer_class = PriceListSerializer


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
            },
            "gooseuser": request.gooseuser,
        },
    )


class PriceListDetailView(DetailView):
    model = PriceList


class PriceListDeleteView(DeleteView):
    model = PriceList
    success_url = reverse_lazy("pricing:pricelist-list")
    queryset = PriceList.objects.exclude(deletable=False)


class PriceListCreateView(SuccessMessageMixin, PassRequestToFormViewMixin, CreateView):
    model = PriceList
    form_class = PriceListForm
    success_message = "%(name)s was created successfully"


class PriceListUpdateView(SuccessMessageMixin, PassRequestToFormViewMixin, UpdateView):
    model = PriceList
    form_class = PriceListForm
    success_message = "%(name)s was edited successfully"
