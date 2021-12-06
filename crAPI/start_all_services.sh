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

user=`whoami`
echo "Running as $user"

# Start postgres
print_banner "Starting Postgres"
/usr/local/bin/docker-entrypoint.sh postgres &

# Wait for Postgres to come up fully
waitport 5432

# Start MongoDB
print_banner "Starting MongoDB"
/usr/bin/mongod -f /etc/mongod.conf --auth --fork --quiet --logpath /var/log/mongodb.log --logappend

# Wait until mongo logs that it's ready (or timeout after 10s)
COUNTER=0
grep -q 'waiting for connections on port' /var/log/mongodb.log
while [[ $? -ne 0 && $COUNTER -lt 10 ]] ; do
    sleep 1
    let COUNTER+=1
    echo "Waiting for mongo to initialize... ($COUNTER seconds so far)"
    grep -q 'waiting for connections on port' /var/log/mongodb.log
done

# Initialize the MongoDB with init users.
mongo --authenticationDatabase admin <<EOF
use admin;
db.createUser({user: 'admin', pwd: 'crapisecretpassword', roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]})
EOF

# Start mailhog after MongoDB
print_banner "Starting MailHog"
/usr/local/bin/MailHog &

# Wait for MailHog to come up
waitport 8025
# while ! echo exit | nc localhost 8025; do sleep 1; done

# Start identity service
print_banner "Starting Identity Service"
java -jar /app/identity/user-microservices-1.0-SNAPSHOT.jar &

# Wait for identity service to fully come up
wait_endpoint 0.0.0.0:8080/identity/health_check

# Start community service
print_banner "Starting Community Service"
/app/community/main &

# Wait for community service to fully come up
wait_endpoint 0.0.0.0:8087/community/home

# Start workshop service
print_banner "Starting Workshop Service"
cd "$(dirname "${BASH_SOURCE[0]}")/workshop"
sh ./runner.sh &

# Wait for workshop service to fully come up
wait_endpoint 0.0.0.0:8000/workshop/health_check/

cd "$(dirname "${BASH_SOURCE[0]}")"

# Start Nginx to start web at the end
# Change the /var/run/openresty directory to be owned by the nobody user
chown nobody:nobody /var/run/openresty
print_banner "Starting Nginx"
/etc/nginx/nginx-wrapper.sh