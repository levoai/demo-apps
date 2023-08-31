Setup | crAPI
=============

## Docker Compose

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

**Note**: All emails are sent to mailhog service by default and can be checked on `http://localhost:8025`.
You can change the smtp configuration if required. However all emails with domain **example.com** will still go to mailhog.


## Kubernetes 

###  Minikube

Make sure minikube is up and running as well as the following addons:
`storage-provisioner`, `default-storageclass`, and `registry`.

1. Expose minikube registry to Docker

    ```
    $ docker run --rm -it --network=host alpine ash -c "apk add socat && socat TCP-LISTEN:5000,reuseaddr,fork TCP:$(minikube ip):5000"
    ```

2. Bring the k8s cluster up

    ```
    $ deploy/k8s/minikube/deploy.sh
    ```

3. Run the following command to get the URLs
    ```
    crAPI URL:
    $ echo "http://$(minikube ip):30080"
    ```
    ```
    Mailhog URL:
    echo "http://$(minikube ip):30025"
    ```

###  All other K8s installation flavors

1. Deploy to K8s using pre-built images from Docker Hub.

    ```
    $ deploy/k8s/base/deploy.sh
    ```

2. Retrieve the external IPs for crAPI Web & Mailhog services

    ```
    kubectl get services -n crapi
    ```
    This will produce output similar to what is shown below:
    
    ```
    NAME              TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)          AGE
    crapi-community   ClusterIP      10.84.14.130   <none>           8087/TCP         3h1m
    crapi-identity    ClusterIP      10.84.5.8      <none>           8080/TCP         3h1m
    crapi-web         LoadBalancer   10.84.12.81    35.232.101.208   80:30080/TCP     3h
    crapi-workshop    ClusterIP      10.84.9.205    <none>           8000/TCP         3h
    mailhog           ClusterIP      10.84.4.117    <none>           1025/TCP         3h1m
    mailhog-web       LoadBalancer   10.84.8.135    35.226.144.72    8025:30025/TCP   3h1m
    mongodb           ClusterIP      10.84.0.178    <none>           27017/TCP        3h1m
    postgresdb        ClusterIP      10.84.13.80    <none>           5432/TCP         3h1m
    ```

    Note down the `EXTERNAL-IP` values for `crapi-web` and `mailhog-web` services. You will need them in the step below.

3. Access crAPI & Mailhog via web

    Replace the EXTERNAL-IP template values with the actual values noted from the previous step.

    crAPI URL: **`http://<crapi-web EXTERNAL-IP>`**
    
    Mailhog URL: **`http://<mailhog-web EXTERNAL-IP:8025>`**

## Vagrant

This option allows you to run crAPI within a virtual machine, thus isolated from
your system. You'll need to have [Vagrant] and, for example [VirtualBox] installed.

1. Clone crAPI repository
    ```
    $ git clone [REPOSITORY-URL]
    ```
2. Start crAPI Virtual Machine
    ```
    $ cd deploy/vagrant && vagrant up
    ```
3. Visit `http://192.168.33.20`

**Note**: All emails are sent to mailhog service by default and can be checked on `http://192.168.33.20:8025`.
You can change the smtp configuration if required. However all emails with domain **example.com** will still go to mailhog.

To remove crAPI completely from your system, run the following command from the repository root directory:

```
$ cd deploy/vagrant && vagrant destroy
```

[Vagrant]: https://www.vagrantup.com/downloads
[VirtualBox]: https://www.virtualbox.org/wiki/Downloads
