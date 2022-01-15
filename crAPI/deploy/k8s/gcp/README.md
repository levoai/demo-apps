# Deployment for Levo's Hosted crAPI in GCP/GKE

This deployment is specific to Levo's hosted crAPI instance on GKE.

Levo uses a static (regional) ip for the web & mailhog services (external loadbalancer).

Refer to GCP instructions on creating static IPs and DNS A records
[here](https://cloud.google.com/kubernetes-engine/docs/tutorials/configuring-domain-name-static-ip).

Essentially the `ingress.yaml` in the `web` and `mailhog` directories needs to have their static IPs defined.

## Web Service Definition
```YAML
apiVersion: v1
kind: Service
metadata:
  name: crapi-web
  labels:
    app: crapi-web
spec:
  ports:
  - port: 80
    nodePort: 30080
    name: nginx
  type: LoadBalancer
  loadBalancerIP: "YOUR.WEB-STATIC-IP.ADDRESS.HERE"
  selector:
    app: crapi-web
```

# Mailhog Service Definition
```YAML
apiVersion: v1
kind: Service
metadata:
  name: mailhog-web
  namespace: crapi
spec:
  ports:
  - name: web
    port: 8025
    nodePort: 30025
    protocol: TCP
  selector:
    app: mailhog
  sessionAffinity: None
  type: LoadBalancer
  loadBalancerIP: "YOUR.MAILHOG-STATIC-IP.ADDRESS.HERE"
```

## Current Address Allocations
```bash
# setup gcloud to point to hosted crAPI first
gcloud config set project graphic-tide-305619
```

### Web
```bash
gcloud compute addresses describe crapi-web-ip --region us-central1
address: 35.226.144.72
addressType: EXTERNAL
creationTimestamp: '2022-01-15T12:40:16.662-08:00'
description: static IP for crAPIs web service
id: '3962482400378654687'
kind: compute#address
name: crapi-web-ip
networkTier: PREMIUM
region: https://www.googleapis.com/compute/v1/projects/graphic-tide-305619/regions/us-central1
selfLink: https://www.googleapis.com/compute/v1/projects/graphic-tide-305619/regions/us-central1/addresses/crapi-web-ip
status: RESERVED
```

### Mailhog
```bash
gcloud compute addresses describe crapi-mailhog-ip --region us-central1
address: 35.232.101.208
addressType: EXTERNAL
creationTimestamp: '2022-01-15T12:55:11.734-08:00'
description: ''
id: '929205354381609536'
kind: compute#address
name: crapi-mailhog-ip
networkTier: PREMIUM
region: https://www.googleapis.com/compute/v1/projects/graphic-tide-305619/regions/us-central1
selfLink: https://www.googleapis.com/compute/v1/projects/graphic-tide-305619/regions/us-central1/addresses/crapi-mailhog-ip
status: RESERVED

```