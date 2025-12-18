# Dev Env Setup

## Install & start instuctions

- Ensure you have Java, JDK, and Maven installed, are in your path 
- Make sure you modify the Docker compose to expose all ports on the localhost for all the services
- Start all services using Docker compose
- Now kill the Identity Service container
- Now, run `start-dev-env.sh` to start the local identity server
- Server listens on `0.0.0.0:8080`

## Auto generated OpenAPI specs
- OAS in JSON format is available at: `http://{identity-service-hostname}:8080/v3/api-docs`
- OAS Swagger UI is available at: `http://{identity-service-hostname}:8080/swagger-ui.html`

## Checking in OpenAPI specs into GIT
- If you modify the APIs, please generate the specs and check them into `crAPI/api-specs/identity/openapi.json`
- Please diff the specs, and remove extraneous info such as `servers` section
- Please ensure that `security` section is appropriately filled, as security is not auto generated