#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

gunicorn goosetools.wsgi
