# Dev Env Setup

## Install & start instuctions

- Install python venv 
- Activate the venv
- Setup requirements for workshop using the requirements file via pip install in the venv
- Make sure you modify the Docker compose to expose all ports on the localhost for all the services
- run `start-dev-env.sh` to start the local python server
- Server listens on `0.0.0.0:8000`

## Auto generate OpenAPI specs
- The `./code-changes-for-oas-generation` directory has code modifications to activate DRF spectacular. Spectacular can auto generate OAS via code annotations. 
- If you need to autogenerate specs, copy over the view source files from that directory into the actual locations (overwrite them), and run the `generate-oas.sh`
- Refer to that directory for more instructions on `DRF Spectacular`