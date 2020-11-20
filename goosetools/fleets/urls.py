from django.urls import path

from .views import (
    all_fleets_view,
    fleet_add,
    fleet_create,
    fleet_edit,
    fleet_end,
    fleet_future,
    fleet_join,
    fleet_leave,
    fleet_make_admin,
    fleet_past,
    fleet_remove_admin,
    fleet_view,
)

urlpatterns = [
    path("", all_fleets_view, name="home"),
    path("fleet/", all_fleets_view, name="fleet"),
    path("fleet/past", fleet_past, name="fleet_past"),
    path("fleet/future", fleet_future, name="fleet_future"),
    path("fleet/create/", fleet_create, name="fleet_create"),
    path("fleet/<int:pk>/", fleet_view, name="fleet_view"),
    path("fleet/<int:pk>/join/", fleet_join, name="fleet_join"),
    path("fleet/add/<int:pk>/", fleet_add, name="fleet_add"),
    path("fleet/make_admin/<int:pk>/", fleet_make_admin, name="fleet_make_admin"),
    path("fleet/remove_admin/<int:pk>/", fleet_remove_admin, name="fleet_remove_admin"),
    path("fleet/leave/<int:pk>/", fleet_leave, name="fleet_leave"),
    path("fleet/end/<int:pk>/", fleet_end, name="fleet_end"),
    path("fleet/edit/<int:pk>/", fleet_edit, name="fleet_edit"),
]
