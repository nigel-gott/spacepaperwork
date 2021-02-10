#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

name=${1:-}
# ssh to server and make server dump
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

echo "SUCCESS"
