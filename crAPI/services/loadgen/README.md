# Loadgen Instructions

In order to use this loadgen, go to https://docs.levo.ai/beta/api-observability/quickstart and follow all the steps to get the API observability testing up and running.

Now, save the locustfile (loadgen) on your computer: https://github.com/levoai/demo-apps/tree/main/crAPI/services/loadgen

Execute this command in terminal/console:

locust -f <file_directory>

where <file_directory> is replaced by the path to the loadgen on your computer.

Go to http://0.0.0.0:8089/ on your browser to access Locust's UI. If the locustfile is running, Locust will ask you for the number of users, spawn rate, and the host. By default, the host is set to localhost:8888. If crAPI is running somewhere else, point Locust to crAPI.

Wait for about 30 seconds and you should begin to see the API specs being discovered.

You may set the number of users and spawn rate to whatever values you wish but be aware that too many requests may raise a 429 error.
