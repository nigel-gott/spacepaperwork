from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView

# Create your views here.
from core.forms import FleetForm
from core.models import Fleet


def fleet(request):
    now = timezone.now()
    now_minus_24_hours = now - timezone.timedelta(days=1)
    active_fleets = Fleet.objects.filter(
        Q(start__gte=now_minus_24_hours) & Q(start__lte=now) & (Q(end__gt=now) | Q(end__isnull=True))).order_by('-start')
    zombie_fleets = Fleet.objects.filter(
        Q(start__lt=now_minus_24_hours) & (Q(end__gt=now) | Q(end__isnull=True))).order_by('-start')
    context = {'active_fleets': active_fleets, 'zombie_fleets': zombie_fleets}
    return render(request, 'core/fleet.html', context)


class FleetCreateView(CreateView):
    model = Fleet
    fields = '__all__'


class FleetUpdateView(UpdateView):
    model = Fleet
    fields = '__all__'


class FleetDeleteView(DeleteView):
    model = Fleet
    fields = '__all__'
