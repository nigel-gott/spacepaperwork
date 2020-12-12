import json


def lookup_real_uid(
    discord_id_truncated,
    users_by_uid_truncated_3dp,
    users_by_uid_truncated_2dp,
    users_by_uid_truncated_1dp,
):
    real_uid = None
    if discord_id_truncated not in users_by_uid_truncated_3dp:
        if discord_id_truncated not in users_by_uid_truncated_2dp:
            if discord_id_truncated in users_by_uid_truncated_1dp:
                real_uid = users_by_uid_truncated_1dp[discord_id_truncated]["uid"]
        else:
            real_uid = users_by_uid_truncated_2dp[discord_id_truncated]["uid"]
    else:
        real_uid = users_by_uid_truncated_3dp[discord_id_truncated]["uid"]
    return real_uid


def main():
    with open("misc_data/geeseAuthDB.json", "r") as auth_db_file:
        auth_db = json.load(auth_db_file)
        with open("misc_data/char_user_dump.json", "r") as current_dump_file:
            current_users_chars = json.load(current_dump_file)

            users_by_uid = {}
            users_by_uid_truncated_3dp = {}
            users_by_uid_truncated_2dp = {}
            users_by_uid_truncated_1dp = {}
            users_by_username = {}
            users_by_pk = {}
            for model in current_users_chars:
                if model["model"] == "users.discorduser":
                    uid = model["fields"]["uid"]
                    pk = model["pk"]
                    username = model["fields"]["username"]

                    if username in ("TEST USER 1", "TEST USER 2"):
                        continue

                    truncated_uid_3dp = (
                        uid[:-4] + str(round(float(uid[-4:]) / 1000.0)) + "000"
                    )
                    truncated_uid_2dp = (
                        uid[:-3] + str(round(float(uid[-3:]) / 100.0)) + "00"
                    )
                    truncated_uid_1dp = (
                        uid[:-2] + str(round(float(uid[-2:]) / 10.0)) + "0"
                    )
                    real_truncated_uid_1dp = uid[:-1] + "0"
                    real_truncated_uid_2dp = uid[:-2] + "00"
                    assert uid not in users_by_uid
                    assert (
                        truncated_uid_3dp not in users_by_uid_truncated_3dp
                    ), f"Already found {truncated_uid_2dp}"
                    assert (
                        truncated_uid_2dp not in users_by_uid_truncated_2dp
                    ), f"Already found {truncated_uid_2dp}"
                    assert (
                        truncated_uid_1dp not in users_by_uid_truncated_1dp
                    ), f"Already found {truncated_uid_1dp}"
                    assert (
                        real_truncated_uid_1dp not in users_by_uid_truncated_1dp
                    ), f"Already found {real_truncated_uid_1dp}"
                    assert (
                        real_truncated_uid_2dp not in users_by_uid_truncated_1dp
                    ), f"Already found {real_truncated_uid_2dp}"
                    assert pk not in users_by_pk
                    assert (
                        username not in users_by_username
                    ), f"Duplicate username {username}"

                    users_by_uid[uid] = {
                        "new_user": False,
                        "uid": uid,
                        "pk": pk,
                        "username": username,
                        "existing_characters": [],
                        "removed_characters": [],
                        "matched_characters": [],
                        "changed_characters": [],
                        "new_characters": [],
                    }
                    users_by_username[username.split("#")[0]] = users_by_uid[uid]
                    users_by_pk[pk] = users_by_uid[uid]
                    users_by_uid_truncated_3dp[truncated_uid_3dp] = users_by_uid[uid]
                    users_by_uid_truncated_2dp[truncated_uid_2dp] = users_by_uid[uid]
                    users_by_uid_truncated_1dp[truncated_uid_1dp] = users_by_uid[uid]
                    users_by_uid_truncated_1dp[real_truncated_uid_1dp] = users_by_uid[
                        uid
                    ]
                    users_by_uid_truncated_1dp[real_truncated_uid_2dp] = users_by_uid[
                        uid
                    ]

            character_to_user = {}
            for model in current_users_chars:
                if model["model"] == "users.character":
                    disord_user_pk = model["fields"]["discord_user"]
                    pk = model["pk"]
                    ingame_name = model["fields"]["ingame_name"]
                    corp = model["fields"]["corp"]

                    assert ingame_name not in character_to_user

                    character_to_user[ingame_name] = {
                        "pk": pk,
                        "discord_user_pk": disord_user_pk,
                        "ingame_name": ingame_name,
                        "corp": corp,
                    }
                    users_by_pk[disord_user_pk]["existing_characters"].append(
                        character_to_user[ingame_name]
                    )

            missing_users = []
            interesting_users = {}
            for user in auth_db:
                discord_id_wrong = str(user["DiscordId"])
                discord_id_truncated = discord_id_wrong
                username = user["DiscordName"]
                real_uid = None
                if discord_id_truncated not in users_by_uid_truncated_3dp:
                    if discord_id_truncated not in users_by_uid_truncated_2dp:
                        if discord_id_truncated not in users_by_uid_truncated_1dp:
                            if username not in users_by_username:
                                missing_users.append(user)
                                assert len(user["Characters"]) == 0
                            else:
                                real_uid = users_by_username[username]["uid"]
                        else:
                            real_uid = users_by_uid_truncated_1dp[discord_id_truncated][
                                "uid"
                            ]
                    else:
                        real_uid = users_by_uid_truncated_2dp[discord_id_truncated][
                            "uid"
                        ]
                else:
                    real_uid = users_by_uid_truncated_3dp[discord_id_truncated]["uid"]

                if real_uid:
                    existing_user = users_by_uid[real_uid]
                    existing_user["sa_profile"] = user["SaProfile"]
                    existing_user["vouchable"] = user["Vouchable"]
                    existing_user["notes"] = user["Note"] if "Note" in user else ""
                    existing_chars = existing_user["existing_characters"]

                    vouches = []
                    for vouch in user["CurrentVouches"]:
                        if str(vouch) == "350120042681073660":
                            continue
                        real_uid = lookup_real_uid(
                            str(vouch),
                            users_by_uid_truncated_3dp,
                            users_by_uid_truncated_2dp,
                            users_by_uid_truncated_1dp,
                        )
                        assert (
                            real_uid
                        ), f"Failed to lookup real uid {real_uid} for {vouch} for {user}"
                        vouches.append(real_uid)

                    existing_user["vouches"] = vouches

                    if user["Voucher"] != 0:
                        if user["Voucher"] != "350120042681073660":
                            real_uid = lookup_real_uid(
                                str(user["Voucher"]),
                                users_by_uid_truncated_3dp,
                                users_by_uid_truncated_2dp,
                                users_by_uid_truncated_1dp,
                            )
                            assert (
                                real_uid
                            ), f"Failed to lookup real uid for {real_uid} - {user['Voucher']} for {user}"
                            existing_user["voucher"] = real_uid

                    display = False
                    for char in user["Characters"]:
                        ign = char["IGN"]
                        found = False
                        for existing_char in existing_chars:
                            if ign == existing_char["ingame_name"]:
                                found = True
                                if char["Corp"] == existing_char["corp"]:
                                    existing_user["matched_characters"].append(
                                        existing_char
                                    )
                                else:
                                    display = True
                                    existing_char["new_corp"] = char["Corp"]
                                    existing_user["changed_characters"].append(
                                        existing_char
                                    )
                        if not found:
                            display = True
                            existing_user["new_characters"].append(
                                {
                                    "discord_user_pk": existing_user["pk"],
                                    "ingame_name": ign,
                                    "corp": char["Corp"],
                                }
                            )
                            print("NEW WTF - " + ign)
                    for char in existing_chars:
                        if char["ingame_name"] not in [
                            u["IGN"] for u in user["Characters"]
                        ]:
                            display = True
                            existing_user["removed_characters"].append(char)
                    if display:
                        interesting_users[real_uid] = existing_user

            for user in users_by_uid:
                if "voucher" in user:
                    assert (
                        user["uid"] in users_by_uid[user["voucher"]]["vouches"]
                    ), f"Incorrect vouch for {user}"

            with open("misc_data/output.json", "w") as output:
                output.write(json.dumps(users_by_uid, indent=4, sort_keys=True))
                print("WROTE OUTPUT TO misc_data/output.json")

            print("====== USERS IN AUTHDB AND MISSING FROM GOOSETOOLS ===========")
            print(
                {
                    x["DiscordName"] + "#" + str(x["DiscordId"]): x["Characters"]
                    for x in missing_users
                }
            )


if __name__ == "__main__":
    main()
