from dal import autocomplete

from goosetools.items.models import Item, ItemSubSubType, ItemSubType, ItemType, System


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

        item_type = self.forwarded.get("item_type", None)

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

        item_type = self.forwarded.get("item_type", None)

        if item_type:
            item_type = ItemType.objects.get(pk=item_type)
            qs = qs.filter(item_sub_type__item_type=item_type)

        item_sub_type = self.forwarded.get("item_sub_type", None)

        if item_sub_type:
            item_sub_type = ItemSubType.objects.get(pk=item_sub_type)
            qs = qs.filter(item_sub_type=item_sub_type)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class ItemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Item.objects.none()

        qs = Item.objects.all()

        item_type = self.forwarded.get("item_type", None)

        if item_type:
            item_type = ItemType.objects.get(pk=item_type)
            qs = qs.filter(item_type__item_sub_type__item_type=item_type)

        item_sub_type = self.forwarded.get("item_sub_type", None)

        if item_sub_type:
            item_sub_type = ItemSubType.objects.get(pk=item_sub_type)
            qs = qs.filter(item_type__item_sub_type=item_sub_type)

        item_sub_sub_type = self.forwarded.get("item_sub_sub_type", None)

        if item_sub_sub_type:
            item_sub_sub_type = ItemSubSubType.objects.get(pk=item_sub_sub_type)
            qs = qs.filter(item_type=item_sub_sub_type)

        faction = self.forwarded.get("faction", None)
        if faction and faction != "All":
            qs = qs.filter(
                inventoryitem__loot_group__fleet_anom__anom_type__faction=faction
            ).distinct()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.distinct()
