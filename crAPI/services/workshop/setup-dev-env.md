# Dev Env Setup

## Install & start instructions

- Install python venv: `python3 -m venv env`
- Activate the venv: `source env/bin/activate`
- `env` is specified in `.gitignore`, so it doesn't get checked into GIT 
- Setup requirements for workshop using the requirements file via pip install in the venv
- Make sure you modify the Docker compose to expose all ports on the localhost for all the services
- run `start-dev-env.sh` to start the local python server
- Server listens on `0.0.0.0:8000`

## Auto generate OpenAPI specs
- The `./code-changes-for-oas-generation` directory has code modifications to activate DRF spectacular. Spectacular can auto generate OAS via code annotations. 
- If you need to autogenerate specs, copy over the view source files from that directory into the actual locations (overwrite them), and run the `generate-oas.sh`
- Refer to that directory for more instructions on `DRF Spectacular`

## Resolving Runtime Errors

### Resolving `AssertionError: database connection isn't set to UTC`
If the workshop API calls result in a `500 internal server` error, and the below exception in the logs, see steps below to fix.

```
File "/usr/local/lib/python3.8/site-packages/django/db/backends/postgresql/utils.py", line 6, in utc_tzinfo_factory
    raise AssertionError("database connection isn't set to UTC")
AssertionError: database connection isn't set to UTC
```
Comment out `USE_TZ = True` in the file `crAPI/services/workshop/crapi_site/settings.py`, and rebuild the image. This should fix this problem.