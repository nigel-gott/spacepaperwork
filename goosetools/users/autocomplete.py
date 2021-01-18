from dal import autocomplete

from goosetools.users.models import Character, GooseUser


class CharacterAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.gooseuser.is_authed_and_approved():
            return Character.objects.none()

        qs = Character.objects.all()

        fleet = self.forwarded.get("fleet", None)

        # TODO Break dependency on fleet by creating a seperate fleet member autocomplete.
        if fleet:
            chars = fleet.fleetmember_set.values("character__id")
            qs = qs.exclude(pk__in=chars)

        user = self.forwarded.get("username", None)

        if user:
            user = GooseUser.objects.get(pk=user)
            qs = qs.filter(user=user)

        if self.q:
            qs = qs.filter(ingame_name__icontains=self.q)

        return qs


class UsernameAutocomplete(autocomplete.Select2QuerySetView):
    def get_result_label(self, result):
        return result.username

    def get_selected_result_label(self, result):
        return result.username

    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.gooseuser.is_authed_and_approved():
            return GooseUser.objects.none()

        qs = GooseUser.objects.all()

        if self.q:
            qs = qs.filter(site_user__username__icontains=self.q)

        return qs
