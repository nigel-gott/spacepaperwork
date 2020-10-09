from django.conf.urls import url
from django.urls import path, include
from .views import fleet, FleetCreateView, FleetUpdateView, FleetDeleteView, SettingsView

urlpatterns = [
    path('fleets/', fleet, name='fleet'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('fleet/create/', FleetCreateView.as_view(), name='fleet_create'),
    path('fleet/<int:pk>/update/', FleetUpdateView.as_view(), name='fleet_update'),
    path('fleet/<int:pk>/delete/', FleetDeleteView.as_view(), name='fleet_delete'),
]