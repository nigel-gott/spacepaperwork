from typing import Optional

from dal import autocomplete
from django import forms
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView

from goosetools.users.models import VENMO_ADMIN, GooseUser, has_perm
from goosetools.venmo.api.fog_venmo import FogVenmo
from goosetools.venmo.api.space_venmo import SpaceVenmo
from goosetools.venmo.api.venmo import VenmoError, VenmoUserBalance
from goosetools.venmo.forms import (
    DepositForm,
    TransferForm,
    TransferMethodForm,
    TransferMethodTypeForm,
    WithdrawForm,
)
from goosetools.venmo.models import FOG_VENMO_API_TYPE, TransferMethod, VirtualCurrency


def dashboard(request, ccy, gooseuser):
    discord_uid = gooseuser.discord_uid()
    try:
        venmo_user_balance = venmo_api(ccy).user_balance(discord_uid)
    except VenmoError:
        messages.error(request, "Failed to load your balance from venmo.")
        venmo_user_balance = VenmoUserBalance(0, 0, 0)
    context = {
        "page_data": {
            "gooseuser_id": gooseuser.id,
            "ccy": {"name": ccy.name},
            "site_prefix": f"/{request.site_prefix}",
        },
        "gooseuser": gooseuser,
        "venmo_user_balance": venmo_user_balance,
        "ccy": ccy,
        "all_ccy": VirtualCurrency.objects.all(),
    }
    return render(request, "venmo/dashboard.html", context=context)


def get_ccy(ccy: str) -> Optional[VirtualCurrency]:
    try:
        if not ccy or ccy == "default":
            return VirtualCurrency.objects.get(default=True)
        else:
            return VirtualCurrency.objects.get(name=ccy)
    except VirtualCurrency.DoesNotExist:
        return None


def other_dashboard(request, ccy, pk: int):
    gooseuser = get_object_or_404(GooseUser, pk=pk)
    ccy = get_ccy(ccy)
    if not ccy:
        messages.error(
            request,
            "No Virtual Currencies have been setup, please get your admin to make one first!",
        )
        return HttpResponseRedirect(reverse("core:home"))
    return dashboard(request, ccy, gooseuser)


def own_dashboard(request, ccy):
    ccy = get_ccy(ccy)
    if not ccy:
        messages.error(
            request,
            "No Virtual Currencies have been setup, please get your admin to make one first!",
        )
        return HttpResponseRedirect(reverse("core:home"))
    return dashboard(request, ccy, request.gooseuser)


@has_perm(perm=VENMO_ADMIN)
def pending(request, ccy):
    ccy = get_ccy(ccy)
    if not ccy:
        messages.error(
            request,
            "No Virtual Currencies have been setup, please get your admin to make one first!",
        )
        return HttpResponseRedirect(reverse("core:home"))
    return render(
        request,
        "venmo/pending.html",
        {"page-data": {"ccy": ccy_json(ccy)}, "ccy": ccy},
    )


def other_user_transactions_list(request, ccy, pk: int):
    gooseuser = get_object_or_404(GooseUser, pk=pk)
    ccy = get_ccy(ccy)
    if not ccy:
        return JsonResponse({"error": "No virtual currency found"})
    return transactions_list(ccy, gooseuser)


def transactions_list(ccy, gooseuser: GooseUser):
    return JsonResponse(
        {
            "result": venmo_api(ccy).user_transactions(gooseuser.discord_uid()),
            "ccy": ccy_json(ccy),
        }
    )


def ccy_json(ccy):
    return {
        "id": ccy.id,
        "name": ccy.name,
    }


@has_perm(perm=VENMO_ADMIN)
def pending_list(request, ccy):
    ccy = get_ccy(ccy)
    if not ccy:
        return JsonResponse({"error": "No virtual currency found"})
    return JsonResponse(
        {"result": venmo_api(ccy).pending_transactions(), "ccy": ccy_json(ccy)}
    )


def venmo_api(currency):
    if currency.api_type == FOG_VENMO_API_TYPE:
        return FogVenmo()
    else:
        return SpaceVenmo(currency)


def withdraw(request, ccy):
    ccy = get_ccy(ccy)
    if request.method == "POST":
        form = WithdrawForm(request.POST)
        if form.is_valid():
            try:
                venmo_api(ccy).withdraw(
                    request.gooseuser.discord_uid(), form.cleaned_data["quantity"]
                )
                return HttpResponseRedirect(reverse("venmo:dashboard", args=[ccy.name]))
            except VenmoError as e:
                messages.error(request, e.message)
    else:
        form = WithdrawForm()

    return render(request, "venmo/withdraw.html", {"form": form, "ccy": ccy})


def transfer(request, ccy):
    ccy = get_ccy(ccy)
    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            try:
                venmo_api(ccy).transfer(
                    request.gooseuser.discord_uid(),
                    form.cleaned_data["user"].discord_uid(),
                    form.cleaned_data["quantity"],
                )
                return HttpResponseRedirect(reverse("venmo:dashboard", args=[ccy.name]))
            except VenmoError as e:
                messages.error(request, e.message)
    else:
        form = TransferForm()

    return render(request, "venmo/transfer.html", {"form": form, "ccy": ccy})


def deposit(request, ccy):
    ccy = get_ccy(ccy)
    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            try:
                venmo_api(ccy).deposit(
                    request.gooseuser.discord_uid(),
                    form.cleaned_data["quantity"],
                    form.cleaned_data["note"],
                )
                return HttpResponseRedirect(reverse("venmo:dashboard", args=[ccy.name]))
            except VenmoError as e:
                messages.error(request, e.message)
    else:
        form = DepositForm()

    return render(request, "venmo/deposit.html", {"form": form, "ccy": ccy})


@has_perm(perm=VENMO_ADMIN)
def approve_transaction(request, ccy, pk: int):
    return update_transaction(request, ccy, pk, "complete")


@has_perm(perm=VENMO_ADMIN)
def deny_transaction(request, ccy, pk: int):
    return update_transaction(request, ccy, pk, "rejected")


def update_transaction(request, ccy, transaction_id: int, new_status: str):
    ccy = get_ccy(ccy)
    if request.method != "PUT":
        return HttpResponseForbidden()
    try:
        venmo_api(ccy).update_transaction(str(transaction_id), new_status)
        return HttpResponse()
    except VenmoError as e:
        messages.error(request, e.message)
        return HttpResponseBadRequest()


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class VirtualCurrencyListView(ListView):
    queryset = VirtualCurrency.objects.order_by("name")
    context_object_name = "currency_list"


class VirtualCurrencyForm(forms.ModelForm):
    class Meta:
        model = VirtualCurrency
        fields = ["name", "description", "corps", "withdrawal_characters", "default"]
        widgets = {
            "withdrawal_characters": autocomplete.ModelSelect2Multiple(
                url="character-autocomplete"
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["corps"].required = False

    def clean(self):
        super().clean()
        if self.instance.id:
            data = self.cleaned_data
            new_corps = data["corps"]
            deleted_corps = self.instance.corps.difference(new_corps)
            for deleted_corp in deleted_corps:
                balance = deleted_corp.virtualcurrencystorageaccount_set.get(
                    currency=self.instance
                ).balance()

                if balance != 0:
                    raise forms.ValidationError(
                        f"You cannot remove {deleted_corp} as it still has a {self.instance} balance of {balance}. Please first ensure it's balance is 0 by doing admin transfers before removing it as a corp for this currency."
                    )

    def save(self, commit=True):
        instance = super().save(commit=commit)
        for acc in instance.virtualcurrencystorageaccount_set.all():
            acc.setup()
        return instance


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class VirtualCurrencyCreateView(SuccessMessageMixin, CreateView):
    model = VirtualCurrency
    form_class = VirtualCurrencyForm
    success_message = "%(name)s was created successfully"


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class VirtualCurrencyUpdateView(SuccessMessageMixin, UpdateView):
    model = VirtualCurrency
    form_class = VirtualCurrencyForm
    success_message = "%(name)s was edited successfully"


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class VirtualCurrencyDeleteView(DeleteView):
    model = VirtualCurrency
    success_url = reverse_lazy("venmo:currency-list")

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        balance = self.get_object().balance()  # type: ignore
        if balance != 0:
            messages.error(
                request,
                f"Cannot delete a currency which has a balance of {balance}, please "
                f"zero it out using admin transactions first.",
            )
            return HttpResponseRedirect(reverse("venmo:currency-list"))
        else:
            return super().delete(request, *args, **kwargs)


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class VirtualCurrencyDetailView(DetailView):
    model = VirtualCurrency


class PassRequestToFormViewMixin:
    def get_form_kwargs(self):
        # noinspection PyUnresolvedReferences
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class TransferMethodSelectCreateView(FormView):
    form_class = TransferMethodTypeForm
    template_name = "venmo/transfermethod_select-form.html"


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class TransferMethodListView(ListView):
    queryset = TransferMethod.objects.order_by("name")
    context_object_name = "transfer_list"


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class TransferMethodDetailView(DetailView):
    model = TransferMethod


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class TransferMethodDeleteView(DeleteView):
    model = TransferMethod
    success_url = reverse_lazy("venmo:transfer-list")


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class TransferMethodCreateView(
    SuccessMessageMixin, PassRequestToFormViewMixin, CreateView
):
    model = TransferMethod
    form_class = TransferMethodForm
    success_message = "%(name)s was created successfully"


@method_decorator(has_perm(perm=VENMO_ADMIN), name="dispatch")
class TransferMethodUpdateView(
    SuccessMessageMixin, PassRequestToFormViewMixin, UpdateView
):
    model = TransferMethod
    form_class = TransferMethodForm
    success_message = "%(name)s was edited successfully"
