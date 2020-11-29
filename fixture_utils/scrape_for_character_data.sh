#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

token=`cat ~/.secrets/.secret_discord_token`

source /opt/goosetools_venv/bin/activate

echo "======================================"
echo "Char scrape run begin!"
date
rm -rf misc_data/discord_channel_dump/
mkdir -p misc_data/discord_channel_dump
docker run --rm -v $(pwd)/misc_data/discord_channel_dump:/app/out tyrrrz/discordchatexporter:stable export -c 754139786679156807 -t $token -f Json
python3 manage.py dumpdata users.Character users.DiscordUser > misc_data/char_dump.json
python3 fixture_utils/parse_bot_spam.py
python3 manage.py loaddata characters_and_users
echo "Char scrape end!"
