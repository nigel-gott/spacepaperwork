#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

docker-compose -f test.yml run --rm  --entrypoint ptw django
