from django.urls import path

from goosetools.notifications.views import notification_dismiss, notification_list

app_name = "notifications"

urlpatterns = [
    path("notification/all", notification_list, name="notifications-list"),
    path(
        "notification/<int:pk>/dismiss",
        notification_dismiss,
        name="notification-dismiss",
    ),
]
