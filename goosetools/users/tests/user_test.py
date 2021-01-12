from allauth.socialaccount.models import SocialAccount
from django.test import TestCase

from goosetools.users.models import Character, Corp, DiscordUser, GooseUser


class FleetTest(TestCase):
    def test_when_avatar_hash_is_null_default_avatar_is_returned(self):
        discord_user = DiscordUser.objects.create(
            username="Test Goose User",
        )
        corp = Corp.objects.create(name="Test Corp")
        char = Character.objects.create(
            discord_user=discord_user, ingame_name="Test Char", corp=corp
        )
        user = GooseUser.objects.create(
            username="Test Goose User#1",
            discord_user=discord_user,
            default_character=char,
            status="approved",
        )
        SocialAccount.objects.create(
            uid="1",
            provider="discord",
            extra_data={
                "username": "Test Goose User",
                "discriminator": "1",
            },
            user_id=user.pk,
        )
        user.refresh_from_db()
        self.assertEqual(
            user.discord_avatar_url(),
            "https://cdn.discordapp.com/embed/avatars/1.png",
        )

    def test_when_user_has_default_discord_avatar_the_default_url_is_their_avatar_url(
        self,
    ):
        discord_user = DiscordUser.objects.create(
            username="Test Goose User",
        )
        corp = Corp.objects.create(name="Test Corp")
        char = Character.objects.create(
            discord_user=discord_user, ingame_name="Test Char", corp=corp
        )
        user = GooseUser.objects.create(
            username="Test Goose User#1",
            discord_user=discord_user,
            default_character=char,
            status="approved",
        )
        SocialAccount.objects.create(
            uid="1",
            provider="discord",
            extra_data={
                "username": "Test Goose User",
                "avatar": "1",  # When a user has a default avatar the hash is just a single number
                "discriminator": "1",
            },
            user=user,
        )
        user.refresh_from_db()
        self.assertEqual(
            user.discord_avatar_url(),
            "https://cdn.discordapp.com/embed/avatars/1.png",
        )

    def test_when_user_has_custom_avatar_it_is_their_avatar_url(self):
        discord_user = DiscordUser.objects.create(
            username="Test Goose User",
        )
        corp = Corp.objects.create(name="Test Corp")
        char = Character.objects.create(
            discord_user=discord_user, ingame_name="Test Char", corp=corp
        )
        user = GooseUser.objects.create(
            username="Test Goose User#12345",
            discord_user=discord_user,
            default_character=char,
            status="approved",
        )
        SocialAccount.objects.create(
            uid="1",
            provider="discord",
            extra_data={
                "username": "Test Goose User",
                "avatar": "custom",
                "discriminator": "12345",
            },
            user=user,
        )
        user.refresh_from_db()
        self.assertEqual(
            user.discord_avatar_url(),
            "https://cdn.discordapp.com/avatars/1/custom.png",
        )

    # User can set default char / fees / timezone
    # Setting timezone works
    # User cannot signup if not in database
