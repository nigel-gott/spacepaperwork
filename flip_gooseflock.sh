#!/bin/bash
# set -euo
# IFS=$'\n\t'

is_on=`cat .env | grep "GOOSEFLOCK_FEATURES=on"`

if [ -z "$is_on" ]
then
    echo "Flipping to on"
    awk -F"=" -v OFS='=' '/GOOSEFLOCK_FEATURES/{$2="on";print;next}1' .env > .tempenv && mv .tempenv .env
else
    echo "Flipping to off"
    awk -F"=" -v OFS='=' '/GOOSEFLOCK_FEATURES/{$2="off";print;next}1' .env > .tempenv && mv .tempenv .env
fi
