crAPI
=====

**c**ompletely **r**idiculous **API** (crAPI) will help you to understand the
ten most critical API security risks. crAPI is vulnerable by design, but you'll
be able to safely run it to educate/train yourself.

crAPI is modern, built on top of a microservices architecture. When time has
come to buy your first car, sign up for an account and start your journey. To
know more about crAPI, please check [crAPI's overview][overview].

## QuickStart Guide

### Docker with single container

You'll need to have Docker installed and running on your host system.
After having crAPI running, you may want to remove unnecessary docker images
left behind.

1. Start crAPI in single container
    ```
    docker run -p 80:80 levoai/crapi-all
    ```
2. Visit `http://localhost`

If you want to build the crapi-all image locally with some modifications,
run the following command in the root directory.

```
docker build -t levoai/crapi-all crAPI
```

### Docker Compose

1. Clone crAPI repository
    ```
    $ git clone [REPOSITORY-URL]
    ```
2. Start crAPI, which fetches the images from Dockerhub
    ```
    $ docker-compose -f crAPI/deploy/docker/docker-compose.yml --compatibility up -d
    ```
3. Visit `http://localhost:8888`

If you want to bulid the images lcoally:

4. Build all docker images
    ```
    $ ./crAPI/build-all.sh
    ```

**Note**: All emails are sent to mailhog service by default and can be checked on
`http://localhost:8025`
You can change the smtp configuration if required however all emails with domain **example.com** will still go to mailhog.

### Kubernetes

If you would like to deploy on kubernetes we have sample k8s configs already
created. Check [the setup instructions][setup-k8s] for more details.


### Vagrant

This option allows you to run crAPI within a virtual machine, thus isolated from
your system. You'll need to have [Vagrant] and, for example [VirtualBox]
installed.

1. Clone crAPI repository
    ```
    $ git clone [REPOSITORY-URL]
    ```
2. Start crAPI Virtual Machine
    ```
    $ cd crAPI/deploy/vagrant && vagrant up
    ```
3. Visit `http://192.168.33.20`


**Note**: All emails are sent to mailhog service and can be checked on
`http://192.168.33.20:8025`

Once you're done playing with crAPI, you can remove it completely from your
system running the following command from the repository root directory

```
$ cd crAPI/deploy/vagrant && vagrant destroy
```

---

Copyright (c) 2020 "Traceable AI". All rights reserved.

[overview]: docs/overview.md
[Vagrant]: https://www.vagrantup.com/downloads
[VirtualBox]: https://www.virtualbox.org/wiki/Downloads
