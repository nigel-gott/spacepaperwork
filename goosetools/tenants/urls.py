from django.urls import path

from goosetools.tenants.views import splash

app_name = "tenants"


urlpatterns = [
    path("splash/", splash, name="splash"),
]
