import sys

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.edit import FormView, UpdateView, DeleteView

# Create your views here.
from django_tables2 import SingleTableView

from core.forms import FleetForm, SettingsForm
from core.models import Fleet, GooseUser
from core.tables import FleetTable


class SettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = 'core/settings.html'
    model = GooseUser
    form_class = SettingsForm
    success_url = '.'
    success_message = 'Settings saved!'

    def get_object(self, **kwargs):
        return get_object_or_404(GooseUser, pk=self.request.user.id)


@login_required(login_url='/accounts/discord/login/')
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


class FleetListView(SingleTableView):
    model = Fleet
    template_name = "core/fleet.html"
    table_class = FleetTable


@login_required(login_url='/accounts/discord/login/')
def fleet_create(request):
    if request.method == 'POST':
        form = FleetForm(request.POST)
        if form.is_valid():
            combined_start = timezone.make_aware(timezone.datetime.combine(form.cleaned_data['start_date'],
                                                                           form.cleaned_data['start_time']))

            new_fleet = Fleet(fc=form.cleaned_data['fc'],
                              fleet_type=form.cleaned_data['fleet_type'],
                              name=form.cleaned_data['name'],
                              start=combined_start)
            new_fleet.full_clean()
            new_fleet.save()
            return HttpResponseRedirect('/fleets/')

    else:
        now = timezone.localtime(timezone.now())
        form = FleetForm(initial={'fc': request.user.id, 'start_date': now.date(), 'start_time': now.time()})

    return render(request, 'core/fleet_form.html', {'form': form})


class FleetCreateView(LoginRequiredMixin, FormView):
    template_name = "core/fleet_form.html"
    form_class = FleetForm


class FleetUpdateView(LoginRequiredMixin, UpdateView):
    model = Fleet
    fields = '__all__'


class FleetDeleteView(LoginRequiredMixin, DeleteView):
    model = Fleet
    fields = '__all__'
