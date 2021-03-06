from django.conf import settings
from django.db import models
from django.urls.base import reverse

from goosetools.users.models import Corp

api_choices = [("space_venmo", "space_venmo")]
if settings.GOOSEFLOCK_FEATURES:
    api_choices.append(("fog_venmo", "Fog Venmo"))


class VirtualCurrency(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(blank=True)
    corps = models.ManyToManyField(Corp, blank=True)
    api_type = models.TextField(choices=api_choices, default="space_venmo")

    def get_absolute_url(self):
        return reverse("venmo:currency-detail", kwargs={"pk": self.pk})
