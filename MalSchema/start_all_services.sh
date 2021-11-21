#!/usr/bin/env bash

wait_port() {
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
wait_port 5432

psql test -h localhost -d schemathesis-example -f database/schema.sql || true

python3 /example/main.py
