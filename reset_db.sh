#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

name=${1:-goosetools}

echo "WARNING: THIS SCRIPT WILL TERMINATE ALL DATABASE CONNECTIONS FORCIBLY AND DELETE YOUR LOCAL goosetools DATABASE"
read -p "Are you sure you want to continue, type Y to reset the db? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

sudo -H -u postgres psql << EOF
SELECT
 pg_terminate_backend(pg_stat_activity.pid)
FROM
pg_stat_activity
WHERE
pg_stat_activity.datname = '${name}'
 AND pid <> pg_backend_pid();

DROP DATABASE ${name};

create database ${name} with owner ${name}_user;
EOF

echo "SUCCESS"
