#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

./manage.py dbshell <<EOF

alter table socialaccount drop constraint if exists socialaccount_social_user_id_8146e70c_fk_core_goos;
update socialaccount sa set user_id=gooseuser.site_user_id from users_gooseuser gooseuser where gooseuser.id = sa.user_id;
ALTER TABLE "socialaccount_socialaccount" ADD CONSTRAINT "socialaccount_social_user_id_8146e70c_fk_tenants_s" FOREIGN KEY ("user_id") REFERENCES "tenants_siteuser" ("id") DEFERRABLE INITIALLY DEFERRED;

BEGIN;
--
-- Create model SiteUser
--
CREATE TABLE "tenants_siteuser_groups" ("id" serial NOT NULL PRIMARY KEY, "siteuser_id" integer NOT NULL, "group_id" integer NOT NULL);
CREATE TABLE "tenants_siteuser_user_permissions" ("id" serial NOT NULL PRIMARY KEY, "siteuser_id" integer NOT NULL, "permission_id" integer NOT NULL);
CREATE INDEX "tenants_siteuser_username_f74c842b_like" ON "tenants_siteuser" ("username" varchar_pattern_ops);
ALTER TABLE "tenants_siteuser_groups" ADD CONSTRAINT "tenants_siteuser_groups_siteuser_id_group_id_404af03a_uniq" UNIQUE ("siteuser_id", "group_id");
ALTER TABLE "tenants_siteuser_groups" ADD CONSTRAINT "tenants_siteuser_gro_siteuser_id_8ca1df89_fk_tenants_s" FOREIGN KEY ("siteuser_id") REFERENCES "tenants_siteuser" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "tenants_siteuser_groups" ADD CONSTRAINT "tenants_siteuser_groups_group_id_d9edf5d1_fk_auth_group_id" FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "tenants_siteuser_groups_siteuser_id_8ca1df89" ON "tenants_siteuser_groups" ("siteuser_id");
CREATE INDEX "tenants_siteuser_groups_group_id_d9edf5d1" ON "tenants_siteuser_groups" ("group_id");
ALTER TABLE "tenants_siteuser_user_permissions" ADD CONSTRAINT "tenants_siteuser_user_pe_siteuser_id_permission_i_7800e970_uniq" UNIQUE ("siteuser_id", "permission_id");
ALTER TABLE "tenants_siteuser_user_permissions" ADD CONSTRAINT "tenants_siteuser_use_siteuser_id_7c98aedc_fk_tenants_s" FOREIGN KEY ("siteuser_id") REFERENCES "tenants_siteuser" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "tenants_siteuser_user_permissions" ADD CONSTRAINT "tenants_siteuser_use_permission_id_67a881ec_fk_auth_perm" FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "tenants_siteuser_user_permissions_siteuser_id_7c98aedc" ON "tenants_siteuser_user_permissions" ("siteuser_id");
CREATE INDEX "tenants_siteuser_user_permissions_permission_id_67a881ec" ON "tenants_siteuser_user_permissions" ("permission_id");
COMMIT;

DROP TABLE public.users_gooseuser_user_permissions;
DROP TABLE public.users_gooseuser_groups;

ALTER TABLE public.users_gooseuser DROP COLUMN "password";
ALTER TABLE public.users_gooseuser DROP COLUMN "password";


TRUNCATE TABLE django_migrations;
EOF

# Update all usages of request.user and template -> user
# Update signup process to create gooseusers + corp apps independantly of site signup
# Run through all code working off django permissions (json api, role giving, industry, user admin)

./manage.py migrate --fake
