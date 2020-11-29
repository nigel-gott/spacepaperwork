from dal import autocomplete

from goosetools.industry.models import Ship


class ShipAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Ship.objects.none()

        qs = Ship.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
