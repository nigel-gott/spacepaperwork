from django.urls import path

from goosetools.tenants.views import ClientCreate, splash

app_name = "tenants"


urlpatterns = [
    path("", splash, name="splash"),
    path("signup", ClientCreate.as_view(), name="client-create"),
]
