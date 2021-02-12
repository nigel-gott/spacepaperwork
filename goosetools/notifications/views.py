from django.http.response import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse

from goosetools.notifications.models import Notification
from goosetools.notifications.notification_types import NOTIFICATION_TYPES


def notification_dismiss(request, pk):
    n = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        NOTIFICATION_TYPES[n.type].dismiss(n)
        return HttpResponseRedirect(reverse("notifications:notifications-list"))
    else:
        return HttpResponseForbidden()


def notification_list(request):
    return render(
        request,
        "notifications/notification_list.html",
        {"notifications": Notification.for_user_rendered(request.gooseuser)},
    )
