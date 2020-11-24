from django.db import models


class Region(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)


class System(models.Model):
    name = models.TextField(primary_key=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    jumps_to_jita = models.PositiveIntegerField(null=True, blank=True)
    security = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.region})"
