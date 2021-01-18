from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SiteUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[],
        error_messages={"unique": _("A user with that username already exists.")},
    )

    def has_gooseuser(self):
        return hasattr(self, "gooseuser")

    def is_approved(self):
        # pylint: disable=no-member
        return self.has_gooseuser() and self.gooseuser.is_approved()

    def is_rejected(self):
        # pylint: disable=no-member
        return self.has_gooseuser() and self.gooseuser.is_rejected()

    def discord_socialaccount(self):
        return self.socialaccount_set.get(provider="discord")

    @staticmethod
    def create(username):
        site_user = SiteUser(
            first_name="",
            last_name="",
            email="",
            password="",
            username=username,
            is_staff=False,
            is_active=True,
            date_joined=timezone.now(),
            is_superuser=False,
        )
        site_user.save()
        return site_user

    @staticmethod
    def copy_from_user(user):
        site_user, _ = SiteUser.objects.update_or_create(
            username=user.username,
            defaults={
                "is_staff": user.is_staff,
                "is_active": user.is_active,
                "date_joined": user.date_joined,
                "password": user.password or "",
                "last_login": user.last_login,
                "is_superuser": user.is_superuser,
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "email": user.email or "",
            },
        )
        user.site_user_id = site_user.id
        user.save()
        return site_user
