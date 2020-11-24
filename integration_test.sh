#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

trap "docker-compose -f test.yml logs django && docker-compose -f test.yml down && docker-compose -f test.yml rm" EXIT

docker-compose -f test.yml up --build -d
docker-compose -f test.yml exec django pytest goosetools/tests/integration --runslow
docker-compose -f test.yml down
docker-compose -f test.yml rm
