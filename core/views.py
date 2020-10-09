from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic.edit import FormView, UpdateView, DeleteView

# Create your views here.
from core.forms import FleetForm, SettingsForm
from core.models import Fleet, GooseUser


class SettingsView(LoginRequiredMixin, UpdateView):
    template_name = 'core/settings.html'
    model = GooseUser
    form_class = SettingsForm
    success_url = '.'

    def get_object(self, **kwargs):
        return get_object_or_404(GooseUser, pk=self.request.user.id)


def fleet(request):
    now = timezone.now()
    now_minus_24_hours = now - timezone.timedelta(days=1)
    active_fleets = Fleet.objects.filter(
        Q(start__gte=now_minus_24_hours) & Q(start__lte=now) & (Q(end__gt=now) | Q(end__isnull=True))).order_by(
        '-start')
    zombie_fleets = Fleet.objects.filter(
        Q(start__lt=now_minus_24_hours) & (Q(end__gt=now) | Q(end__isnull=True))).order_by('-start')
    context = {'active_fleets': active_fleets, 'zombie_fleets': zombie_fleets}
    return render(request, 'core/fleet.html', context)


class FleetCreateView(LoginRequiredMixin, FormView):
    template_name = "core/fleet_form.html"
    form_class = FleetForm


class FleetUpdateView(LoginRequiredMixin, UpdateView):
    model = Fleet
    fields = '__all__'


class FleetDeleteView(LoginRequiredMixin, DeleteView):
    model = Fleet
    fields = '__all__'
