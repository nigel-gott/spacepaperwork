from django.urls import path

from .views import fleet, SettingsView, fleet_create, fleet_view, fleet_join

urlpatterns = [
    path('', fleet, name='home'),
    path('fleet/', fleet, name='fleet'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('fleet/create/', fleet_create, name='fleet_create'),
    path('fleet/<int:pk>/', fleet_view, name='fleet_view'),
    path('fleet/join/<int:pk>/', fleet_join, name='fleet_join'),
    path('fleet/end/<int:pk>/', fleet_view, name='fleet_end'),
    path('fleet/edit/<int:pk>/', fleet_view, name='fleet_edit'),
]