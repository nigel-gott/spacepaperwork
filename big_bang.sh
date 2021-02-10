#!/bin/bash
set -euo pipefail
IFS=$'\n\t'


./manage.py dbshell <<EOF
BEGIN;
TRUNCATE TABLE public.django_migrations;
TRUNCATE TABLE gooseflock.django_migrations;
EOF


./manage.py migrate --fake
