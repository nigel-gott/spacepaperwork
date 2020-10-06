#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

gunicorn -c /opt/goosetools/gunicorn_config.py goosetools.wsgi
