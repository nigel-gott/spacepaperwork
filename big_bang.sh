#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

./manage.py migrate tenants

./manage.py dbshell <<EOF
BEGIN;
CREATE SCHEMA gooseflock;
ALTER TABLE  public.bank_eggtransaction SET SCHEMA gooseflock;
ALTER TABLE  public.bank_isktransaction SET SCHEMA gooseflock;
ALTER TABLE  public.contracts_contract SET SCHEMA gooseflock;
ALTER TABLE  public.core_region SET SCHEMA gooseflock;
ALTER TABLE  public.core_system SET SCHEMA gooseflock;
ALTER TABLE  public.django_comment_flags SET SCHEMA gooseflock;
ALTER TABLE  public.django_comments SET SCHEMA gooseflock;
ALTER TABLE  public.django_content_type SET SCHEMA gooseflock;
ALTER TABLE  public.django_migrations SET SCHEMA gooseflock;
ALTER TABLE  public.fleets_anomtype SET SCHEMA gooseflock;
ALTER TABLE  public.fleets_fleet SET SCHEMA gooseflock;
ALTER TABLE  public.fleets_fleetanom SET SCHEMA gooseflock;
ALTER TABLE  public.fleets_fleetmember SET SCHEMA gooseflock;
ALTER TABLE  public.fleets_killmail SET SCHEMA gooseflock;
ALTER TABLE  public.industry_orderlimitgroup SET SCHEMA gooseflock;
ALTER TABLE  public.industry_ship SET SCHEMA gooseflock;
ALTER TABLE  public.industry_shiporder SET SCHEMA gooseflock;
ALTER TABLE  public.items_characterlocation SET SCHEMA gooseflock;
ALTER TABLE  public.items_corphanger SET SCHEMA gooseflock;
ALTER TABLE  public.items_inventoryitem SET SCHEMA gooseflock;
ALTER TABLE  public.items_item SET SCHEMA gooseflock;
ALTER TABLE  public.items_itemlocation SET SCHEMA gooseflock;
ALTER TABLE  public.items_itemsubsubtype SET SCHEMA gooseflock;
ALTER TABLE  public.items_itemsubtype SET SCHEMA gooseflock;
ALTER TABLE  public.items_itemtype SET SCHEMA gooseflock;
ALTER TABLE  public.items_junkeditem SET SCHEMA gooseflock;
ALTER TABLE  public.items_stackedinventoryitem SET SCHEMA gooseflock;
ALTER TABLE  public.items_station SET SCHEMA gooseflock;
ALTER TABLE  public.market_marketorder SET SCHEMA gooseflock;
ALTER TABLE  public.market_solditem SET SCHEMA gooseflock;
ALTER TABLE  public.ownership_lootbucket SET SCHEMA gooseflock;
ALTER TABLE  public.ownership_lootgroup SET SCHEMA gooseflock;
ALTER TABLE  public.ownership_lootshare SET SCHEMA gooseflock;
ALTER TABLE  public.ownership_transferlog SET SCHEMA gooseflock;
ALTER TABLE  public.pricing_itemmarketdataevent SET SCHEMA gooseflock;
ALTER TABLE  public.user_forms_dynamicform SET SCHEMA gooseflock;
ALTER TABLE  public.user_forms_formquestion SET SCHEMA gooseflock;
ALTER TABLE  public.users_authconfig SET SCHEMA gooseflock;
ALTER TABLE  public.users_character SET SCHEMA gooseflock;
ALTER TABLE  public.users_corp SET SCHEMA gooseflock;
ALTER TABLE  public.users_corp_discord_roles_allowing_application SET SCHEMA gooseflock;
ALTER TABLE  public.users_corpapplication SET SCHEMA gooseflock;
ALTER TABLE  public.users_discordguild SET SCHEMA gooseflock;
ALTER TABLE  public.users_discordrole SET SCHEMA gooseflock;
ALTER TABLE  public.users_goosegroup SET SCHEMA gooseflock;
ALTER TABLE  public.users_goosepermission SET SCHEMA gooseflock;
ALTER TABLE  public.users_gooseuser SET SCHEMA gooseflock;
ALTER TABLE  public.users_groupmember SET SCHEMA gooseflock;
ALTER TABLE  public.users_grouppermission SET SCHEMA gooseflock;
ALTER TABLE  public.users_userapplication SET SCHEMA gooseflock;
COMMIT;

INSERT INTO public.tenants_client (schema_name,"name",paid_until,on_trial,created_on) VALUES
('gooseflock','gooseflock','3030-01-01',false,'2021-02-09')
;

INSERT INTO public.tenants_domain ("domain",is_primary,tenant_id) VALUES
('goosetools.com',true,1)
;
EOF


./manage.py migrate --fake
