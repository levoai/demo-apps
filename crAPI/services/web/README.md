# Dev Environment Setup

1. Modify `crAPI/deploy/docker/docker-compose.yml` to expose ports locally for Identity, Workshop, and Community
2. Start all services using Docker Compose
3. ```docker rm -f crapi-web```
4. ```export NODE_OPTIONS=--openssl-legacy-provider```
5. ```yarn```
6. ```yarn start```
7. Goto `http://localhost:3000` to access the web console

