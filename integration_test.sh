#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

trap "docker-compose -f test.yml logs && docker-compose -f test.yml down && docker-compose -f test.yml rm" EXIT

docker-compose -f test.yml up --build -d
docker-compose -f test.yml exec django pytest tests/integration 
docker-compose -f test.yml down
docker-compose -f test.yml rm