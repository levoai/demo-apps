#!/bin/bash
# Auto-discovered by deploy/k8s/base/build-all.sh via:
#   find ../../../services/ -name 'build-image*' -exec bash {} \;
set -e
cd "$(dirname "$0")"
docker build -t levoai/crapi-payments:latest .
