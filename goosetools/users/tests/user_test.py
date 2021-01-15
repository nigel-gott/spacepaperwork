from allauth.socialaccount.models import SocialAccount
from django.test import TestCase

from goosetools.tenants.models import SiteUser
from goosetools.users.models import GooseUser


class FleetTest(TestCase):
    def test_when_avatar_hash_is_null_default_avatar_is_returned(self):
        s = SiteUser.create("Test Goose User#1")
        user = GooseUser.objects.create(
            site_user=s,
            username="Test Goose User#1",
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
        s = SiteUser.create("Test Goose User#1")
        user = GooseUser.objects.create(
            site_user=s,
            username="Test Goose User#1",
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
        s = SiteUser.create("Test Goose User#1")
        user = GooseUser.objects.create(
            site_user=s,
            username="Test Goose User#12345",
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
