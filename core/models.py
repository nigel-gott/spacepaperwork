import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from django.contrib import admin


def auto_str(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items() if item[0] != '_state')
        )

    cls.__str__ = __str__
    return cls


class Region(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)


class System(models.Model):
    name = models.TextField(primary_key=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)


class Corp(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)


class Character(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    ingame_name = models.TextField()
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)

    def __str__(self):
        return f"[{self.corp}]: {self.ingame_name} ({self.user.name})"


class FleetType(models.Model):
    type = models.TextField()

    def __str__(self):
        return str(self.type)


class Fleet(models.Model):
    fc = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.TextField()
    fleet_type = models.ForeignKey(FleetType, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.name)


class FleetMember(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(blank=True, null=True)
    left_at = models.DateTimeField(blank=True, null=True)


