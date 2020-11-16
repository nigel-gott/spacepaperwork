#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

docker build --tag goosetools_dev -f ./compose/local/dev/Dockerfile .
docker run --rm -v $(pwd):/app  goosetools_dev pre-commit run --all-files
