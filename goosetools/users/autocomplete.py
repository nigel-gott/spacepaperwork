from dal import autocomplete

from goosetools.users.models import Character, DiscordUser


class CharacterAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Character.objects.none()

        qs = Character.objects.all()

        fleet = self.forwarded.get("fleet", None)

        # TODO Break dependency on fleet by creating a seperate fleet member autocomplete.
        if fleet:
            chars = fleet.fleetmember_set.values("character__id")
            qs = qs.exclude(pk__in=chars)

        discord_username = self.forwarded.get("discord_username", None)

        if discord_username:
            discord_user = DiscordUser.objects.get(pk=discord_username)
            qs = qs.filter(discord_user=discord_user)

        if self.q:
            qs = qs.filter(ingame_name__icontains=self.q)

        return qs


class DiscordUsernameAutocomplete(autocomplete.Select2QuerySetView):
    def get_result_label(self, result):
        return result.username

    def get_selected_result_label(self, result):
        return result.username

    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Character.objects.none()

        qs = DiscordUser.objects.all()

        if self.q:
            qs = qs.filter(username__icontains=self.q)

        return qs
