from django.urls import path

from goosetools.core.views import core_home

app_name = "core"


urlpatterns = [
    path("", core_home, name="home"),
]
