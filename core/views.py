from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic.edit import UpdateView

from core.forms import FleetForm, SettingsForm, JoinFleetForm
from core.models import Fleet, GooseUser, FleetMember, Character, active_fleets_query, future_fleets_query, \
    past_fleets_query

# Create your views here.

login_url = reverse_lazy('discord_login')


class SettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = 'core/settings.html'
    model = GooseUser
    form_class = SettingsForm
    success_url = '.'
    success_message = 'Settings saved!'

    def get_object(self, **kwargs):
        return get_object_or_404(GooseUser, pk=self.request.user.id)


@login_required(login_url=login_url)
def fleet(request):
    active_fleets = active_fleets_query()
    context = {'fleets': active_fleets, 'header': 'Active Fleets'}
    return render(request, 'core/fleet.html', context)


@login_required(login_url=login_url)
def fleet_past(request):
    past_fleets = past_fleets_query()
    context = {'fleets': past_fleets, 'header': 'Past Fleets'}
    return render(request, 'core/fleet.html', context)


@login_required(login_url=login_url)
def fleet_future(request):
    future_fleets = future_fleets_query()
    context = {'fleets': future_fleets, 'header': 'Future Fleets'}
    return render(request, 'core/fleet.html', context)


# zombie_fleets = Fleet.objects.filter(
#     Q(start__lte=now_minus_24_hours) & (Q(end__gt=now) | Q(end__isnull=True))).order_by('-start')
# old_fleets = Fleet.objects.filter(Q(end__lte=now)).order_by('-start')
# future_fleets = Fleet.objects.filter(
#     Q(start__gt=now))
@login_required(login_url=login_url)
def fleet_leave(request, pk):
    member = get_object_or_404(FleetMember, pk=pk)
    if member.character.discord_id == request.user.discord_uid() or request.user == member.fleet.fc:
        member.delete()
        return HttpResponseRedirect(reverse('fleet_view', args=[member.fleet.pk]))
    else:
        return HttpResponseForbidden()


@login_required(login_url=login_url)
def fleet_view(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    fleet_members = f.fleetmember_set.all()
    by_discord_id = {}
    for member in fleet_members:
        if member.character.discord_id not in by_discord_id:
            by_discord_id[member.character.discord_id] = []
        by_discord_id[member.character.discord_id].append(member)
    return render(request, 'core/fleet_view.html', {'fleet': f, 'fleet_members_by_id': by_discord_id})


@login_required(login_url=login_url)
def fleet_end(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if f.has_admin(request.user):
        f.end = timezone.now()
        f.full_clean()
        f.save()
    else:
        return HttpResponseForbidden()
    return HttpResponseRedirect(reverse('fleet'))


@login_required(login_url=login_url)
def fleet_make_admin(request, pk):
    f = get_object_or_404(FleetMember, pk=pk)
    if f.fleet.has_admin(request.user):
        f.admin_permissions = True
        f.full_clean()
        f.save()
    else:
        return HttpResponseForbidden()
    return HttpResponseRedirect(reverse('fleet_view', args=[f.fleet.pk]))


@login_required(login_url=login_url)
def fleet_remove_admin(request, pk):
    f = get_object_or_404(FleetMember, pk=pk)
    if f.fleet.has_admin(request.user):
        f.admin_permissions = False
        f.full_clean()
        f.save()
    else:
        return HttpResponseForbidden()
    return HttpResponseRedirect(reverse('fleet_view', args=[f.fleet.pk]))

@login_required(login_url=login_url)
def fleet_join(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if request.method == 'POST':
        form = JoinFleetForm(request.POST)
        if form.is_valid():
            if f.can_join(request.user):
                new_fleet = FleetMember(
                    character=form.cleaned_data['character'],
                    fleet=f,
                    joined_at=timezone.now()
                )
                new_fleet.full_clean()
                new_fleet.save()
                return HttpResponseRedirect(reverse('fleet_view', args=[pk]))
            else:
                return HttpResponseForbidden()
    else:
        form = JoinFleetForm()
    characters = non_member_chars(pk, request.user)
    form.fields['character'].queryset = characters
    return render(request, 'core/join_fleet_form.html', {'form': form, 'fleet': f})


def non_member_chars(fleet_id, user):
    uid = user.socialaccount_set.only()[0].uid
    existing = FleetMember.objects.filter(fleet=fleet_id).values('character')
    characters = Character.objects.filter(discord_id=uid).exclude(pk__in=existing)
    return characters


@login_required(login_url=login_url)
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

            new_fleet = Fleet(
                fc=request.user,
                fleet_type=form.cleaned_data['fleet_type'],
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                location=form.cleaned_data['location'],
                expected_duration=form.cleaned_data['expected_duration'],
                gives_shares_to_alts=form.cleaned_data['gives_shares_to_alts'],
                start=combined_start,
                end=combined_end,
            )
            new_fleet.full_clean()
            new_fleet.save()

            fc_member = FleetMember(
                character=form.cleaned_data['fc_character'],
                fleet=new_fleet,
                joined_at=timezone.now(),
                admin_permissions=True
            )
            fc_member.full_clean()
            fc_member.save()
            return HttpResponseRedirect(reverse('fleet'))

    else:
        now = timezone.localtime(timezone.now())
        form = FleetForm(initial={'start_date': now.date(), 'start_time': now.time()})
        form.fields['fc_character'].queryset = request.user.characters()

    return render(request, 'core/fleet_form.html', {'form': form, 'title': 'Create Fleet'})


@login_required(login_url=login_url)
def fleet_edit(request, pk):
    existing_fleet = Fleet.objects.get(pk=pk)
    if not existing_fleet.has_admin(request.user):
        return HttpResponseForbidden()
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

            existing_fleet.fc = request.user
            existing_fleet.fleet_type = form.cleaned_data['fleet_type']
            existing_fleet.name = form.cleaned_data['name']
            existing_fleet.description = form.cleaned_data['description']
            existing_fleet.location = form.cleaned_data['location']
            existing_fleet.start = combined_start
            existing_fleet.end = combined_end
            existing_fleet.expected_duration = form.cleaned_data['expected_duration']
            existing_fleet.gives_shares_to_alts = form.cleaned_data['gives_shares_to_alts']
            existing_fleet.full_clean()
            existing_fleet.save()
            return HttpResponseRedirect(reverse('fleet_view', args=[pk]))

    else:
        form = FleetForm(initial={
            'start_date': existing_fleet.start.date(),
            'start_time': existing_fleet.start.time(),
            'end_date': existing_fleet.end and existing_fleet.end.date(),
            'end_time': existing_fleet.end and existing_fleet.end.time(),
            'fleet_type': existing_fleet.fleet_type,
            'name': existing_fleet.name,
            'description': existing_fleet.description,
            'location': existing_fleet.location,
            'expected_duration': existing_fleet.expected_duration,
            'gives_shares_to_alts': existing_fleet.gives_shares_to_alts,
        })
        form.fields['fc_character'].queryset = request.user.characters()

    return render(request, 'core/fleet_form.html', {'form': form, 'title': 'Edit Fleet'})
