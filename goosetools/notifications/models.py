from abc import ABC, abstractmethod

from django.db import models
from django.db.models.query_utils import Q
from django.urls.base import reverse, reverse_lazy
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
            rendered_n = NOTIFICATION_TYPES[n.type].render(n)
            rendered_n.id = n.id
            rendered_notifications.append(rendered_n)
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
    def send(self, user):
        pass


class UnStackablePermissionNotification(NotificationType):
    def __init__(self, permission, notification_type, pre_rendered) -> None:
        self.permission = permission
        self.notification_type = notification_type
        self.pre_rendered = pre_rendered
        super().__init__()

    def send(self, _=None):
        Notification.objects.update_or_create(
            type=self.notification_type,
            permission=GoosePermission.objects.get(name=self.permission),
            defaults={"created_at": timezone.now()},
        )

    def dismiss(self, _=None):
        Notification.objects.filter(
            type=self.notification_type, permission__name=self.permission
        ).delete()

    def render(self, _):
        return self.pre_rendered


class StackableUserNotification(NotificationType):
    def __init__(self, notification_type) -> None:
        self.notification_type = notification_type
        super().__init__()

    def send(self, user):
        n, new = Notification.objects.get_or_create(
            type=self.notification_type,
            user=user,
        )
        n.created_at = timezone.now()
        if new:
            n.data = {"count": 1}
        else:
            n.data = {"count": n.data["count"] + 1}
        n.save()

    def dismiss_one(self, user):
        try:
            n = Notification.objects.get(type=self.notification_type, user=user)
            if n.data["count"] < 2:
                n.delete()
            else:
                n.data = {"count": n.data["count"] - 1}
                n.save()
        except Notification.DoesNotExist:
            pass

    def dismiss_all(self, user):
        Notification.objects.filter(type=self.notification_type, user=user).delete()

    def dismiss(self, n):
        self.dismiss_all(n.user)


class ContractMadeNotification(StackableUserNotification):
    def __init__(self) -> None:
        super().__init__("contract_made")

    def render(self, notification):
        count = notification.data["count"]
        plural = "s" if count > 1 else ""
        return RenderedNotification(
            f"You have {count} pending contract{plural}.",
            "hourglass_empty",
            reverse("contracts"),
        )


class ContractRequestedNotification(StackableUserNotification):
    def __init__(self) -> None:
        super().__init__("contract_requested")

    def render(self, notification):
        count = notification.data["count"]
        plural = "s" if count > 1 else ""
        return RenderedNotification(
            f"You have {count} requested contract{plural} to make.",
            "add_box",
            reverse("contracts"),
        )


NOTIFICATION_TYPES["discord_not_setup"] = UnStackablePermissionNotification(
    DISCORD_ADMIN_PERMISSION,
    "discord_not_setup",
    RenderedNotification(
        "Discord Integration Is Not Setup",
        "directions",
        reverse_lazy("discord_settings"),
    ),
)
NOTIFICATION_TYPES["contract_made"] = ContractMadeNotification()
NOTIFICATION_TYPES["contract_requested"] = ContractRequestedNotification()
