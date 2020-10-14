import json
import jsonpickle


def main():
    with open("chat.json", "r") as json_chat_file:
        chat = json.load(json_chat_file)
        discord_id_to_characters = {}
        unknown_removes = []
        for message in chat['messages']:
            author_id = message['author']['id']
            content = message['content']
            if valid_command(content):
                if content.lower().startswith("!addign"):
                    character = " ".join(content.split(" ")[2:])
                    if author_id not in discord_id_to_characters:
                        discord_id_to_characters[author_id] = set()
                    print(f"Adding {character} to {author_id}")
                    discord_id_to_characters[author_id].add(character)
                if content.lower().startswith("!removeign"):
                    character = " ".join(content.split(" ")[2:])
                    if author_id not in discord_id_to_characters:
                        discord_id_to_characters[author_id] = set()
                    print(f"Removing {character} to {author_id}")
                    if character not in discord_id_to_characters[author_id]:
                        unknown_removes.append(f"{author_id}, {message['id']}, {character}")
                    else:
                        discord_id_to_characters[author_id].remove(character)
        with open("discord_id_to_char.json", "w") as out_file:
            out_file.write(jsonpickle.encode(discord_id_to_characters, indent=4))


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
