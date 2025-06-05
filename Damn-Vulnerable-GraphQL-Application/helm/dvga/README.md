# Damn Vulnerable GraphQL Application Helm Chart

This Helm chart deploys the Damn Vulnerable GraphQL Application (DVGA) in a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.12+
- Helm 3.0+

## Installing the Chart

To install the chart with the release name `dvga`:

```bash
# From the Damn-Vulnerable-GraphQL-Application directory
helm install dvga ./helm/dvga
```

The command deploys DVGA on the Kubernetes cluster with default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

## Uninstalling the Chart

To uninstall/delete the `dvga` deployment:

```bash
helm uninstall dvga
```

## Parameters

The following table lists the configurable parameters of the DVGA chart and their default values.

| Parameter                | Description                                         | Default           |
|--------------------------|-----------------------------------------------------|-------------------|
| `replicaCount`           | Number of replicas                                  | `1`               |
| `image.repository`       | Image repository                                    | `dolevf/dvga`     |
| `image.tag`              | Image tag                                           | `latest`          |
| `image.pullPolicy`       | Image pull policy                                   | `IfNotPresent`    |
| `service.type`           | Kubernetes Service type                             | `ClusterIP`       |
| `service.port`           | Service HTTP port                                   | `5013`            |
| `ingress.enabled`        | Enable ingress controller resource                  | `false`           |
| `ingress.hosts[0].host`  | Hostname to your DVGA installation                  | `dvga.local`      |
| `resources`              | CPU/Memory resource requests/limits                 | See values.yaml   |
| `env.WEB_HOST`           | Host to bind the application                        | `0.0.0.0`         |
| `env.WEB_PORT`           | Port to bind the application                        | `5013`            |
| `gameMode`               | Game mode (beginner or expert)                      | `beginner`        |

## Accessing the Application

After deploying the chart, you can access the application by:

1. **Port forwarding** (quickest way for testing):
   ```bash
   kubectl port-forward svc/dvga 5013:5013
   ```
   Then access the application at http://localhost:5013

2. **Using an Ingress**:
   If you have enabled the ingress and have a properly configured ingress controller, you can access the application at the host specified in your ingress configuration.

## Warning

DVGA is intentionally vulnerable and should only be deployed in secure, controlled environments used for security training and testing. Never deploy in production environments or expose it to the internet. 