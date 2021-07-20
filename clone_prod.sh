#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

mode=${1:-}
user=${2:-}
url=${3:-}
server_dest=${4:-/home/${DBUSER}}
local_dest=${5:-$HOME}
# ssh to server and make server dump
if [ "$mode" = "download" ]; then
    ssh "${user}"@"${url}" "pg_dump -U ${DBUSER} -Fc --dbname=${DBCONN} > ${server_dest}/dump.dump"
    scp "${user}"@"${url}":"${server_dest}"/dump.dump "${local_dest}"
fi
sudo cp "${local_dest}"/dump.dump /home/postgres/dump.dump
sudo chown -R postgres:postgres /home/postgres/
sudo -H -u postgres psql << EOF
SELECT
 pg_terminate_backend(pg_stat_activity.pid)
FROM
pg_stat_activity
WHERE
pg_stat_activity.datname = 'goosetools'
 AND pid <> pg_backend_pid();

DROP DATABASE goosetools;

create database goosetools with owner goosetools_user;
EOF

sudo -H -u postgres bash -c 'pg_restore -d goosetools /home/postgres/dump.dump'

sudo -H -u postgres psql -d goosetools << EOF
  UPDATE public.socialaccount_socialapp SET client_id='748478733077315645', secret='fake';
  UPDATE public.tenants_domain SET domain='localhost';
EOF
echo "SUCCESS"

./manage.py migrate
