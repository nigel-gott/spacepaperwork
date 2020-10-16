import json
import jsonpickle


def main():
    with open("misc_data/chat.json", "r") as json_chat_file:
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
                corp = words[1]
                without_corp_and_command = words[2:]
                character = " ".join(without_corp_and_command)
                if content.lower().startswith("!addign"):
                    if author_id not in discord_id_to_characters:
                        discord_id_to_characters[author_id] = {}
                    print(f"Adding {character} to {author_id}")
                    discord_id_to_characters[author_id][character] = corp
                if content.lower().startswith("!removeign"):
                    if author_id not in discord_id_to_characters:
                        discord_id_to_characters[author_id] = {}
                    print(f"Removing {character} to {author_id}")
                    if character not in discord_id_to_characters[author_id]:
                        unknown_removes.append(f"{author_id}, {message['id']}, {character}")
                    else:
                        discord_id_to_characters[author_id].pop(character, None)
        with open("misc_data/discord_id_to_char.json", "w") as out_file:
            out_file.write(jsonpickle.encode(discord_id_to_characters, indent=4))

        character_models = []
        next_pk = 1
        with open("misc_data/characters.json", "w") as out_file:
            for discord_id, character_to_corp in discord_id_to_characters.items():

                for character, corp in character_to_corp.items():
                    character_models.append({
                        "model": "core.character",
                        "pk": next_pk,
                        "fields": {
                            "discord_id": discord_id,
                            "ingame_name": character,
                            "discord_username": author_info[discord_id]['discord_name'],
                            "discord_avatar_url": author_info[discord_id]['avatar_url'],
                            "corp": corp.upper()
                        }
                    })
                    next_pk = next_pk + 1
            out_file.write(jsonpickle.encode(character_models, indent=4))


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
