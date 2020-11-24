#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

./manage.py dbshell <<EOF
ALTER TABLE core_corp RENAME TO users_corp;
ALTER TABLE core_character RENAME TO users_character;
ALTER TABLE core_discorduser RENAME TO users_discorduser;
ALTER TABLE core_gooseuser RENAME TO users_gooseuser;
ALTER TABLE core_gooseuser_groups RENAME TO users_gooseuser_groups;
ALTER TABLE core_gooseuser_user_permissions RENAME TO users_gooseuser_user_permissions;
ALTER TABLE core_region RENAME TO core_region;
ALTER TABLE core_system RENAME TO core_system;
ALTER TABLE core_stackedinventoryitem RENAME TO items_stackedinventoryitem;
ALTER TABLE core_item RENAME TO items_item;
ALTER TABLE core_itemlocation RENAME TO items_itemlocation;
ALTER TABLE core_station RENAME TO items_station;
ALTER TABLE core_junkeditem RENAME TO items_junkeditem;
ALTER TABLE core_itemtype RENAME TO items_itemtype;
ALTER TABLE core_itemsubtype RENAME TO items_itemsubtype;
ALTER TABLE core_itemsubsubtype RENAME TO items_itemsubsubtype;
ALTER TABLE core_inventoryitem RENAME TO items_inventoryitem;
ALTER TABLE core_contract RENAME TO contracts_contract;
ALTER TABLE core_isktransaction RENAME TO bank_isktransaction;
ALTER TABLE core_eggtransaction RENAME TO bank_eggtransaction;
ALTER TABLE core_corphanger RENAME TO items_corphanger;
ALTER TABLE core_killmail RENAME TO fleets_killmail;
ALTER TABLE core_anomtype RENAME TO fleets_anomtype;
ALTER TABLE core_fleetanom RENAME TO fleets_fleetanom;
ALTER TABLE core_solditem RENAME TO market_solditem;
ALTER TABLE core_characterlocation RENAME TO items_characterlocation;
ALTER TABLE core_marketorder RENAME TO market_marketorder;
ALTER TABLE core_transferlog RENAME TO ownership_transferlog;
ALTER TABLE core_lootgroup RENAME TO ownership_lootgroup;
ALTER TABLE core_lootbucket RENAME TO ownership_lootbucket;
ALTER TABLE core_lootshare RENAME TO ownership_lootshare;
ALTER TABLE core_itemmarketdataevent RENAME TO pricing_itemmarketdataevent;
DROP TABLE core_itemfilter;
DROP TABLE core_itemfiltergroup;

TRUNCATE TABLE django_migrations;
EOF

./manage.py migrate --fake
