from django.urls import path

from goosetools.tenants.views import ClientCreate, help_page, pricing, splash

app_name = "tenants"


urlpatterns = [
    path("", splash, name="splash"),
    path("help", help_page, name="help"),
    path("pricing", pricing, name="pricing"),
    path("signup", ClientCreate.as_view(), name="client-create"),
]
