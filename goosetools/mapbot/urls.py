from django.urls import path

from goosetools.mapbot.views import mapbot_index

app_name = "mapbot"

urlpatterns = [
    path("", mapbot_index, name="mapbot_index"),
]
