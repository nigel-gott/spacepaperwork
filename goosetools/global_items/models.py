from django.db import models


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
    name = models.TextField()
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
