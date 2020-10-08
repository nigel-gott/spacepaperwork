from django.urls import path
from .views import fleet, FleetCreateView, FleetUpdateView, FleetDeleteView

urlpatterns = [
    path('', fleet, name='fleet'),
    path('fleet/create/', FleetCreateView.as_view(), name='fleet_create'),
    path('fleet/<int:pk>/update/', FleetUpdateView.as_view(), name='fleet_update'),
    path('fleet/<int:pk>/delete/', FleetDeleteView.as_view(), name='fleet_delete'),
]