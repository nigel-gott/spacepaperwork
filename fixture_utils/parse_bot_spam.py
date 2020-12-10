import csv
import glob
import json
import os
from typing import Dict

import jsonpickle


class Character:
    def __init__(self, pk, ingame_name, corp, discord_user_pk):
        self.pk = pk
        self.ingame_name = ingame_name
        self.corp = corp.upper()
        self.discord_user_pk = discord_user_pk

    def __str__(self):
        return (
            f"pk({self.pk}), ingame_name({self.ingame_name}), "
            "corp({self.corp}), discord_user_pk({self.discord_user_pk})"
        )

    def __eq__(self, obj):
        return (
            isinstance(obj, Character)
            and obj.pk == self.pk
            and obj.ingame_name == self.ingame_name
            and obj.corp == self.corp
            and self.discord_user_pk == obj.discord_user_pk
        )


class DiscordUser:
    def __init__(self, pk, uid, avatar_hash, username, pre_approved):
        self.pk = pk
        self.uid = uid
        self.avatar_hash = avatar_hash
        self.username = username
        self.characters = {}
        self.pre_approved = pre_approved

    def add_character(self, character):
        if character.ingame_name in self.characters:
            raise Exception("Dup char " + character.ingame_name)
        self.characters[character.ingame_name] = character

    def __str__(self):
        return (
            f"pk({self.pk}), uid({self.uid}), hash({self.avatar_hash}), "
            "username({self.username}), chars({self.characters}), pre({self.pre_approved})"
        )

    def __eq__(self, obj):
        return (
            isinstance(obj, DiscordUser)
            and obj.pk == self.pk
            and obj.uid == self.uid
            and obj.avatar_hash == self.avatar_hash
            and self.username == obj.username
            and self.pre_approved == obj.pre_approved
        )


def load_existing_models():
    with open(
        os.path.join(os.curdir, "misc_data/char_dump.json"), "r"
    ) as existing_models_file:
        existing_models = json.load(existing_models_file)
        existing_characters = {}
        existing_users = {}
        users_by_pk = {}
        next_character_pk = 1
        next_discord_user_pk = 0
        for model in existing_models:
            if model["model"].lower() == "users.discorduser":
                fields = model["fields"]
                uid = fields["uid"]
                if uid in existing_characters:
                    raise Exception("Duplicate " + uid)
                existing_users[uid] = DiscordUser(
                    model["pk"],
                    fields["uid"],
                    fields["avatar_hash"],
                    fields["username"],
                    fields["pre_approved"],
                )
                users_by_pk[model["pk"]] = existing_users[uid]
                next_discord_user_pk = max(model["pk"] + 1, next_discord_user_pk)
        for model in existing_models:
            if model["model"].lower() == "users.character":
                fields = model["fields"]
                ingame_name = fields["ingame_name"]
                if ingame_name in existing_characters:
                    raise Exception("Duplicate " + ingame_name)
                char = Character(
                    model["pk"],
                    fields["ingame_name"],
                    fields["corp"],
                    fields["discord_user"],
                )
                existing_characters[ingame_name] = char
                users_by_pk[fields["discord_user"]].add_character(char)
                next_character_pk = max(model["pk"] + 1, next_character_pk)
        return (
            existing_characters,
            existing_users,
            next_character_pk,
            next_discord_user_pk,
        )


def load_kris_dump(chars, users, char_pk, user_pk):
    with open(
        os.path.join(os.curdir, "misc_data/auth.csv"), "r", newline=""
    ) as auth_csv:
        lines = list(csv.reader(auth_csv))[1:]
        for line in lines:
            uid = line[0]
            discord_name = line[1]
            ingame_name = line[2]
            corp = line[3]
            if uid not in users:
                users[uid] = DiscordUser(user_pk, uid, None, discord_name, True)
                user_pk = user_pk + 1

            if ingame_name not in chars:
                chars[ingame_name] = Character(
                    char_pk, ingame_name, corp, users[uid].pk
                )
                users[uid].add_character(chars[ingame_name])
                char_pk = char_pk + 1

    return chars, users, char_pk, user_pk


def parse_chat_data(chat):
    discord_id_to_characters: Dict[str, Dict[str, str]] = {}
    unknown_removes = []
    author_info = {}
    for message in chat["messages"]:
        author_id = message["author"]["id"]
        author_name = message["author"]["name"]
        author_discriminator = message["author"]["discriminator"]
        author_info[author_id] = {
            "discord_name": f"{author_name}#{author_discriminator}",
            "avatar_url": message["author"]["avatarUrl"],
        }
        content = message["content"]
        if valid_command(content):
            words = content.split(" ")
            user_name = words[1]
            without_corp_and_command = words[2:]
            character = " ".join(without_corp_and_command)
            if content.lower().startswith("!addign"):
                if author_id not in discord_id_to_characters:
                    discord_id_to_characters[author_id] = {}
                discord_id_to_characters[author_id][character] = user_name
            if content.lower().startswith("!removeign"):
                if author_id not in discord_id_to_characters:
                    discord_id_to_characters[author_id] = {}
                if character not in discord_id_to_characters[author_id]:
                    unknown_removes.append(f"{author_id}, {message['id']}, {character}")
                else:
                    discord_id_to_characters[author_id].pop(character, None)
    return discord_id_to_characters, author_info


def load_and_parse_chat_data():
    chat_filenames = glob.glob("misc_data/discord_channel_dump/*general-bot-spam*.json")
    if len(chat_filenames) != 1:
        raise Exception(
            "Found multiple or no chat files in sub dir: " + str(chat_filenames)
        )
    chat_filename = chat_filenames[0]
    with open(os.path.join(os.curdir, chat_filename), "r") as json_chat_file:
        chat = json.load(json_chat_file)
        return parse_chat_data(chat)


def load_chat_data(chars, users, char_pk, user_pk):
    discord_id_to_characters, author_info = load_and_parse_chat_data()
    for uid, chat_data in discord_id_to_characters.items():
        if uid not in users:
            new_user = DiscordUser(
                user_pk,
                uid,
                url_to_hash(author_info[uid]["avatar_url"]),
                author_info[uid]["discord_name"],
                True,
            )
            users[uid] = new_user
            user_pk = user_pk + 1
        elif users[uid].avatar_hash is None:
            new_user = DiscordUser(
                users[uid].pk,
                uid,
                url_to_hash(author_info[uid]["avatar_url"]),
                author_info[uid]["discord_name"],
                True,
            )
            new_user.characters = users[uid].characters
            users[uid] = new_user
        else:
            new_user = DiscordUser(
                users[uid].pk,
                uid,
                url_to_hash(author_info[uid]["avatar_url"]),
                author_info[uid]["discord_name"],
                True,
            )
            new_user.characters = users[uid].characters
            if new_user != users[uid]:
                print(f"Diff!\n{new_user}\n{users[uid]}")
                users[uid] = new_user

        for ingame_name, corp in chat_data.items():
            if ingame_name not in chars:
                new_character = Character(char_pk, ingame_name, corp, users[uid].pk)
                chars[ingame_name] = new_character
                users[uid].add_character(new_character)
                char_pk = char_pk + 1
            else:
                new_character = Character(
                    chars[ingame_name].pk, ingame_name, corp, users[uid].pk
                )
                if new_character != chars[ingame_name]:
                    print(f"Diff!\n{new_character}\n{chars[ingame_name]}")
    return chars, users, char_pk, user_pk


def url_to_hash(url):
    return url.split("/")[-1].split(".")[0]


def output_models(chars, users):
    models = []
    with open("goosetools/users/fixtures/characters_and_users.json", "w") as out_file:
        for char in chars.values():
            models.append(
                {
                    "model": "users.Character",
                    "pk": char.pk,
                    "fields": {
                        "discord_user": char.discord_user_pk,
                        "ingame_name": char.ingame_name,
                        "corp": char.corp.upper(),
                    },
                }
            )
        for user in users.values():
            models.append(
                {
                    "model": "users.DiscordUser",
                    "pk": user.pk,
                    "fields": {
                        "username": user.username,
                        "uid": user.uid,
                        "avatar_hash": user.avatar_hash,
                        "pre_approved": user.pre_approved,
                    },
                }
            )

        out_file.write(jsonpickle.encode(models, indent=4))


def main():
    chars, users, next_char_pk, next_user_pk = load_existing_models()
    chars, users, next_char_pk, next_user_pk = load_chat_data(
        chars, users, next_char_pk, next_user_pk
    )
    output_models(chars, users)


def valid_command(content):
    split = content.lower().split(" ")
    if len(split) < 3:
        return False
    if not (split[0] == "!addign" or split[0] == "!removeign"):
        return False
    valid_corps = set(["mean", "haus", "honk", "xbux"])
    return split[1] in valid_corps


if __name__ == "__main__":
    main()
