#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

token=`cat ~/.secrets/.secret_discord_token`

rm -rf discord_channel_dump/
mkdir -p discord_channel_dump 
docker run --rm -it -v $(pwd)/discord_channel_dump/:/app/out tyrrrz/discordchatexporter:stable export -c 754139786679156807 -t $token -f Json

