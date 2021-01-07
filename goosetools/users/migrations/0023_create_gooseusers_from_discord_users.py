from django.db import migrations
from allauth.socialaccount.models import SocialAccount


# pylint: disable=unused-argument
def apply_migration(apps, schema_editor):
    GooseUser = apps.get_model("users", "GooseUser")
    DiscordUser = apps.get_model("users", "DiscordUser")

    for no_gooseuser_discord_user in DiscordUser.objects.filter(
        gooseuser__isnull=True
    ).all():
        if len(no_gooseuser_discord_user.username.split("#")) < 2:
            print(no_gooseuser_discord_user.username)

    for no_gooseuser_discord_user in DiscordUser.objects.filter(
        gooseuser__isnull=True
    ).all():
        user = GooseUser.objects.create(
            username=no_gooseuser_discord_user.username,
            discord_user=no_gooseuser_discord_user,
            status="approved"
            if no_gooseuser_discord_user.pre_approved
            else "unapproved",
            notes=no_gooseuser_discord_user.old_notes,
        )
        social_account = SocialAccount(
            user_id=user.pk,
            provider="discord",
            uid=no_gooseuser_discord_user.uid,
            extra_data={
                "id": no_gooseuser_discord_user.uid,
                "username": no_gooseuser_discord_user.username.split("#")[0],
                "avatar": no_gooseuser_discord_user.avatar_hash,
                "discriminator": no_gooseuser_discord_user.username.split("#")[1],
            },
        )
        social_account.save()


# pylint: disable=unused-argument
def revert_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0022_corp_full_name"),
    ]

    operations = [migrations.RunPython(apply_migration, revert_migration)]
