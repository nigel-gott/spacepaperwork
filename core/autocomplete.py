from dal import autocomplete

from core.models import Character, DiscordUser, FleetAnom, FleetMember, Item, ItemFilterGroup, ItemSubSubType, ItemSubType, ItemType, System


class SystemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return System.objects.none()

        qs = System.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class ItemTypeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return ItemType.objects.none()

        qs = ItemType.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class ItemSubTypeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return ItemSubType.objects.none()

        qs = ItemSubType.objects.all()

        item_type = self.forwarded.get('item_type', None)

        if item_type:
            item_type = ItemType.objects.get(pk=item_type)
            qs = qs.filter(item_type=item_type)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class ItemSubSubTypeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return ItemSubSubType.objects.none()

        qs = ItemSubSubType.objects.all()

        item_type = self.forwarded.get('item_type', None)

        if item_type:
            item_type = ItemType.objects.get(pk=item_type)
            qs = qs.filter(item_sub_type__item_type=item_type)

        item_sub_type = self.forwarded.get('item_sub_type', None)

        if item_sub_type:
            item_sub_type = ItemSubType.objects.get(pk=item_sub_type)
            qs = qs.filter(item_sub_type=item_sub_type)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class ItemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Item.objects.none()

        qs = Item.objects.all()

        item_type = self.forwarded.get('item_type', None)

        if item_type:
            item_type = ItemType.objects.get(pk=item_type)
            qs = qs.filter(item_type__item_sub_type__item_type=item_type)

        item_sub_type = self.forwarded.get('item_sub_type', None)

        if item_sub_type:
            item_sub_type = ItemSubType.objects.get(pk=item_sub_type)
            qs = qs.filter(item_type__item_sub_type=item_sub_type)

        item_sub_sub_type = self.forwarded.get('item_sub_sub_type', None)

        if item_sub_sub_type:
            item_sub_sub_type = ItemSubSubType.objects.get(pk=item_sub_sub_type)
            qs = qs.filter(item_type=item_sub_sub_type)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class CharacterAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Character.objects.none()

        qs = Character.objects.all()

        fleet = self.forwarded.get('fleet', None)

        if fleet:
            chars = FleetMember.objects.filter(fleet=fleet).values('character__id')
            qs = qs.exclude(pk__in=chars)

        discord_username = self.forwarded.get('discord_username', None)

        if discord_username:
            discord_user = DiscordUser.objects.get(pk=discord_username)
            qs = qs.filter(discord_user=discord_user)

        if self.q:
            qs = qs.filter(ingame_name__icontains=self.q)

        return qs


class DiscordUsernameAutocomplete(autocomplete.Select2QuerySetView):
    def get_result_label(self, item):
        return item.username

    def get_selected_result_label(self, item):
        return item.username

    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Character.objects.none()

        qs = DiscordUser.objects.all()

        if self.q:
            qs = qs.filter(username__icontains=self.q)

        return qs

class ItemFilterGroupAutocomplete(autocomplete.Select2ListView):

    def results(self, results):
        """Return the result dictionary."""
        return [dict(id=pk, text=human) for pk,human in results]

    def get_list(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return [] 
        
        fleet_anom = self.forwarded.get('fleet_anom', None)
        return create_ifg_choice_list(fleet_anom, self.q)



def create_ifg_choice_list(fleet_anom_id, name_filter=None):
    fleet_anom_model = FleetAnom.objects.get(id=fleet_anom_id) 
    qs = fleet_anom_model.anom_type.scored_item_filter_groups(name_filter)
    return [(q[0].pk, f"{q[0].name} - Match Score:{q[1]}") for q in qs]

