#!/usr/bin/env bash

waitport() {
  while ! nc -z localhost $1 ; do sleep 0.3 ; done
}

wait_endpoint() {
  while ! echo exit | curl -s $1; do sleep 3; done
}

print_banner() {
  echo ""
  echo "********************"
  echo "$1......."
  echo ""
}

# Start postgres
print_banner "Starting Postgres"
/usr/local/bin/docker-entrypoint.sh postgres &

# Wait for Postgres to come up fully
waitport 5432

python3 /example/main.py
