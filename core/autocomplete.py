from dal import autocomplete

from core.models import Character


class CharacterAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Character.objects.none()

        qs = Character.objects.all()

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
