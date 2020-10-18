from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic.edit import UpdateView

from core.forms import FleetAddMemberForm, FleetForm, InventoryItemForm, JoinFleetForm, LootGroupForm, LootShareForm, SettingsForm
from core.models import AnomType, Character, CharacterLocation, Fleet, FleetAnom, FleetMember, GooseUser, InventoryItem, ItemLocation, LootBucket, LootGroup, LootShare, active_fleets_query, future_fleets_query, past_fleets_query

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
    loot_buckets = f.lootbucket_set.prefetch_related('lootgroup_set').all()
    return render(request, 'core/fleet_view.html',
                  {'fleet': f, 'fleet_members_by_id': by_discord_id, 'loot_buckets': loot_buckets})


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
def fleet_add(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if not f.has_admin(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = FleetAddMemberForm(request.POST)
        if form.is_valid():
            new_fleet = FleetMember(
                character=form.cleaned_data['character'],
                fleet=f,
                joined_at=timezone.now()
            )
            new_fleet.full_clean()
            new_fleet.save()
            return HttpResponseRedirect(reverse('fleet_view', args=[pk]))
    else:
        form = FleetAddMemberForm()
    return render(request, 'core/add_fleet_form.html', {'form': form, 'fleet': f})


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
    characters = Character.objects.filter(
        discord_id=uid).exclude(pk__in=existing)
    return characters


# Two types needed - one without bucket which makes it, one which adds group to existing bucket
# Buckets group up all shares in underlying groups and split all items in underlying groups by total shares
@login_required(login_url=login_url)
def loot_group_create(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if not f.has_admin(request.user):
        return HttpResponseForbidden()
    new_bucket = LootBucket(fleet=f)
    new_bucket.save()
    return loot_group_add(request, pk, new_bucket.pk)


@login_required(login_url=login_url)
def loot_share_add(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    if not loot_group.fleet.has_admin(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = LootShareForm(request.POST)
        if form.is_valid():
            ls = LootShare(
                character=form.cleaned_data['character'],
                loot_group=loot_group,
                share_quantity=form.cleaned_data['share_quantity'],
                flat_percent_cut=form.cleaned_data['flat_percent_cut']
            )
            ls.full_clean()
            ls.save()
            return HttpResponseRedirect(reverse('loot_group_view', args=[pk]))
    else:
        form = LootShareForm(
            initial={'share_quantity': 1, 'flat_percent_cut': 0})
    return render(request, 'core/loot_share_form.html', {'form': form, 'title': 'Add New Loot Share'})


@login_required(login_url=login_url)
def loot_share_delete(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.loot_group.fleet().has_admin(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        group_pk = loot_share.loot_group.pk
        loot_share.delete()
        return HttpResponseRedirect(reverse('loot_group_view', args=[group_pk]))
    else:
        return HttpResponseNotAllowed()


@login_required(login_url=login_url)
def loot_share_edit(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.loot_group.fleet().has_admin(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = LootShareForm(request.POST)
        if form.is_valid():
            loot_share.character = form.cleaned_data['character']
            print(form.cleaned_data['share_quantity'])
            loot_share.share_quantity = form.cleaned_data['share_quantity']
            loot_share.flat_percent_cut = form.cleaned_data['flat_percent_cut']
            loot_share.full_clean()
            loot_share.save()
            return HttpResponseRedirect(reverse('loot_group_view', args=[loot_share.loot_group.pk]))
    else:
        form = LootShareForm(
            initial={'share_quantity': loot_share.share_quantity, 'flat_percent_cut': loot_share.flat_percent_cut, 'character': loot_share.character})
    return render(request, 'core/loot_share_form.html', {'form': form, 'title': 'Edit Loot Share'})


@login_required(login_url=login_url)
def loot_share_add_fleet_members(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    if request.method == 'POST':
        for fleet_member in loot_group.fleet_anom.fleet.fleetmember_set.all():
            LootShare.objects.get_or_create(
                character=fleet_member.character,
                loot_group=loot_group,
                defaults={'share_quantity': 1, 'flat_percent_cut': 0}
            )
    return HttpResponseRedirect(reverse('loot_group_view', args=[pk]))


@login_required(login_url=login_url)
def loot_group_add(request, fleet_pk, loot_bucket_pk):
    f = get_object_or_404(Fleet, pk=fleet_pk)
    loot_bucket = get_object_or_404(LootBucket, pk=loot_bucket_pk)
    if request.method == 'POST':
        form = LootGroupForm(request.POST)
        if form.is_valid():
            # Form will let you specify anom/km/other
            # depending on mode, a anom/km/other info will be created
            # also can come with participation filled in and items filled in all on one form
            spawned = timezone.now()

            if form.cleaned_data['loot_source'] == LootGroupForm.ANOM_LOOT_GROUP:
                anom_type = AnomType.objects.get_or_create(
                    level=form.cleaned_data['anom_level'],
                    type=form.cleaned_data['anom_type'],
                    faction=form.cleaned_data['anom_faction']
                )[0]
                anom_type.full_clean()
                anom_type.save()
                fleet_anom = FleetAnom(
                    fleet=f,
                    anom_type=anom_type,
                    time=spawned,
                    system=form.cleaned_data['anom_system'],
                )
                fleet_anom.full_clean()
                fleet_anom.save()

                new_group = LootGroup(
                    bucket=loot_bucket,
                    fleet_anom=fleet_anom
                )
                new_group.full_clean()
                new_group.save()

            return HttpResponseRedirect(reverse('fleet_view', args=[fleet_pk]))

    else:
        form = LootGroupForm()

    return render(request, 'core/loot_group_form.html', {'form': form, 'title': 'Start New Loot Group'})


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
        form = FleetForm(
            initial={'start_date': now.date(), 'start_time': now.time()})
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

            existing_fleet.fc = existing_fleet.fc
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
        form.fields['fc_character'].queryset = existing_fleet.fc.characters()

    return render(request, 'core/fleet_form.html', {'form': form, 'title': 'Edit Fleet'})


@login_required(login_url=login_url)
def loot_group_view(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    by_discord_id = {}
    for loot_share in loot_group.lootshare_set.all():
        id = loot_share.character.discord_id
        if id not in by_discord_id:
            by_discord_id[id] = []
        by_discord_id[id].append(loot_share)
    return render(request, 'core/loot_group_view.html',
                  {'loot_group': loot_group, 'loot_shares_by_discord_id': by_discord_id})


@login_required(login_url=login_url)
def item_add(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    if not loot_group.fleet().has_admin(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            char_loc = CharacterLocation.objects.get_or_create(
                character=form.cleaned_data['character'],
                station=None
            )
            loc = ItemLocation.objects.get_or_create(
                character_location=char_loc[0],
                corp_hanger=None
            )
            item = InventoryItem(
                location=loc[0],
                loot_group=loot_group,
                item=form.cleaned_data['item'],
                quantity=form.cleaned_data['quantity'],
                remaining_quantity=form.cleaned_data['quantity']
            )
            item.full_clean()
            item.save()
            return HttpResponseRedirect(reverse('loot_group_view', args=[pk]))
    else:
        form = InventoryItemForm()
    return render(request, 'core/loot_item_form.html', {'form': form, 'title': 'Add New Item'})


@login_required(login_url=login_url)
def item_edit(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            char_loc = CharacterLocation.objects.get_or_create(
                character=form.cleaned_data['character'],
                station=None
            )[0]
            loc = ItemLocation.objects.get_or_create(
                character_location=char_loc,
                corp_hanger=None
            )

            item.location = loc[0]
            item.item = form.cleaned_data['item']
            item.quantity = form.cleaned_data['quantity']
            item.full_clean()
            item.save()
            return HttpResponseRedirect(reverse('loot_group_view', args=[item.loot_group.pk]))
    else:
        form = InventoryItemForm(
            initial={
                'item':item.item,
                'quantity':item.quantity,
                'character':item.location.character_location.character
            }
        )
    return render(request, 'core/loot_item_form.html', {'form': form, 'title': 'Edit Item'})

@login_required(login_url=login_url)
def item_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        group_pk = item.loot_group.pk
        item.delete()
        return HttpResponseRedirect(reverse('loot_group_view', args=[group_pk]))
    else:
        return HttpResponseNotAllowed()
