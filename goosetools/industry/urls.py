from django.urls import path

from goosetools.industry.views import shiporders_create, shiporders_view

app_name = "industry"

urlpatterns = [
    path("shiporders/create", shiporders_create, name="shiporders_create"),
    path("shiporders/", shiporders_view, name="shiporders_view"),
]
