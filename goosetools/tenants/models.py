from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin, TenantMixin


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


class Client(TenantMixin):
    name = models.CharField(
        max_length=100,
        help_text="The name of your organization.",
        validators=[RegexValidator("^[a-z0-9_]{1,100}$")],
    )
    owner = models.ForeignKey(
        SiteUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    paid_until = models.DateField()
    on_trial = models.BooleanField()
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True


class Domain(DomainMixin):
    pass


class GlobalItemType(models.Model):
    name = models.TextField()

    def __str__(self):
        return str(self.name)


class GlobalItemSubType(models.Model):
    item_type = models.ForeignKey(GlobalItemType, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        return str(self.name)


class GlobalItemSubSubType(models.Model):
    item_sub_type = models.ForeignKey(GlobalItemSubType, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        return str(self.name)


class GlobalItem(models.Model):
    item_type = models.ForeignKey(GlobalItemSubSubType, on_delete=models.CASCADE)
    name = models.TextField(primary_key=True)
    eve_echoes_market_id = models.TextField(null=True, blank=True, unique=True)
    cached_lowest_sell = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )


class GlobalRegion(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)


class GlobalSystem(models.Model):
    name = models.TextField(primary_key=True)
    region = models.ForeignKey(GlobalRegion, on_delete=models.CASCADE)
    jumps_to_jita = models.PositiveIntegerField(null=True, blank=True)
    security = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.region})"
