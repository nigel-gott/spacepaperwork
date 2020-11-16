#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

docker-compose -f local.yml exec django python manage.py "$@"
