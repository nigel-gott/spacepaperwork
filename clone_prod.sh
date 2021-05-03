#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

name=${1:-}
# ssh to server and make server dump
if [ "$name" = "download" ]; then
    ssh thejanitor@goosetools.com "pg_dump -U goosetools_user -Fc --dbname=postgresql://goosetools_user:${DBPASS}@localhost/goosetools > /home/thejanitor/dump.dump"
    scp thejanitor@goosetools.com:~/dump.dump /home/nigel/
fi
sudo cp /home/nigel/dump.dump /home/postgres/dump.dump
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
