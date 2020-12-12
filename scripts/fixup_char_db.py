import json

from goosetools.contracts.models import Contract
from goosetools.fleets.models import FleetMember
from goosetools.industry.models import ShipOrder
from goosetools.items.models import CharacterLocation
from goosetools.ownership.models import LootShare
from goosetools.users.models import Character, CorpApplication, DiscordUser


def run():
    with open("misc_data/output.json", "r") as output_file:
        output = json.load(output_file)

        for uid, stuff in output.items():
            if stuff["new_user"]:
                print(f"Skipping {stuff}")
                continue
            discord_user = DiscordUser.objects.get(uid=uid)
            # discord_user.old_notes = stuff["notes"]
            # discord_user.sa_profile = stuff["sa_profile"]
            if stuff["voucher"]:
                pass
                # voucher = DiscordUser.objects.get(uid=stuff["voucher"])
                # discord_user.voucher = voucher
            # discord_user.save()

            for character in stuff["changed_characters"]:
                char = Character.objects.get(ingame_name=character["ingame_name"])
                assert (
                    char.discord_user == discord_user
                ), f"Data thinks {char} should be for user {discord_user} however its not"

                # corp = Corp.objects.get(name=character["corp"])
                # char.corp = corp
                # char.save()

            move_to_char = discord_user.gooseuser.default_character
            assert move_to_char
            assert move_to_char.ingame_name not in [
                c["ingame_name"] for c in stuff["removed_characters"]
            ]
            for character in stuff["removed_characters"]:
                char = Character.objects.get(ingame_name=character["ingame_name"])
                print(f"Attempting to remove {char}")
                assert CorpApplication.objects.filter(character=char).count() == 0
                assert Contract.objects.filter(to_char=char).count() == 0
                assert ShipOrder.objects.filter(recipient_character=char).count() == 0
                assert CharacterLocation.objects.filter(character=char).count() == 0

                print(
                    f"Moving {FleetMember.objects.filter(character=char).count()} fleet members"
                )
                print(
                    f"Moving {LootShare.objects.filter(character=char).count()} loot shares"
                )

                # FleetMember.objects.filter(character=char).update(
                #     character=move_to_char
                # )
                # LootShare.objects.filter(character=char).update(character=move_to_char)
