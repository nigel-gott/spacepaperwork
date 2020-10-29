import json
import sys
from _pydecimal import ROUND_UP
from decimal import Decimal
from math import floor

import django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.forms.formsets import formset_factory
from django.http import (HttpResponseForbidden, HttpResponseNotAllowed,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic.edit import UpdateView
from djmoney.money import Money
from moneyed.localization import format_money

from core.forms import CharacterForm, DeleteItemForm, DepositEggsForm, FleetAddMemberForm, FleetForm, InventoryItemForm, ItemMoveAllForm, JoinFleetForm, LootGroupForm, LootJoinForm, LootShareForm, SelectFilterForm, SellItemForm, SettingsForm, SoldItemForm
from core.models import AnomType, Character, CharacterLocation, Contract, DiscordUser, EggTransaction, Fleet, FleetAnom, FleetMember, GooseUser, InventoryItem, IskTransaction, Item, ItemFilterGroup, ItemLocation, JunkedItem, LootBucket, LootGroup, LootShare, MarketOrder, SoldItem, TransferLog, active_fleets_query, future_fleets_query, past_fleets_query, to_isk
from django.forms.forms import Form
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from core.autocomplete import create_ifg_choice_list

# Create your views here.

login_url = reverse_lazy('discord_login')


@login_required(login_url=login_url)
def settings_view(request):
    goose_user = request.user
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            messages.success(request, "Updated your settings!")
            goose_user.default_character = form.cleaned_data['default_character']
            goose_user.timezone = form.cleaned_data['timezone']
            goose_user.broker_fee = form.cleaned_data['broker_fee']
            goose_user.transaction_tax = form.cleaned_data['transaction_tax']
            goose_user.full_clean()
            goose_user.save()
            return HttpResponseRedirect(reverse('settings'))
    else:
        form = SettingsForm(
            initial={
                'default_character': goose_user.default_character,
                'timezone': goose_user.timezone,
                'broker_fee': goose_user.broker_fee,
                'transaction_tax': goose_user.transaction_tax,
            })

    form.fields['default_character'].queryset = Character.objects.filter(
        discord_user=goose_user.discord_user)
    return render(request, 'core/settings.html', {'form': form})


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
    if member.character.discord_user == request.user.discord_user or request.user == member.fleet.fc:
        member.delete()
        return HttpResponseRedirect(reverse('fleet_view', args=[member.fleet.pk]))
    else:
        return forbidden(request)


@login_required(login_url=login_url)
def fleet_view(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    fleet_members = f.fleetmember_set.all()
    by_discord_user = {}
    for member in fleet_members:
        if member.character.discord_user.id not in by_discord_user:
            by_discord_user[member.character.discord_user.id] = []
        by_discord_user[member.character.discord_user.id].append(member)
    loot_buckets = f.lootbucket_set.prefetch_related('lootgroup_set').all()
    return render(request, 'core/fleet_view.html',
                  {'fleet': f, 'fleet_members_by_id': by_discord_user, 'loot_buckets': loot_buckets})


@login_required(login_url=login_url)
def fleet_end(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if f.has_admin(request.user):
        f.end = timezone.now()
        f.full_clean()
        f.save()
    else:
        return forbidden(request)
    return HttpResponseRedirect(reverse('fleet'))


@login_required(login_url=login_url)
def fleet_make_admin(request, pk):
    f = get_object_or_404(FleetMember, pk=pk)
    if f.fleet.has_admin(request.user):
        f.admin_permissions = True
        f.full_clean()
        f.save()
    else:
        return forbidden(request)
    return HttpResponseRedirect(reverse('fleet_view', args=[f.fleet.pk]))


@login_required(login_url=login_url)
def fleet_remove_admin(request, pk):
    f = get_object_or_404(FleetMember, pk=pk)
    if f.fleet.has_admin(request.user):
        f.admin_permissions = False
        f.full_clean()
        f.save()
    else:
        return forbidden(request)
    return HttpResponseRedirect(reverse('fleet_view', args=[f.fleet.pk]))

@login_required(login_url=login_url)
def fleet_add(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if not f.has_admin(request.user):
        return forbidden(request)
    if request.method == 'POST':
        form = FleetAddMemberForm(request.POST)
        if form.is_valid():
            character = form.cleaned_data['character']
            manual_character = form.cleaned_data['manual_character']
            if manual_character and not character:
                character = create_manual_user(manual_character, form.cleaned_data['manual_discord_username'])
            if f.member_can_be_added(character):
                new_fleet_member = FleetMember(
                    character=character,
                    fleet=f,
                    joined_at=timezone.now()
                )
                new_fleet_member.full_clean()
                new_fleet_member.save()
                return HttpResponseRedirect(reverse('fleet_view', args=[pk]))
            else:
                messages.error(request, "You cannot add an alt to this fleet")
                return forbidden(request)
    else:
        form = FleetAddMemberForm(initial={
            'fleet':f.id
        })
    existing_members = f.fleetmember_set.values('character__id')
    form.fields['character'].queryset = Character.objects.exclude(id__in=existing_members)
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
                messages.error(request, "You cannot join this fleet with that character. Maybe you are already a member or this fleet doesn't allow alts?")
                return HttpResponseRedirect(reverse('fleet_view', args=[pk]))
    else:
        form = JoinFleetForm(initial={
            'character': request.user.default_character
        })
    characters = non_member_chars(pk, request.user)
    form.fields['character'].queryset = characters

    return render(request, 'core/join_fleet_form.html', {'form': form, 'fleet': f})


def non_member_chars(fleet_id, user):
    existing = FleetMember.objects.filter(fleet=fleet_id).values('character')
    characters = Character.objects.filter(
        discord_user=user.discord_user).exclude(pk__in=existing)
    return characters


# Two types needed - one without bucket which makes it, one which adds group to existing bucket
# Buckets group up all shares in underlying groups and split all items in underlying groups by total shares
@login_required(login_url=login_url)
def loot_group_create(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if not f.has_admin(request.user):
        return forbidden(request)
    return loot_group_add(request, pk, False)


def non_participation_chars(loot_group, user):
    existing = LootShare.objects.filter(loot_group=loot_group, character__discord_user=user.discord_user).values('character')
    return user.characters().exclude(pk__in=existing)

def forbidden(request):
    return HttpResponseForbidden(render(request, 'core/403.html'))

@login_required(login_url=login_url)
def loot_share_join(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    if request.method == 'POST':
        form = LootJoinForm(request.POST)
        if form.is_valid():
            selected_character = form.cleaned_data['character']
            if selected_character not in request.user.characters():
                messages.error(request, f"{selected_character} is not your Character, you cannot join the loot group with it.")
                return forbidden(request)

            if not loot_group.can_join(selected_character):
                messages.error(request, f"{selected_character} is not allowed to join this group.")
                return forbidden(request)

            ls = LootShare(
                character=selected_character,
                loot_group=loot_group,
                share_quantity=1,
                flat_percent_cut=0
            )
            ls.full_clean()
            ls.save()
            return HttpResponseRedirect(reverse('loot_group_view', args=[pk]))
    else:
        can_still_join = non_participation_chars(loot_group, request.user) 
        if len(can_still_join) == 0: 
            messages.error(request, f"You have no more characters that can join this loot group. Don't worry you have probably already been added check below to make sure!")
            return HttpResponseRedirect(reverse('loot_group_view', args=[pk]))
        if loot_group.has_share(request.user) and not loot_group.still_can_join_alts(request.user):
            messages.error(request, f"You cannot join with more characters as the fleet doesn't allow alts to have shares.")
            return HttpResponseRedirect(reverse('loot_group_view', args=[pk]))
        default_char = request.user.default_character
        if default_char not in can_still_join:
            default_char = can_still_join[0]
        form = LootJoinForm(
            initial={'character':default_char})
        form.fields['character'].queryset = can_still_join
    return render(request, 'core/loot_join_form.html', {'form': form, 'title': 'Add Your Participation', 'loot_group':loot_group})


def create_manual_user(manual_character, manual_discord_username):
    user, created = DiscordUser.objects.get_or_create(
        username=manual_discord_username
    )

    character = Character(
        discord_user=user, 
        ingame_name=manual_character, 
        corp_id="UNKNOWN", 
        verified=False)
    character.full_clean()
    character.save()
    return character

@login_required(login_url=login_url)
def loot_share_add(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    if not loot_group.has_admin(request.user):
        return forbidden(request)
    if request.method == 'POST':
        form = LootShareForm(request.POST)
        if form.is_valid():
            character = form.cleaned_data['character']
            manual_character = form.cleaned_data['manual_character']
            if manual_character and not character:
                character = create_manual_user(manual_character, form.cleaned_data['manual_discord_username'])
            ls = LootShare(
                character=character,
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
        return forbidden(request)
    if request.method == 'POST':
        group_pk = loot_share.loot_group.pk
        loot_share.delete()
        return HttpResponseRedirect(reverse('loot_group_view', args=[group_pk]))
    else:
        return forbidden(request)


@login_required(login_url=login_url)
def loot_share_edit(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.loot_group.fleet().has_admin(request.user):
        return forbidden(request)
    if request.method == 'POST':
        form = LootShareForm(request.POST)
        if form.is_valid():
            loot_share.character = form.cleaned_data['character']
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
    if loot_bucket_pk:
        loot_bucket = get_object_or_404(LootBucket, pk=loot_bucket_pk)
    if request.method == 'POST':
        form = LootGroupForm(request.POST)
        if form.is_valid():
            # Form will let you specify anom/km/other
            # depending on mode, a anom/km/other info will be created
            # also can come with participation filled in and items filled in all on one form
            spawned = timezone.now()

            if form.cleaned_data['loot_source'] == LootGroupForm.ANOM_LOOT_GROUP:
                try:
                    anom_type = AnomType.objects.get_or_create(
                        level=form.cleaned_data['anom_level'],
                        type=form.cleaned_data['anom_type'],
                        faction=form.cleaned_data['anom_faction']
                    )[0]
                    anom_type.full_clean()
                    anom_type.save()
                except ValidationError as e:
                    form.add_error(None, e)
                    return render(request, 'core/loot_group_form.html', {'form': form, 'title': 'Start New Loot Group'})
                fleet_anom = FleetAnom(
                    fleet=f,
                    anom_type=anom_type,
                    time=spawned,
                    system=form.cleaned_data['anom_system'],
                )
                fleet_anom.full_clean()
                fleet_anom.save()

                if not loot_bucket_pk:
                    loot_bucket = LootBucket(
                        fleet=f
                    )
                    loot_bucket.save()

                new_group = LootGroup(
                    bucket=loot_bucket,
                    fleet_anom=fleet_anom
                )
                new_group.full_clean()
                new_group.save()


            return HttpResponseRedirect(reverse('loot_group_view', args=[new_group.id]))

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
            initial={
                'start_date': now.date(),
                'start_time': now.time(),
                'fc_character': request.user.default_character})

        form.fields['fc_character'].queryset = request.user.characters()

    return render(request, 'core/fleet_form.html', {'form': form, 'title': 'Create Fleet'})


@login_required(login_url=login_url)
def fleet_edit(request, pk):
    existing_fleet = Fleet.objects.get(pk=pk)
    if not existing_fleet.has_admin(request.user):
        return forbidden(request)
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
    by_discord_user = {}
    for loot_share in loot_group.lootshare_set.all():
        discord_user = loot_share.character.discord_user.id
        if discord_user not in by_discord_user:
            by_discord_user[discord_user] = []
        by_discord_user[discord_user].append(loot_share)
    return render(request, 'core/loot_group_view.html',
                  {'loot_group': loot_group, 'loot_shares_by_discord_id': by_discord_user})

@transaction.atomic
@login_required(login_url=login_url)
def reject_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        form = Form(request.POST)
        if form.is_valid() and contract.can_accept_or_reject(request.user):
            contract.status = 'rejected'
            log = []
            for item in contract.inventoryitem_set.all():
                log.append({
                    'id':item.id,
                    'item':str(item),
                    'quantity':item.quantity,
                    'status':item.status(),
                    'loot_group_id':item.loot_group and item.loot_group.id,
                })
            contract.log=json.dumps(log, cls=ComplexEncoder)
            contract.full_clean()
            contract.save()
            contract.inventoryitem_set.update(contract=None)
    return HttpResponseRedirect(reverse('view_contract', args=[pk]))

@transaction.atomic
@login_required(login_url=login_url)
def accept_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        form = Form(request.POST)
        if form.is_valid() and contract.can_accept_or_reject(request.user):

            contract.status = 'accepted'
            char_loc, _ = CharacterLocation.objects.get_or_create(
                character=contract.to_char,
                system=contract.system
            )
            loc, _ = ItemLocation.objects.get_or_create(
                character_location=char_loc,
                corp_hanger=None
            )
            log = []
            for item in contract.inventoryitem_set.all():
                log.append({
                    'id':item.id,
                    'item':str(item),
                    'quantity':item.quantity,
                    'status':item.status(),
                    'loot_group_id':item.loot_group and item.loot_group.id,
                })
            contract.log=json.dumps(log, cls=ComplexEncoder)
            contract.full_clean()
            contract.save()
            contract.inventoryitem_set.update(contract=None, location=loc)
    return HttpResponseRedirect(reverse('view_contract', args=[pk]))

@transaction.atomic
@login_required(login_url=login_url)
def create_contract_item(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            if not item.has_admin(request.user):
                messages.error(request, f"You do not have permission to move item {item}")
                return forbidden(request)
            if item.quantity == 0:
                messages.error(request, f"You cannot contract an item which is being or has been sold")
                return forbidden(request)
            system = form.cleaned_data['system']
            character = form.cleaned_data['character']

            contract = Contract(
                from_user=request.user,
                to_char=character,
                system=system,
                created=timezone.now(),
                status='pending'
            )
            contract.full_clean()
            contract.save()
            item.contract = contract
            item.full_clean()
            item.save()
            return HttpResponseRedirect(reverse('contracts')) 
    else:
        form = ItemMoveAllForm(
            )
    return render(request, 'core/item_move_all.html', {'form': form, 'title': f'Contract Individual Item: {item}'})
@transaction.atomic
@login_required(login_url=login_url)
def create_contract_for_fleet(request, fleet_pk, loc_pk):
    f = get_object_or_404(Fleet, pk=fleet_pk)
    loc = get_object_or_404(ItemLocation, pk=loc_pk)
    if request.method == 'POST':
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            if not loc.has_admin(request.user):
                messages.error(request, f"You do not have permission to move items from {loc}")
                return forbidden(request)
            system = form.cleaned_data['system']
            character = form.cleaned_data['character']
            items_in_location = InventoryItem.objects.filter(contract__isnull=True, loot_group__fleet_anom__fleet=f, location=loc, quantity__gt=0, marketorder__isnull=True, solditem__isnull=True)
            if items_in_location.count() == 0:
                messages.error(request, "You have no items to contract :'(") 
                return forbidden(request)

            contract = Contract(
                from_user=request.user,
                to_char=character,
                system=system,
                created=timezone.now(),
                status='pending'
            )
            contract.full_clean()
            contract.save()
            items_in_location.update(contract=contract)
            return HttpResponseRedirect(reverse('contracts')) 
    else:
        form = ItemMoveAllForm(
            )
    return render(request, 'core/item_move_all.html', {'form': form, 'title': f'Contract Your Items From Fleet:{f} {loc}'})


@transaction.atomic
@login_required(login_url=login_url)
def item_move_all(request):
    if request.method == 'POST':
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            system = form.cleaned_data['system']
            character = form.cleaned_data['character']
            all_your_items = InventoryItem.objects.filter(contract__isnull=True, location__character_location__character__discord_user=request.user.discord_user, quantity__gt=0, marketorder__isnull=True, solditem__isnull=True)
            if all_your_items.count() == 0:
                messages.error(request, "You have no items to contract :'(") 
                return forbidden(request)

            contract = Contract(
                from_user=request.user,
                to_char=character,
                system=system,
                created=timezone.now(),
                status='pending'
            )
            contract.full_clean()
            contract.save()
            all_your_items.update(contract=contract)
            return HttpResponseRedirect(reverse('contracts')) 
    else:
        form = ItemMoveAllForm()
            
    return render(request, 'core/item_move_all.html', {'form': form, 'title': 'Contract All Your Items'})


@login_required(login_url=login_url)
def item_add(request, lg_pk):
    extra=10
    InventoryItemFormset= formset_factory(InventoryItemForm,extra=0)
    loot_group = get_object_or_404(LootGroup, pk=lg_pk)
    ifg_pk = request.GET.get('item_filter_group',None)
    choice_list = create_ifg_choice_list(loot_group.fleet_anom.id)
    if not ifg_pk:
        ifg_pk = choice_list[0][0]
    item_filter_group = get_object_or_404(ItemFilterGroup, pk=ifg_pk)
    if not loot_group.fleet().has_admin(request.user):
        return forbidden(request)
    initial = [{'item_filter_group':ifg_pk,'quantity': 1} for x in range(0,extra)]
    if request.method == 'POST':
        formset = InventoryItemFormset(request.POST, request.FILES, initial=initial)
        char_form = CharacterForm(request.POST)
        if formset.is_valid() and char_form.is_valid():
            character = char_form.cleaned_data['character']
            count = 0
            for form in formset:
                item = form.cleaned_data['item']
                quantity = form.cleaned_data['quantity']
                if item and quantity:
                    char_loc = CharacterLocation.objects.get_or_create(
                        character=character,
                        system=None
                    )
                    loc = ItemLocation.objects.get_or_create(
                        character_location=char_loc[0],
                        corp_hanger=None
                    )
                    item, created = InventoryItem.objects.get_or_create(
                        location=loc[0],
                        loot_group=loot_group,
                        item=item,
                        defaults = {
                            'quantity':quantity
                        }
                    )
                    count = count + quantity 
                    if not created:
                        if item.can_edit():
                            item.quantity = item.quantity + quantity 
                            item.full_clean()
                            item.save()
                        else:
                            new_item = InventoryItem(
                                location=loc[0],
                                loot_group=loot_group,
                                item=item,
                                quantity=quantity,
                            )
                            new_item.full_clean()
                            new_item.save()
            add_another = request.POST.get('add_another', False)
            if add_another:
                messages.success(request, f"Added {count} items") 
                return HttpResponseRedirect(reverse('item_add', args=[lg_pk]))
            else:
                return HttpResponseRedirect(reverse('loot_group_view', args=[lg_pk]))
    else:
        char_form = CharacterForm(initial={'character': request.user.default_character})
        char_form.fields['character'].queryset = request.user.characters()
        formset = InventoryItemFormset(
            initial=initial)
    filter_form = SelectFilterForm()
    filter_form.fields['item_filter_group'].choices = choice_list 
    filter_form.fields['item_filter_group'].initial = ifg_pk 
    filter_form.fields['fleet_anom'].initial = loot_group.fleet_anom.id 
    return render(request, 'core/loot_item_form.html', {'formset': formset, 'char_form':char_form, 'title': 'Add New Items to Loot Bucket', 'filter_form':filter_form})




@login_required(login_url=login_url)
def junk(request):
    characters = request.user.characters()
    all_junked = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None)
            junked = JunkedItem.objects.filter(item__location=loc)

            all_junked.append({
                'loc': loc,
                'junked':junked,
            })

    return render(request, 'core/junk.html', {'all_junked':all_junked})

@login_required(login_url=login_url)
def transfered_items(request):
    characters = request.user.characters()
    all_sold = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None)
            done = SoldItem.objects.filter(item__location=loc, transfered_to_participants=True)
            all_sold.append({
                'loc': loc,
                'done':done
            })

    return render(request, 'core/transfered_items.html', {'all_sold': all_sold})
@login_required(login_url=login_url)
def sold(request):
    characters = request.user.characters()
    all_sold = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None)
            sold = SoldItem.objects.filter(item__location=loc, transfered_to_participants=False)
            all_sold.append({
                'loc': loc,
                'sold':sold,
            })

    return render(request, 'core/sold.html', {'all_sold': all_sold})

@login_required(login_url=login_url)
def orders(request):
    characters = request.user.characters()
    all_orders = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None)
            orders = MarketOrder.objects.filter(item__location=loc)
            all_orders.append({
                'loc': loc,
                'orders':orders,
            })

    return render(request, 'core/orders.html', {'all_orders': all_orders})


@login_required(login_url=login_url)
def view_contract(request,pk):
    contract = get_object_or_404(Contract, pk=pk)
    if contract.status == "pending":
        log = []
        for item in contract.inventoryitem_set.all():
            log.append({
                'id':item.id,
                'item':str(item),
                'quantity':item.quantity,
                'status':item.status(),
                'loot_group_id':item.loot_group and item.loot_group.id,
            })
    else:
        log = json.loads(contract.log)

    return render(request, 'core/contract_view.html', {
        'contract': contract,
        'log': log
        })

@login_required(login_url=login_url)
def contracts(request):
    return render(request, 'core/contracts.html', {
        'my_contracts': Contract.objects.filter(from_user__discord_user=request.user.discord_user, status='pending'), 
        'to_me_contracts': list(Contract.objects.filter(to_char__discord_user=request.user.discord_user, status='pending')), 
        'old_my_contracts': Contract.objects.filter(from_user__discord_user=request.user.discord_user).exclude(status='pending'), 
        'old_to_me_contracts': Contract.objects.filter(to_char__discord_user=request.user.discord_user).exclude(status='pending'), 
        })

@login_required(login_url=login_url)
def items(request):
    characters = request.user.characters()
    return render_item_view(request,characters,True, 'Your Items Waiting To Be Sold Or Contracted to a Seller')

@login_required(login_url=login_url)
def items_grouped(request):
    items = Item.objects.annotate(total=Sum('inventoryitem__quantity')).filter(total__gt=0).order_by('item_type')
    return render(request, 'core/grouped_items.html', {'items': items, 'title':"All Not Sold Items In Goosetools Grouped Together"})

@login_required(login_url=login_url)
def all_items(request):
    characters = Character.objects.annotate(cc=Sum('characterlocation__itemlocation__inventoryitem__quantity')).filter(cc__gt=0)
    return render_item_view(request,characters,False, 'All Items')

def render_item_view(request, characters, show_contract_all, title):
    all_items = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            items_by_fleet = {}
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None)
            items = InventoryItem.objects.filter(contract__isnull=True, location=loc, quantity__gt=0)
            fleets = items.values('loot_group__fleet_anom__fleet').distinct()
            for fleet in fleets:
                fleet_id = fleet['loot_group__fleet_anom__fleet']
                items_by_fleet[fleet_id] = items.filter(loot_group__fleet_anom__fleet=fleet_id)
            if char_loc.has_admin(request.user):
                fleet_count = fleets.count()
            else:
                fleet_count = 0

            all_items.append({
                'total_in_loc': items.count() + fleet_count, 
                'loc': loc,
                'items_by_fleet':items_by_fleet,
            })

    return render(request, 'core/items.html', {'all_items': all_items, 'show_contract_all':show_contract_all, 'title':title})

@login_required(login_url=login_url)
def view_transfer_log(request, pk):
    item = get_object_or_404(TransferLog, pk=pk)
    return render(request, 'core/view_transfer_log.html', {'log': item, 'explaination':json.loads(item.explaination)}) 

@login_required(login_url=login_url)
def item_view(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    return render(request, 'core/item_view.html', {'item': item}) 

@login_required(login_url=login_url)
def item_minus(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    if not inventory_item.has_admin(request.user):
        return forbidden(request)
    if request.method == 'POST':
        result = inventory_item.add(-1)
        if not result:
            messages.error(request, "Failed to increment item")
    return HttpResponseRedirect(reverse('loot_group_view', args=[inventory_item.loot_group.id]))
@login_required(login_url=login_url)
def item_plus(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    if not inventory_item.has_admin(request.user):
        return forbidden(request)
    if request.method == 'POST':
        result = inventory_item.add(1)
        if not result:
            messages.error(request, "Failed to increment item")
    return HttpResponseRedirect(reverse('loot_group_view', args=[inventory_item.loot_group.id]))

@login_required(login_url=login_url)
def loot_share_plus(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.has_admin(request.user):
        return forbidden(request)
    if request.method == 'POST':
        loot_share.increment()
    return HttpResponseRedirect(reverse('loot_group_view', args=[loot_share.loot_group.id]))
    
@login_required(login_url=login_url)
def loot_share_minus(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.has_admin(request.user):
        return forbidden(request)
    if request.method == 'POST':
        loot_share.decrement()
    return HttpResponseRedirect(reverse('loot_group_view', args=[loot_share.loot_group.id]))

@login_required(login_url=login_url)
def item_edit(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.user):
        return forbidden(request)
    if not item.can_edit():
        messages.error(request, "Cannot edit an item once market orders have been made for it. PM @thejanitor on discord to make admin edits for you.")
        return forbidden(request)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            char_loc = CharacterLocation.objects.get_or_create(
                character=form.cleaned_data['character'],
                system=None
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
                'item': item.item,
                'quantity': item.quantity,
                'character': item.location.character_location.character
            }
        )
    return render(request, 'core/loot_item_form.html', {'form': form, 'title': 'Edit Item'})


@login_required(login_url=login_url)
@transaction.atomic
def order_sold(request, pk):
    order = get_object_or_404(MarketOrder, pk=pk)
    if not order.has_admin(request.user):
        return forbidden(request)

    if request.method == 'POST':
        form = SoldItemForm(request.POST)
        if form.is_valid():
            quantity_remaining = form.cleaned_data['quantity_remaining']
            quantity_sold = order.quantity - quantity_remaining
            if quantity_sold <= 0:
                messages.error(request, "Cannot sell nothing or more than the order quantity")
                return forbidden(request)
            transaction_tax_percent = order.transaction_tax/100
            gross_profit = order.listed_at_price * quantity_sold 
            transaction_tax = Money(amount=round((gross_profit * transaction_tax_percent).amount,2), currency="EEI")
            item = order.item
            transaction_tax_line = IskTransaction(
                item = item,
                time = timezone.now(),
                isk = -transaction_tax,
                quantity = quantity_sold,
                transaction_type = "transaction_tax",
            )
            transaction_tax_line.full_clean()
            transaction_tax_line.save()
            profit_line = IskTransaction(
                item = item,
                time = timezone.now(),
                isk = gross_profit,
                quantity = quantity_sold,
                transaction_type = "external_market_gross_profit",
            )
            profit_line.full_clean()
            profit_line.save()
            sold_item, sold_item_created = SoldItem.objects.get_or_create(
                item=item,
                defaults = {
                    'quantity':quantity_sold,
                    'sold_via':'external',
                }
            )
            if not sold_item_created:
                sold_item.quantity = sold_item.quantity + quantity_sold
                sold_item.full_clean()
                sold_item.save()

            if quantity_remaining == 0:
                order.delete()
            else:
                order.quantity = quantity_remaining
                order.full_clean()
                order.save()
            return HttpResponseRedirect(reverse('orders'))

    else:
        form = SoldItemForm(initial={
            'quantity_remaining':0
        })
    return render(request, 'core/order_sold.html', {'form': form, 'title': 'Mark Order As Sold', 'order':order})

@login_required(login_url=login_url)
@transaction.atomic
def deposit_eggs(request):
    if request.user.has_pending_deposit():
        messages.error(request, f"Cannot deposit again until previously deposited items have been approved.")
        return forbidden(request)

    if not request.user.can_deposit():
        messages.error(request, f"Nothing to deposit")
        return forbidden(request)
    
    to_deposit_qs = SoldItem.objects.filter(item__location__character_location__character__discord_user=request.user.discord_user, deposited_into_eggs=False)
    to_deposit_list = list(to_deposit_qs)
    total = to_deposit_qs.aggregate(result=Sum('item__isktransaction__isk'))['result']
    count = to_deposit_qs.count()
    if request.method == 'POST':
        form = DepositEggsForm(request.POST)
        if form.is_valid():
            current_now = timezone.now()
            for sold_item in to_deposit_list:
                isk = sold_item.isk_balance()
                deposit_transaction = IskTransaction(
                    item=sold_item.item,
                    quantity=sold_item.quantity,
                    time=current_now,
                    isk=-isk,
                    transaction_type="egg_deposit"
                )
                deposit_transaction.full_clean()
                deposit_transaction.save()
                egg_transaction = EggTransaction(
                    item=sold_item.item,
                    quantity=sold_item.quantity,
                    time=current_now,
                    eggs=isk,
                    debt=True,
                    counterparty_discord_username=request.user.discord_username()
                )
                egg_transaction.full_clean()
                egg_transaction.save()
            to_deposit_qs.update(deposited_into_eggs=True)
            messages.success(request, f"Marked {count} sold items as deposited into eggs, pending approval.")
            return HttpResponseRedirect(reverse('sold'))
    else:
        form = DepositEggsForm(initial={
            'deposit_command': f'$deposit {floor(total)}'
        })
    return render(request, 'core/deposit_eggs_form.html', {'form': form, 'title': 'Deposit Eggs', 'total':to_isk(total), 'count':count}) 

@login_required(login_url=login_url)
@transaction.atomic
def deposit_approved(request):
    if not request.user.has_pending_deposit():
        messages.error(request, f"Must have a pending deposit to confirm it has been approved.")
        return forbidden(request)
    to_deposit_qs = request.user.pending_deposits() 
    total = to_deposit_qs.aggregate(result=Sum('item__eggtransaction__eggs'))['result']
    count = to_deposit_qs.count()
    if request.method == 'POST':
        form = DepositEggsForm(request.POST)
        if form.is_valid():
            request.user.pending_deposits().update(deposit_approved=True)
            return HttpResponseRedirect(reverse('sold'))
    else:
        form = DepositEggsForm()
    return render(request, 'core/eggs_approved.html', {'form': form, 'title': 'Egg Deposit Approved', 'total':to_isk(total), 'count':count})


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Money):
            return format_money(obj, locale=django.utils.translation.get_language())
        if isinstance(obj, Decimal):
            return str(floor(obj)) 
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
@login_required(login_url=login_url)
@transaction.atomic
def transfer_eggs(request):
    
    if not request.user.has_pending_transfers():
        messages.error(request, f"Must have a deposited and approved eggs to transfer them.")
        return forbidden(request)
    
    if request.method == 'POST':
        form = DepositEggsForm(request.POST)
    else:
        form = None

    total_participation = {}
    explaination = {}
    to_transfer = SoldItem.objects.filter(item__location__character_location__character__discord_user=request.user.discord_user, deposited_into_eggs=True, deposit_approved=True, transfered_to_participants=False)
    current_now = timezone.now()
    total = 0
    count = 0
    for sold_item in to_transfer:
        bucket = sold_item.item.loot_group.bucket
        total_isk = sold_item.item.isk_and_eggs_balance()
        participation = bucket.calculate_participation(total_isk, sold_item.item.loot_group)
        item_id = sold_item.item.id
        explaination[item_id] = participation
        explaination[item_id]['item'] = str(sold_item.item)
        explaination[item_id]['total_isk'] = total_isk.amount 
        total = total + total_isk
        count = count + 1
        for discord_username, result in participation['participation'].items():
            isk = round(result['total_isk'],2)
            if form and form.is_valid():
                egg_transaction = EggTransaction(
                    item=sold_item.item,
                    quantity=sold_item.quantity,
                    time=current_now,
                    eggs=-isk,
                    debt=True,
                    counterparty_discord_username=request.user.discord_username()
                )
                egg_transaction.full_clean()
                egg_transaction.save()
                egg_transaction = EggTransaction(
                    item=sold_item.item,
                    quantity=sold_item.quantity,
                    time=current_now,
                    eggs=isk,
                    debt=False,
                    counterparty_discord_username=discord_username
                )
                egg_transaction.full_clean()
                egg_transaction.save()
            if discord_username in total_participation:
                total_participation[discord_username] = total_participation[discord_username]+isk
            else:
                total_participation[discord_username] = isk 

    if form and form.is_valid():
        messages.success(request, f"Transfered {total} eggs from {count} sold items to the correct participants.")
        log = TransferLog(
            user=request.user,
            time=timezone.now(),
            total=total,
            count=count,
            explaination=json.dumps(explaination, cls=ComplexEncoder)
        )
        log.full_clean()
        log.save()
        to_transfer.update(transfered_to_participants=True, transfer_log=log.id)
        return HttpResponseRedirect(reverse('sold'))
    else:
        end = ""
        command = "$bulk\n"
        commands_issued = False
        for discord_username, isk in total_participation.items():
            if discord_username != request.user.discord_username():
                commands_issued = True
                command = command + f"@{discord_username} {floor(isk.amount)}\n"
            else:
                end = end + f"Keep {floor(isk.amount)} for yourself! \n"
        if commands_issued:
            command = command + "\n\n" + end
        else:
            command = end


        form = DepositEggsForm(initial={
            'deposit_command': command 
        })
    return render(request, 'core/transfer_eggs_form.html', {'form': form, 'title': 'Transfer Eggs', 'total':total, 'count':count, 'command':command, 'explaination':explaination}) 

@login_required(login_url=login_url)
@transaction.atomic
def item_sell(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.user):
        return forbidden(request)
    
    if item.quantity == 0:
        messages.error(request, f"Cannot sell an item with 0 quantity.")
        return forbidden(request)

    if request.method == 'POST':
        form = SellItemForm(request.POST)
        if form.is_valid():
            price = form.cleaned_data['listed_at_price']
            total_isk_listed = item.quantity * price
            broker_fee_percent = form.cleaned_data['broker_fee']/100
            broker_fee = Money(amount=round(-(total_isk_listed* broker_fee_percent),2), currency="EEI")
            broker_fee = IskTransaction(
                item = item,
                time = timezone.now(),
                isk = broker_fee, 
                quantity = item.quantity,
                transaction_type = "broker_fee",
            )
            broker_fee.full_clean()
            broker_fee.save()
            sell_order = MarketOrder(
                item = item,
                internal_or_external="external",
                buy_or_sell="sell",
                quantity=item.quantity,
                listed_at_price = price,
                transaction_tax = form.cleaned_data['transaction_tax'],
                broker_fee = form.cleaned_data['broker_fee']
            )
            sell_order.full_clean()
            sell_order.save()
            item.quantity = 0
            item.save()
            return HttpResponseRedirect(reverse('items')) 
    else:
        form = SellItemForm(initial={
            'broker_fee':request.user.broker_fee,
            'transaction_tax':request.user.transaction_tax,
        })

    return render(request, 'core/sell_item.html', {'form': form, 'title': 'Sell Item', 'item':item})

@login_required(login_url=login_url)
def item_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.user):
        return forbidden(request)
    if not item.can_edit():
        messages.error(request, "Cannot delete an item once market orders have been made for it. PM @thejanitor on discord to make admin edits for you.")
        return forbidden(request)
    if request.method == 'POST':
        form = DeleteItemForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['are_you_sure']:
                group_pk = item.loot_group and item.loot_group.pk
                item.delete()
                if group_pk:
                    return HttpResponseRedirect(reverse('loot_group_view', args=[group_pk]))
                else:
                    return HttpResponseRedirect(reverse('items')) 
            else:
                messages.error(request, "Don't delete the item if you are not sure!")
                return HttpResponseRedirect(reverse('item_view', args=[item.pk]))

    else:
        form = DeleteItemForm()

    return render(request, 'core/item_delete.html', {'form': form, 'title': 'Delete Item', 'item':item})
