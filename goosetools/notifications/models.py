from abc import ABC, abstractmethod

from django.db import models
from django.db.models.query_utils import Q
from django.urls.base import reverse_lazy
from django.utils import timezone

from goosetools.notifications.notification_types import NOTIFICATION_TYPES
from goosetools.users.models import DISCORD_ADMIN_PERMISSION, GoosePermission, GooseUser


class Notification(models.Model):
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE, null=True, blank=True)
    permission = models.ForeignKey(
        GoosePermission, on_delete=models.CASCADE, null=True, blank=True
    )
    type = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # type:ignore
    created_at = models.DateField(auto_now_add=True)
    priority = models.IntegerField(default=0)

    @staticmethod
    def for_user(user: GooseUser):
        permissions = user.groupmember_set.values_list(
            "group__grouppermission__permission__name", flat=True
        )
        return Notification.objects.filter(
            Q(user=user) | Q(permission__name__in=permissions)
        ).order_by("-created_at", "priority", "type")

    @staticmethod
    def for_user_rendered(user: GooseUser):
        notifications = Notification.for_user(user)
        rendered_notifications = []
        for n in notifications:
            rendered_notifications.append(NOTIFICATION_TYPES[n.type].render(n))
        return rendered_notifications


class RenderedNotification:
    def __init__(self, text: str, icon: str, action_url: str) -> None:
        self.text = text
        self.icon = icon
        self.action_url = action_url

    def as_html(self) -> str:
        return f"<a href='{self.action_url}' class='red-text'><i class='material-icons left'>{self.icon}</i>{self.text}</a>"

    def __str__(self) -> str:
        return self.as_html()


class NotificationType(ABC):
    @abstractmethod
    def render(self, notification) -> RenderedNotification:
        pass

    @abstractmethod
    def send(self):
        pass


class UnStackablePermissionNotification(NotificationType):
    def __init__(self, permission, notification_type, pre_rendered) -> None:
        self.permission = permission
        self.notification_type = notification_type
        self.pre_rendered = pre_rendered
        super().__init__()

    def send(self):
        Notification.objects.update_or_create(
            type=self.notification_type,
            permission=GoosePermission.objects.get(name=self.permission),
            defaults={"created_at": timezone.now()},
        )

    def dismiss(self, _=None):
        Notification.objects.filter(
            type=self.notification_type, permission__name=self.permission
        ).delete()

    def render(self, notification):
        self.pre_rendered.id = notification.id
        return self.pre_rendered


NOTIFICATION_TYPES["discord_not_setup"] = UnStackablePermissionNotification(
    DISCORD_ADMIN_PERMISSION,
    "discord_not_setup",
    RenderedNotification(
        "Discord Integration Is Not Setup",
        "directions",
        reverse_lazy("discord_settings"),
    ),
)
