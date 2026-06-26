# Build image for web
FROM node:16 as web-build
WORKDIR /app
COPY ./services/web/package.json /app/package.json
COPY ./services/web/package-lock.json /app/package-lock.json
RUN npm install --silent
COPY ./services/web/src /app/src
COPY ./services/web/public /app/public
RUN cp /app/src/config.js.template /app/src/config.js
RUN NODE_OPTIONS=--max_old_space_size=2048 npm run build
RUN ls /app/build

# Build image for identity service
FROM maven:3.8.2-jdk-11 AS identity-build
WORKDIR /app
COPY ./services/identity/pom.xml /app/pom.xml
RUN mvn -f /app/pom.xml dependency:go-offline -B 
COPY ./services/identity/src /app/src
RUN mvn -f /app/pom.xml clean package -DskipTests

# Build image for Community service
FROM golang:1.24rc1-bullseye AS community-builder
ENV GO111MODULE=on \
    CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64
WORKDIR /build
COPY ./services/community/go.mod .
COPY ./services/community/go.sum .
RUN go mod download
COPY ./services/community/main.go ./main.go
COPY ./services/community/api ./api
RUN go mod vendor
RUN ls -al
RUN go build -o main .
WORKDIR /dist
RUN cp /build/main .

# Build image for Mailhog.
# MailHog@v1.0.1 has no pinned deps, so `go install` resolves the latest
# golang.org/x/crypto (v0.52.0+), which requires Go >= 1.25. Go 1.25 no longer
# ships a -bullseye image, so build on bookworm with CGO disabled to produce a
# fully static binary that still runs on the bullseye-based final image.
FROM golang:1.25-bookworm AS mailhog-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ARG TARGETARCH
RUN mkdir -p /app/gocode
ENV GOPATH=/app/gocode
ENV GOBIN=/usr/local/bin
RUN CGO_ENABLED=0 GOARCH=${TARGETARCH:-amd64} GOOS=linux go install github.com/mailhog/MailHog@v1.0.1

# OpenResty base image to copy binaries
FROM openresty/openresty:1.25.3.1-0-bullseye-fat AS openresty-builder

# Final Docker image. Basing it off of Postgres so that we don't have to
# go through the pain of adding Postgres ourselves.
FROM postgres:13-bullseye
WORKDIR /app
ENV DB_NAME=crapi \
    DB_USER=admin \
    DB_PASSWORD=crapisecretpassword \
    DB_HOST=localhost \
    DB_PORT=5432 \
    MONGO_DB_HOST=localhost \
    MONGO_DB_PORT=27017 \
    MONGO_DB_USER=admin \
    MONGO_DB_PASSWORD=crapisecretpassword \
    MONGO_DB_NAME=crapi \
    JWT_SECRET=crapi \
    SECRET_KEY=crapi \
    POSTGRES_USER=admin \
    POSTGRES_PASSWORD=crapisecretpassword \
    POSTGRES_DB=crapi
ENV GO_SERVICE=localhost:8087 \
    JAVA_SERVICE=localhost:8080 \
    PYTHON_SERVICE=localhost:8000 \
    PAYMENTS_SERVICE=localhost:8001 \
    MAILHOG_UI=localhost:8025

# Install runtime dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        gnupg2 \
        lsb-release \
        software-properties-common \
        wget \
        gettext \
        gettext-base \
        openjdk-11-jre \
        netcat \
        vim \
        dumb-init \
        procps \
    && DEBIAN_FRONTEND=noninteractive apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=openresty-builder /usr/local/openresty /usr/local/openresty

RUN mkdir -p /var/run/openresty \
    && ln -sf /dev/stdout /usr/local/openresty/nginx/logs/access.log \
    && ln -sf /dev/stderr /usr/local/openresty/nginx/logs/error.log

# Add additional binaries into PATH for convenience
ENV PATH="$PATH:/usr/local/openresty${RESTY_DEB_FLAVOR}/luajit/bin:/usr/local/openresty${RESTY_DEB_FLAVOR}/nginx/sbin:/usr/local/openresty${RESTY_DEB_FLAVOR}/bin"

# Add MongoDB 7.0 from the official MongoDB Debian (bullseye) apt repo.
#
# NOTE: do NOT copy the mongod binary out of the mongo:7.0 Docker image. That
# image is built on Ubuntu 22.04 (glibc 2.35, OpenSSL 3), while this image is
# based on postgres:13-bullseye (Debian 11, glibc 2.31, OpenSSL 1.1). A binary
# copied across distros fails to start at runtime with
#   "libc.so.6: version `GLIBC_2.34' not found"
# plus missing libcurl.so.4 / libssl.so.3, so mongod never comes up and every
# Mongo client (community service, MailHog) gets "connection refused".
# Installing the bullseye-native package via apt pulls in the matching libs.
# amd64 only: MongoDB does not publish arm64 packages for the Debian repo.
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc \
        | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor \
    && echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg arch=amd64 ] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/7.0 main" \
        > /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    # mongodb-org-server's postinst invokes systemctl, which is absent in a
    # container; shim it with /bin/true so dpkg configuration succeeds.
    && ln -sf /bin/true /usr/local/bin/systemctl \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        mongodb-org-server mongodb-mongosh \
    && rm -f /usr/local/bin/systemctl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data/db /var/log/mongodb \
    && printf 'net:\n  bindIp: 0.0.0.0\n  port: 27017\nstorage:\n  dbPath: /data/db\n' \
        > /etc/mongod.conf

# Python for Workshop service
ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y libpq-dev \
    python3-dev python3-pip python3-setuptools python3-venv libffi-dev gcc && \
    # There is an issue with psycopg2 version 2.9, hence pin it to lower version. See https://stackoverflow.com/a/68025007/467969
    pip3 install psycopg2==2.8.5

# Copy Mailhog from builder image
ENV MH_MONGO_URI=admin:crapisecretpassword@localhost:27017 \
    MH_STORAGE=mongodb
WORKDIR /app/mailhog
COPY --from=mailhog-builder /usr/local/bin/ /usr/local/bin

# Copy identity service artifacts from builder image
ENV BLOCK_SHELL_INJECTION=false \
    MAILHOG_HOST=localhost \
    MAILHOG_PORT=1025 \
    MAILHOG_DOMAIN=example.com \
    MAILHOG_UI=localhost:8025 \
    SMTP_HOST=smtp.example.com \
    SMTP_PORT=587 \
    SMTP_EMAIL=user@example.com \
    SMTP_PASS=xxxxxxxxxxxxxx \
    SMTP_FROM=no-reply@example.com \
    SMTP_AUTH=true \
    SMTP_STARTTLS=true \
    RESTRICT_CMDI=true
WORKDIR /app/identity
COPY --from=identity-build /app/target/user-microservices-1.0-SNAPSHOT.jar /app/identity/user-microservices-1.0-SNAPSHOT.jar

# Copy community service artifacts from builder image
RUN mkdir /app/community
COPY --from=community-builder /dist/main /app/community/main
RUN ls -al /app/community

# Add Workshop service directly, no builder image.
WORKDIR /app/workshop
COPY ./services/workshop/ /app/workshop
RUN pip3 install -r requirements.txt

# Add Payments service in an isolated virtualenv.
# Payments runs Django 3.2 while Workshop pins Django ~2.2; installing both into
# the global site-packages would clobber one of them, so payments gets its own venv.
ENV PAYMENTS_VENV=/opt/payments-venv \
    DJANGO_KEY=payments-insecure-dev-key-00001 \
    SERVER_PORT=8001 \
    PAYMENTS_ALLOWED_MERCHANT_IDS=merch_7f2a91,merch_4b8c12,merch_0d3e55,merch_load01
WORKDIR /app/payments
COPY ./services/payments/ /app/payments
RUN python3 -m venv "$PAYMENTS_VENV" \
    && "$PAYMENTS_VENV"/bin/pip install --no-cache-dir --upgrade pip \
    && "$PAYMENTS_VENV"/bin/pip install --no-cache-dir -r requirements.txt

# Copy Nginx related config form web
COPY --from=web-build /app/build /usr/share/nginx/html
COPY ./services/web/nginx-wrapper.sh /etc/nginx/nginx-wrapper.sh
COPY ./services/web/nginx-selfsigned.crt /etc/nginx/selfsigned.crt
COPY ./services/web/nginx-selfsigned.key /etc/nginx/selfsigned.key
COPY ./services/web/nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY openresty_nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
# RUN echo "daemon off;" >> /usr/local/openresty/nginx/conf/nginx.conf
EXPOSE 80
EXPOSE 443

WORKDIR /app
COPY start_all_services.sh /app

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["bash", "-c", "/app/start_all_services.sh"]

STOPSIGNAL SIGINT
