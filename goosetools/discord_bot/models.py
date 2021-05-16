from django.db import models


class DiscordChannel(models.Model):
    channel_id = models.TextField()
    name = models.TextField()
