from django.urls import path

from goosetools.core.views import (
    core_conduct,
    core_handler500,
    core_help,
    core_home,
    core_splash,
)

app_name = "core"

urlpatterns = [
    path("conduct/", core_conduct, name="conduct"),
    path("home/", core_home, name="home"),
    path("help/", core_help, name="help"),
    path("", core_splash, name="splash"),
]

handler500 = core_handler500
