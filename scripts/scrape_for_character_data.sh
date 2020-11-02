#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

token=`cat ~/.secrets/.secret_discord_token`

rm -rf misc_data/discord_channel_dump/
mkdir -p misc_data/discord_channel_dump 
docker run --rm -it -v $(pwd)/misc_data/discord_channel_dump:/app/out tyrrrz/discordchatexporter:stable export -c 754139786679156807 -t $token -f Json
python manage.py dbbackup
python manage.py dumpdata core.Character core.DiscordUser > misc_data/char_dump.json
python scripts/parse_bot_spam.py 
python manage.py loaddata core.characters_and_users.json


