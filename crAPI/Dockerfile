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
FROM golang:1.18.0-buster AS community-builder
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

# Build image for Mailhog
FROM golang:1.18.0-buster AS mailhog-builder
RUN apt-get update && apt-get install -y \
    ca-certificates \
    git
WORKDIR /app
RUN mkdir -p /app/gocode \
  && export GOPATH=/app/gocode \
  && go install github.com/mailhog/MailHog@v1.0.1 \
  && mv /app/gocode/bin/MailHog /usr/local/bin \
  && rm -rf /app/gocode

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
    MAILHOG_UI=localhost:8025

# Add openresty for web
ARG RESTY_DEB_FLAVOR=""
# ARG RESTY_DEB_VERSION="=1.19.9.1-1~buster1"
ARG RESTY_APT_REPO="https://openresty.org/package/debian"
ARG RESTY_APT_DIST="bullseye"
ARG RESTY_APT_PGP="https://openresty.org/package/pubkey.gpg"

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
    && curl -fsSL ${RESTY_APT_PGP} | gpg --dearmor -o /usr/share/keyrings/openresty.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/openresty.gpg] ${RESTY_APT_REPO} ${RESTY_APT_DIST} openresty" > /etc/apt/sources.list.d/openresty.list \
    && DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        openresty \
    && DEBIAN_FRONTEND=noninteractive apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/openresty \
    && ln -sf /dev/stdout /usr/local/openresty${RESTY_DEB_FLAVOR}/nginx/logs/access.log \
    && ln -sf /dev/stderr /usr/local/openresty${RESTY_DEB_FLAVOR}/nginx/logs/error.log

# Add additional binaries into PATH for convenience
ENV PATH="$PATH:/usr/local/openresty${RESTY_DEB_FLAVOR}/luajit/bin:/usr/local/openresty${RESTY_DEB_FLAVOR}/nginx/sbin:/usr/local/openresty${RESTY_DEB_FLAVOR}/bin"

# Add MongoDB
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | apt-key add -
RUN echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.2 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-4.2.list
RUN apt-get update && apt-get install -y mongodb-org
RUN sed -i "s,\\(^[[:blank:]]*bindIp:\\) .*,\\1 0.0.0.0," /etc/mongod.conf

# Python for Workshop service
ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y libpq-dev \
    python3-dev python3-pip python3-setuptools libffi-dev gcc && \
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
