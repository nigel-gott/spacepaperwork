from django.contrib import messages
from django.shortcuts import render


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


def core_home(request):
    return render(
        request,
        "core/home.html",
    )
