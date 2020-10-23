from dal import autocomplete

from core.models import Character, FleetMember, Item, ItemSubSubType, ItemSubType, ItemType, System


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
            char = Character.objects.get(pk=discord_username)
            qs = qs.filter(discord_username__icontains=char.discord_username)

        if self.q:
            qs = qs.filter(ingame_name__icontains=self.q)

        return qs


class DiscordUsernameAutocomplete(autocomplete.Select2QuerySetView):
    def get_result_label(self, item):
        return item.discord_username

    def get_selected_result_label(self, item):
        return item.discord_username

    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Character.objects.none()

        qs = Character.objects.all().distinct('discord_username')

        if self.q:
            qs = qs.filter(discord_username__icontains=self.q)

        return qs
