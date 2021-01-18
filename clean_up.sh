#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

./manage.py dbshell <<EOF
# TODO Drop old columns from GooseUser

DROP TABLE public.users_gooseuser_user_permissions;
DROP TABLE public.users_gooseuser_groups;

ALTER TABLE public.users_gooseuser DROP CONSTRAINT core_gooseuser_username_key;
DROP INDEX public.core_gooseuser_username_6d391dfc_like;

ALTER TABLE public.users_gooseuser DROP COLUMN "password";
ALTER TABLE public.users_gooseuser DROP COLUMN "last_login";
ALTER TABLE public.users_gooseuser DROP COLUMN "is_superuser";
ALTER TABLE public.users_gooseuser DROP COLUMN "username";
ALTER TABLE public.users_gooseuser DROP COLUMN "first_name";
ALTER TABLE public.users_gooseuser DROP COLUMN "last_name";
ALTER TABLE public.users_gooseuser DROP COLUMN "email";
ALTER TABLE public.users_gooseuser DROP COLUMN "is_staff";
ALTER TABLE public.users_gooseuser DROP COLUMN "is_active";
ALTER TABLE public.users_gooseuser DROP COLUMN "date_joined";
EOF
