

crAPI Quick Start Guide
=====

- [Docker Container](#docker-container)
- [Docker Compose](#docker-compose)
- [Vagrant](#vagrant)
- [Kubernetes](#kubernetes)

---

### Docker Container

This is an ephemeral setup, designed for quick testing of crAPI without checking out the code. 
You'll need to have Docker installed and running on your host system.

1. Start crAPI
    ```
    $ docker run -p 8888:80 levoai/crapi-all
    ```
2. Visit `http://localhost:8888`

**Note**: All emails are sent to mailhog service by default and can be checked on `http://localhost:8888/email`. 


### Docker Compose

In this mode, all the crAPI services will be running as separate containers, orchestrated with docker compose.
You'll need to have Docker installed and running on your host system.

1. Clone crAPI repository
    ```
    $ git clone [REPOSITORY-URL]
    ```
2. Start crAPI
    ```
    $ docker-compose -f deploy/docker/docker-compose.yml up -d
    ```
3. Visit `http://localhost:8888`

**Note**: All emails are sent to mailhog service by default and can be checked on`http://localhost:8025`.

You can change the smtp configuration if required. However all emails with domain **example.com** will still go to mailhog.

**Building the images**
If you want to build the images locally:
    ```
    $ deploy/docker/build-all.sh
    ```


### Vagrant

This option allows you to run crAPI within a virtual machine, thus isolated from your system. Check [the setup instructions][setup-vagrant] for more details.


### Kubernetes
If you would like to deploy on kubernetes we have sample k8s configs already created. Check [the setup instructions][setup-k8s] for more details.


[setup-k8s]: ./setup.md#kubernetes
[setup-vagrant]: ./setup.md#vagrant
[Vagrant]: https://www.vagrantup.com/downloads
[VirtualBox]: https://www.virtualbox.org/wiki/Downloads
