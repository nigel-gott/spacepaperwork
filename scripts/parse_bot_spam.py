import json
import jsonpickle
import glob
import os
import csv

def diff(auth_data, from_chat, auth_usernames):
    in_auth_not_chat = set(auth_data.keys())-set(from_chat.keys())
    in_chat_not_auth = set(from_chat.keys())-set(auth_data.keys())
    names = set()
    for uid in in_auth_not_chat:
        names.add(auth_usernames[uid])
    print("Discord IDs in auth data but not in chat: " + str(names))
    print(in_chat_not_auth)
    for uid, data in auth_data.items():
        if uid in from_chat:
            for char, corp in data.items():
                if char not in from_chat[uid]:
                    print("Auth data has " + uid + " - " + char)

def main():
    chat_filenames = glob.glob('discord_channel_dump/*.json')
    if len(chat_filenames) != 1:
        raise Exception("Found multiple or no chat files in sub dir: " + str(chat_filenames))
    chat_filename = chat_filenames[0]

    
    auth_data = {}
    auth_usernames = {}
    with open(os.path.join(os.curdir, "../misc_data/auth.csv"), "r", newline="") as auth_csv:
        lines = list(csv.reader(auth_csv))[1:]
        for line in lines:
            uid = line[0]
            discord_name = line[1]
            user_name = line[2]
            corp = line[3]
            if uid not in auth_data:
                auth_data[uid] = {}
            auth_data[uid][user_name] = corp 
            if uid not in auth_usernames:
                auth_usernames[uid] = discord_name
            else:
                if auth_usernames[uid] != discord_name:
                    raise Exception(f"Found mis matching username for {uid}, {discord_name} vs {auth_usernames[uid]}")
    with open("../misc_data/discord_id_to_char_auth.json", "w") as out_file:
        out_file.write(jsonpickle.encode(auth_data, indent=4))
    
    with open(os.path.join(os.curdir, chat_filename), "r") as json_chat_file:
        chat = json.load(json_chat_file)
        discord_id_to_characters = {}
        unknown_removes = []
        author_info = {}
        for message in chat['messages']:
            author_id = message['author']['id']
            author_info[author_id] = {
                "discord_name": f"{message['author']['name']}#{message['author']['discriminator']}",
                "avatar_url": message['author']['avatarUrl']
            }
            content = message['content']
            if valid_command(content):
                words = content.split(" ")
                user_name = words[1]
                without_corp_and_command = words[2:]
                character = " ".join(without_corp_and_command)
                if content.lower().startswith("!addign"):
                    if author_id not in discord_id_to_characters:
                        discord_id_to_characters[author_id] = {}
                    # print(f"Adding {character} to {author_id}")
                    discord_id_to_characters[author_id][character] = user_name
                if content.lower().startswith("!removeign"):
                    if author_id not in discord_id_to_characters:
                        discord_id_to_characters[author_id] = {}
                    # print(f"Removing {character} to {author_id}")
                    if character not in discord_id_to_characters[author_id]:
                        unknown_removes.append(f"{author_id}, {message['id']}, {character}")
                    else:
                        discord_id_to_characters[author_id].pop(character, None)
        with open("../misc_data/discord_id_to_char.json", "w") as out_file:
            out_file.write(jsonpickle.encode(discord_id_to_characters, indent=4))

        diff(auth_data, discord_id_to_characters, auth_usernames)

        models = []
        next_character_pk = 1
        next_discord_user_pk = 0
        with open("../misc_data/characters.json", "w") as out_file:
            for discord_id, character_to_corp in discord_id_to_characters.items():
                avatar_url = author_info[discord_id]['avatar_url']
                avatar_hash = avatar_url.split('/')[-1].split('.')[0]
                models.append({
                    "model": "core.discorduser",
                    "pk": next_discord_user_pk,
                    "fields": {
                        "uid": discord_id,
                        "username": author_info[discord_id]['discord_name'],
                        "avatar_hash": avatar_hash,
                        "shortened_uid": False,
                        "unknown": False
                    }
                })

                for character, user_name in character_to_corp.items():
                    models.append({
                        "model": "core.character",
                        "pk": next_character_pk,
                        "fields": {
                            "discord_user": next_discord_user_pk,
                            "ingame_name": character,
                            "corp": user_name.upper()
                        }
                    })
                    next_character_pk = next_character_pk + 1
                next_discord_user_pk = next_discord_user_pk + 1
            out_file.write(jsonpickle.encode(models, indent=4))


def valid_command(content):
    split = content.lower().split(' ')
    if len(split) < 3:
        return False
    if not (split[0] == '!addign' or split[0] == '!removeign'):
        return False
    if not (split[1] == 'mean' or split[1] == 'haus' or split[1] == 'honk' or split[1] == 'xbux'):
        return False
    return True


if __name__ == "__main__":
    main()
