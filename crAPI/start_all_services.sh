#!/usr/bin/env bash

# Bounded waiters. A dependency that never comes up must NOT hang the container
# forever: that is exactly the failure that kept nginx from ever binding (a
# backend with a port collision left the old unbounded `while ! curl` loop
# spinning at ~4% CPU indefinitely). On timeout these helpers log a WARN and
# RETURN non-zero; the CALLER decides what to do with that:
#   * Soft dependencies (MongoDB, community, MailHog) -> caller continues, so
#     nginx still binds and the backend degrades to a 502 instead of blocking
#     the whole image.
#   * Hard dependencies -> caller exits non-zero so the real error surfaces.
#     These still fail the container on purpose: a missing payments venv, failed
#     payments/workshop migrations, or identity never becoming healthy.
# Tune the budget with DEP_WAIT_TIMEOUT (seconds).
DEP_WAIT_TIMEOUT="${DEP_WAIT_TIMEOUT:-180}"

waitport() {
  local port="$1" timeout="${2:-$DEP_WAIT_TIMEOUT}" start=$SECONDS
  # `nc -w 2` bounds each individual connect attempt, so a hung TCP connect
  # (e.g. dropped SYNs) cannot blow past the overall timeout budget.
  while ! nc -z -w 2 localhost "$port" ; do
    if [ $((SECONDS - start)) -ge "$timeout" ]; then
      echo "WARN: timed out after ${timeout}s waiting for port ${port}" >&2
      return 1
    fi
    sleep 0.3
  done
}

wait_endpoint() {
  local url="$1" timeout="${2:-$DEP_WAIT_TIMEOUT}" start=$SECONDS
  # --connect-timeout/--max-time bound each probe so a single hung connect or
  # response cannot exceed the overall timeout budget tracked by the outer loop.
  while ! curl -s -o /dev/null --connect-timeout 2 --max-time 5 "$url" ; do
    if [ $((SECONDS - start)) -ge "$timeout" ]; then
      echo "WARN: timed out after ${timeout}s waiting for ${url}" >&2
      return 1
    fi
    sleep 3
  done
}

print_banner() {
  echo ""
  echo "********************"
  echo "$1......."
  echo ""
}

user=`whoami`
echo "Running as $user"

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Startup is ordered to overlap the slow JVM warmup with everything that does
# not depend on it, instead of starting each service strictly after the last.
#
# Dependency facts that drive this order:
#   * Postgres & MongoDB are independent of each other      -> boot in parallel.
#   * Nothing depends on the identity (JVM) service at boot -> start it FIRST
#     and let it warm up in the background; join on it later.
#   * community (Go) and MailHog need only MongoDB           -> overlap warmup.
#   * payments (Django) owns its own tables, no identity dep -> overlap warmup.
#   * workshop (Django) maps identity-owned tables (user app is managed=False,
#     hence `migrate user --fake`) so it MUST run after identity is healthy.
#   * workshop & payments share the `crapi` Postgres DB and both install
#     django.contrib.auth/contenttypes, so their migrations touch the same
#     framework tables -> they must NOT migrate concurrently. payments migrates
#     during the JVM warmup; workshop migrates after the identity join, so the
#     two migrate steps are naturally serialized.
# Net effect: total backend startup ~= the single slowest path (Postgres -> JVM
# -> workshop) rather than the sum of every service.
# ---------------------------------------------------------------------------

# Phase 1: databases (Postgres + MongoDB boot concurrently).
print_banner "Starting Postgres + MongoDB"
/usr/local/bin/docker-entrypoint.sh postgres &
# `mongod --fork` blocks until Mongo accepts connections; Postgres is warming up
# in the background meanwhile, so the two DB startups overlap.
/usr/bin/mongod -f /etc/mongod.conf --auth --fork --quiet --logpath /var/log/mongodb.log --logappend
waitport 5432
# Only initialize Mongo users if Mongo actually came up. If waitport timed out
# (soft dependency), skip init entirely instead of running mongosh against a dead
# server and emitting a wall of connection errors.
if waitport 27017; then
  # Initialize the MongoDB with init users (needs Mongo up; must precede any
  # authed Mongo client). MongoDB 6.0+ ships only "mongosh"; the legacy "mongo"
  # shell was removed. Idempotent: createUser throws if the admin user already
  # exists (e.g. on restart with a persisted data volume) or if the localhost
  # exception is gone, so we catch and skip rather than fail.
  mongosh --quiet --authenticationDatabase admin <<'EOF'
use admin;
try {
  db.createUser({user: 'admin', pwd: 'crapisecretpassword', roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]});
  print('mongo: admin user created');
} catch (e) {
  print('mongo: skipping createUser (' + e.codeName + '): ' + e.message);
}
EOF
else
  echo "WARN: MongoDB not reachable; skipping user init (community service and MailHog Mongo storage will be degraded)" >&2
fi

# Phase 2: launch the long-pole JVM FIRST so it warms up while everything else
# boots. Nothing depends on identity at startup, so do NOT wait here.
print_banner "Starting Identity Service"
# JVM heap sizing. By default the heap scales with the container's memory limit:
# JDK 11 is cgroup-aware (-XX:+UseContainerSupport is on by default), so
# -XX:MaxRAMPercentage sizes -Xmx as a fraction of the cgroup limit. Give the
# container more memory (--memory / mem_limit) and the heap grows with it.
#
# This is an all-in-one container: the JVM shares RAM with Postgres, MongoDB,
# two Django apps, the Go service and Nginx. So it claims only a FRACTION of the
# limit (default 25%, ~512m at a 2g limit) to avoid starving the co-tenants.
# Tune with IDENTITY_SERVICE_RAM_PERCENT.
#
# Set IDENTITY_SERVICE_HEAP to a fixed size (e.g. 1g) to override the percentage
# and pin -Xms/-Xmx instead.
if [ -n "${IDENTITY_SERVICE_HEAP:-}" ]; then
  IDENTITY_HEAP_OPTS="-Xms${IDENTITY_SERVICE_HEAP} -Xmx${IDENTITY_SERVICE_HEAP}"
else
  IDENTITY_SERVICE_RAM_PERCENT="${IDENTITY_SERVICE_RAM_PERCENT:-25}"
  IDENTITY_HEAP_OPTS="-XX:MaxRAMPercentage=${IDENTITY_SERVICE_RAM_PERCENT}"
fi
java ${IDENTITY_HEAP_OPTS} -jar /app/identity/user-microservices-1.0-SNAPSHOT.jar &

# Phase 3: services that need only MongoDB — start in the background, no wait.
# MailHog is only needed at email-send time, so it never gates startup.
print_banner "Starting MailHog + Community Service"
/usr/local/bin/MailHog &
/app/community/main &

# Phase 4: payments (Django) — independent of identity, so migrate it now during
# the JVM warmup. Migrate runs in the FOREGROUND so it completes before workshop
# migrates later (the two share the crapi DB and must not migrate concurrently);
# only the dev server is backgrounded.
print_banner "Migrating + starting Payments Service"
PAYMENTS_VENV="${PAYMENTS_VENV:-/opt/payments-venv}"
PAYMENTS_PORT="${PAYMENTS_PORT:-8001}"
# Fail fast: a missing venv or a failed migration must stop the container so the
# error surfaces, instead of backgrounding runserver and hanging in wait_endpoint.
if [ ! -x "${PAYMENTS_VENV}/bin/python" ]; then
  echo "ERROR: payments virtualenv interpreter not found at ${PAYMENTS_VENV}/bin/python" >&2
  exit 1
fi
if ! ( cd "$APP_DIR/payments" && "${PAYMENTS_VENV}/bin/python" manage.py migrate --noinput ); then
  echo "ERROR: payments migrations failed" >&2
  exit 1
fi
( cd "$APP_DIR/payments" && "${PAYMENTS_VENV}/bin/python" manage.py runserver 0.0.0.0:"${PAYMENTS_PORT}" ) &

# Phase 5: JOIN on the long pole. workshop's migrations map identity-owned tables
# (user_login, vehicle_*) and create foreign keys to them, so identity MUST be
# healthy before workshop migrates -- this is a HARD dependency, not a soft one.
# Give it a generous budget (IDENTITY_WAIT_TIMEOUT, default 600s) so a slow but
# otherwise healthy JVM (e.g. an emulated or low-resource host) still passes, and
# fail fast with a clear message if it never comes up -- otherwise the workshop
# migrations below would fail later with a confusing missing-table error.
print_banner "Waiting for Identity Service to become healthy"
if ! wait_endpoint "http://127.0.0.1:8080/identity/health_check" "${IDENTITY_WAIT_TIMEOUT:-600}"; then
  echo "ERROR: identity service did not become healthy within ${IDENTITY_WAIT_TIMEOUT:-600}s; workshop migrations depend on it, aborting" >&2
  exit 1
fi

# Phase 6: workshop (Django) — now safe: identity has created the user/vehicle
# tables and payments has finished migrating the shared crapi DB. Migrate in the
# foreground, then background the dev server. Mirrors services/workshop/runner.sh.
print_banner "Migrating + starting Workshop Service"
if ! ( cd "$APP_DIR/workshop" \
        && python3 manage.py migrate user --fake \
        && python3 manage.py migrate crapi \
        && python3 manage.py migrate db ); then
  echo "ERROR: workshop migrations failed" >&2
  exit 1
fi
( cd "$APP_DIR/workshop" && python3 manage.py runserver 0.0.0.0:8000 ) &

# Phase 7: JOIN on the remaining background services. They have all been booting
# concurrently, so this waits ~ only for whichever is slowest.
print_banner "Waiting for remaining services to become healthy"
wait_endpoint "http://127.0.0.1:8087/community/home"
wait_endpoint "http://127.0.0.1:${PAYMENTS_PORT}/payments/api/payments/health"
wait_endpoint "http://127.0.0.1:8000/workshop/health_check/"

cd "$APP_DIR"

# Start Nginx to start web at the end
# Change the /var/run/openresty directory to be owned by the nobody user
mkdir -p /var/run/openresty/
chown nobody:nobody /var/run/openresty
print_banner "Starting Nginx"
/etc/nginx/nginx-wrapper.sh
