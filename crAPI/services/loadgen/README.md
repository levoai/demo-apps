# Load Generator for crAPI

This ['Locust'](https://locust.io/) based load generator will exercise various APIs of crAPI.

## Prerequisites
A working installation of ['Locust'](https://locust.io/).

## Instructions

1. Download the locust-file (loadgen) on to your computer: https://github.com/levoai/demo-apps/tree/main/crAPI/services/loadgen

2. Execute this command in terminal/console:
```bash
locust -f <path to the loadgen on your computer>
```

3. Go to http://0.0.0.0:8089/ on your browser to access Locust's UI. If the locustfile is running, Locust will ask you for the number of users, spawn rate, and the host. By default, the host is set to localhost:8888. If crAPI is running somewhere else, point Locust to crAPI.

> You may set the number of users and spawn rate to whatever values you wish, but be aware that too many requests may raise a 429 error.
