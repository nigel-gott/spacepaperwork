from django.urls import path

from .views import fleet, FleetUpdateView, FleetDeleteView, SettingsView, fleet_create, FleetListView

urlpatterns = [
    path('', FleetListView.as_view(), name='home'),
    path('fleets/', FleetListView.as_view(), name='fleet'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('fleet/create/', fleet_create, name='fleet_create'),
    path('fleet/<int:pk>/update/', FleetUpdateView.as_view(), name='fleet_update'),
    path('fleet/<int:pk>/delete/', FleetDeleteView.as_view(), name='fleet_delete'),
]