MalSchema - Demo API schema non-conformance
============================================

Levo makes *schema conformance testing* (aka contract tests) for REST API & GraphQL super easy!

Levo leverages the popular OSS `Schemathesis <https://schemathesis.readthedocs.io/en/stable/index.html>`_
to automatically generate (positive & negative) conformance test cases, and eliminates developer toil.

This app helps demonstrate these capabilities. Built with `connexion <https://github.com/zalando/connexion>`_,
`aiohttp <https://github.com/aio-libs/aiohttp>`_, `attrs <https://github.com/python-attrs/attrs>`_ and `asyncpg <https://github.com/MagicStack/asyncpg>`_,
it contains many intentional errors, which should be found by running Levo.

Quick Setup
-----------
Levo provides prebuilt Docker images that are hosted on Docker Hub.

To run the demo app, you need the recent version of `docker-compose <https://docs.docker.com/compose/install/>`_.

You need to download the Demo App's docker-compose config file: `docker-compose.yml <https://raw.githubusercontent.com/levoai/demo-apps/main/MalSchema/docker-compose.yml>`_.

Start the application via `docker-compose` in the directory where you downloaded the config file:

.. code::

    docker-compose up

It will spin up a web server available at ``http://0.0.0.0:9000``. You can take a look at API documentation at ``http://0.0.0.0:9000/api/ui/``.
Note, the app will run in the current terminal.

You can download the demo app's OAS file at http://0.0.0.0:9000/api/openapi.json

If not already installed, **Install Levo's CLI** by following the onboarding instructions in the Levo SaaS portal.


Command-line
------------

Below are examples of running schema conformance tests using Levo CLI. Instructions assume a Mac OSX or Linux environment.
Adapt these instructions if running on Windows Powershell.

.. code:: bash

    export SCHEMA_URL="http://host.docker.internal:9000/api/openapi.json"
    export TARGET_URL="http://host.docker.internal:9000/"

    # Login into the Levo SaaS portal
    levo login

    # Runs all schema conformance tests for all API operations
    levo test-conformance --schema $SCHEMA_URL --target-url $TARGET_URL

    # Provide custom headers (e.g. Authorization if required)
    levo test-conformance --schema $SCHEMA_URL --target-url $TARGET_URL -H "Authorization: Bearer <token>"

Now you can view the test results in the https://levo.ai SaaS console.

Shutdown
------------
Use <CTRL-C> to abort, and then shutdown the application via `docker-compose`:

.. code::

    docker-compose down

Setup Using Source
------------------
Setup from source requires you to clone the `MalSchema` Git repo.

To run the demo app, you need the recent version of `docker-compose <https://docs.docker.com/compose/install/>`_.

Start the application via `docker-compose` and specifying an alternate compose config:

.. code::

    docker-compose -f ./docker-compose-local-build.yml up

Now follow rest of the 'Quick Setup' instructions after the `docker-compose` step.

Troubleshooting FAQ
-------------------
1. If `docker-compose up` results in apt-get errors as shown below, use the instructions below to clean the image store, and try again.

.. code::

    => ERROR [3/6] RUN apt-get update && apt-get install -y libpq-dev gcc && pip install -r requirements.txt && apt remove -y libpq-dev gcc && apt -y autoremove && rm -rf /var/lib/apt/li 0.8s
    ------
     > [3/6] RUN apt-get update && apt-get install -y libpq-dev gcc && pip install -r requirements.txt && apt remove -y libpq-dev gcc && apt -y autoremove && rm -rf /var/lib/apt/lists/*:
    #8 0.481 Get:1 http://security.debian.org/debian-security buster/updates InRelease [65.4 kB]
    #8 0.558 Get:2 http://deb.debian.org/debian buster InRelease [121 kB]
    #8 0.586 Err:1 http://security.debian.org/debian-security buster/updates InRelease
    #8 0.586   At least one invalid signature was encountered.
    #8 0.635 Get:3 http://deb.debian.org/debian buster-updates InRelease [51.9 kB]
    #8 0.667 Err:2 http://deb.debian.org/debian buster InRelease
    #8 0.667   At least one invalid signature was encountered.
    #8 0.734 Err:3 http://deb.debian.org/debian buster-updates InRelease
    #8 0.734   At least one invalid signature was encountered.
    #8 0.741 Reading package lists...
    #8 0.750 W: GPG error: http://security.debian.org/debian-security buster/updates InRelease: At least one invalid signature was encountered.
    #8 0.750 E: The repository 'http://security.debian.org/debian-security buster/updates InRelease' is not signed.
    #8 0.750 W: GPG error: http://deb.debian.org/debian buster InRelease: At least one invalid signature was encountered.
    #8 0.750 E: The repository 'http://deb.debian.org/debian buster InRelease' is not signed.
    #8 0.750 W: GPG error: http://deb.debian.org/debian buster-updates InRelease: At least one invalid signature was encountered.
    #8 0.750 E: The repository 'http://deb.debian.org/debian buster-updates InRelease' is not signed.


       `docker image prune` and then `docker container prune` will resolve the above issues

2. Levo CLI fails when specifying '127.0.0.1' or 'localhost' in the --target-url.

 Levo CLI runs in a Docker container. Use 'host.docker.internal" instead, and this will correctly resolve to the underlying Docker host
