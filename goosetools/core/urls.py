from django.urls import path

from goosetools.core.views import core_home, core_splash

app_name = "core"


urlpatterns = [
    path("home/", core_home, name="home"),
    path("", core_splash, name="splash"),
]
