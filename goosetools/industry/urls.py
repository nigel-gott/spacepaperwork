from django.urls import path
from django.urls.conf import include
from rest_framework import routers

from goosetools.industry.views import (
    ShipOrderViewSet,
    shiporders_create,
    shiporders_view,
)

app_name = "industry"


router = routers.DefaultRouter()
router.register(r"shiporder", ShipOrderViewSet)

urlpatterns = [
    path("shiporder/form_create", shiporders_create, name="shiporders_create"),
    path("shiporder/", shiporders_view, name="shiporders_view"),
    path("shiporder/", include((router.urls))),
]
