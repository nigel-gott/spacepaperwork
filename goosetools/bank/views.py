from django.contrib.auth import get_user_model
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from goosetools.bank.models import EggTransaction, IskTransaction, to_isk


def own_user_transactions(request):
    return HttpResponseRedirect(
        reverse("user_transactions", args=[request.user.gooseuser.pk])
    )


def user_transactions(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk)
    isk_transactions = IskTransaction.user_isk_transactions(user).order_by("time").all()
    total_isk = to_isk(0)
    for tran in isk_transactions:
        total_isk = total_isk + tran.isk
        tran.so_far = total_isk
    isk_transactions = list(isk_transactions)
    isk_transactions.reverse()
    egg_transactions = EggTransaction.user_egg_transactions(user).order_by("time").all()
    total_eggs = to_isk(0)
    for tran in egg_transactions:
        total_eggs = total_eggs + tran.eggs
        tran.so_far = total_eggs
    egg_transactions = list(egg_transactions)
    egg_transactions.reverse()

    return render(
        request,
        "bank/transactions_view.html",
        {"isk_transactions": isk_transactions, "egg_transactions": egg_transactions},
    )
