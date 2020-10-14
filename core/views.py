from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic.edit import UpdateView

from core.forms import FleetForm, SettingsForm, JoinFleetForm
from core.models import Fleet, GooseUser, FleetMember, Character


# Create your views here.


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
    active_fleets = active_fleets_query()
    context = {'fleets': active_fleets, 'num_active_fleets': len(active_fleets)}
    return render(request, 'core/fleet.html', context)


def active_fleets_query():
    now = timezone.now()
    now_minus_24_hours = now - timezone.timedelta(days=1)
    active_fleets = \
        Fleet.objects.filter(
            Q(start__gte=now_minus_24_hours) & Q(start__lte=now) & (Q(end__gt=now) | Q(end__isnull=True))).order_by(
            '-start')
    return active_fleets


# zombie_fleets = Fleet.objects.filter(
#     Q(start__lte=now_minus_24_hours) & (Q(end__gt=now) | Q(end__isnull=True))).order_by('-start')
# old_fleets = Fleet.objects.filter(Q(end__lte=now)).order_by('-start')
# future_fleets = Fleet.objects.filter(
#     Q(start__gt=now))

@login_required(login_url='/accounts/discord/login/')
def fleet_view(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    fleet_members = f.fleetmember_set.all()
    return render(request, 'core/fleet_view.html', {'fleet': f, 'fleet_members': fleet_members})


@login_required(login_url='/accounts/discord/login/')
def fleet_join(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if request.method == 'POST':
        form = JoinFleetForm(request.POST)
        if form.is_valid():
            new_fleet = FleetMember(fleet=f,
                                    joined_at=timezone.now()
                                    )
            new_fleet.full_clean()
            new_fleet.save()
            return HttpResponseRedirect('/fleet/' + pk)

    else:
        form = JoinFleetForm()
    form.fields['character'].queryset = Character.objects.filter(user=request.user)
    return render(request, 'core/join_fleet_form.html', {'form': form, 'fleet':f})


@login_required(login_url='/accounts/discord/login/')
def fleet_create(request):
    if request.method == 'POST':
        form = FleetForm(request.POST)
        if form.is_valid():
            combined_start = timezone.make_aware(timezone.datetime.combine(form.cleaned_data['start_date'],
                                                                           form.cleaned_data['start_time']))
            if form.cleaned_data['end_date']:
                combined_end = timezone.make_aware(timezone.datetime.combine(form.cleaned_data['end_date'],
                                                                             form.cleaned_data['end_time']))
            else:
                combined_end = None

            new_fleet = Fleet(fc=request.user,
                              fleet_type=form.cleaned_data['fleet_type'],
                              name=form.cleaned_data['name'],
                              description=form.cleaned_data['description'],
                              location=form.cleaned_data['location'],
                              start=combined_start,
                              end=combined_end,
                              )
            new_fleet.full_clean()
            new_fleet.save()
            return HttpResponseRedirect('/fleet/')

    else:
        now = timezone.localtime(timezone.now())
        form = FleetForm(initial={'start_date': now.date(), 'start_time': now.time()})

    return render(request, 'core/fleet_form.html', {'form': form})
