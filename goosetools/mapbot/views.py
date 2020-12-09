from django.conf import settings
from django.contrib import messages
from django.shortcuts import render


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "market/403.html")


def mapbot_index(request):
    return render(request, "mapbot/index.html", {"mapbot_host": settings.MAPBOT_HOST})
