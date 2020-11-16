#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

./tests.sh
./pre_commit_checks.sh
./integration_test.sh
