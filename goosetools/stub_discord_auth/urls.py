from django.urls import path

from .views import access_token_url, authorize_url, profile_url, set_uid

urlpatterns = [
    path("access_token_url", access_token_url, name="access_token_url"),
    path("authorize_url", authorize_url, name="authorize_url"),
    path("profile_url", profile_url, name="profile_url"),
    path("set_uid/<int:uid>", set_uid, name="set_uid"),
]
