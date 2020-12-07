from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

login_url = reverse_lazy("discord_login")


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "market/403.html")


@login_required(login_url=login_url)
def mapbot_index(request):
    return render(request, "mapbot/index.html", {"mapbot_host": settings.MAPBOT_HOST})
