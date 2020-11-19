from django.test import TestCase

from core.models import DiscordUser


class FleetTest(TestCase):
    def test_when_avatar_hash_is_null_default_avatar_is_returned(self):
        discord_user = DiscordUser.objects.create(
            username="Test Discord User", avatar_hash=None
        )
        self.assertEqual(
            discord_user.avatar_url(),
            "https://cdn.discordapp.com/embed/avatars/1.png",
        )

    def test_when_user_has_default_discord_avatar_the_default_url_is_their_avatar_url(
        self,
    ):
        discord_user = DiscordUser.objects.create(
            username="Test Discord User",
            avatar_hash="1",  # When a user has a default avatar the hash is just a single number
        )
        self.assertEqual(
            discord_user.avatar_url(),
            "https://cdn.discordapp.com/embed/avatars/1.png",
        )

    def test_when_user_has_custom_avatar_it_is_their_avatar_url(self):
        discord_user = DiscordUser.objects.create(
            username="Test Discord User",
            avatar_hash="custom",
            uid="12345",
        )
        self.assertEqual(
            discord_user.avatar_url(),
            "https://cdn.discordapp.com/avatars/12345/custom.png",
        )
