#!/bin/bash
set -e

# Usage information
usage() {
    cat << EOF
Usage: [NAMESPACE=<namespace>] $0 [OPTIONS]

Deploy crAPI (Completely Ridiculous API) to a Kubernetes cluster.

OPTIONS:
    -h, --help     Show this help message and exit

ENVIRONMENT VARIABLES:
    NAMESPACE      Target Kubernetes namespace (default: crapi)

EXAMPLES:
    # Deploy to default namespace (crapi)
    $0

    # Deploy to custom namespace
    NAMESPACE=crapi-dev $0

    # Deploy to staging environment
    NAMESPACE=crapi-staging $0

DESCRIPTION:
    This script deploys the crAPI application with all its components:
    - PostgreSQL database (version 17)
    - MongoDB database
    - Identity service (Java/Spring Boot)
    - Community service (Go)
    - Workshop service (Python)
    - Web frontend
    - Mailhog (email testing)

    Each deployment is isolated per namespace with:
    - Separate databases and persistent volumes
    - Namespace-specific RBAC (ClusterRoleBinding: waitfor-grant-NAMESPACE)
    - Independent service endpoints

VERIFICATION:
    Check deployment status:
        kubectl get pods -n <namespace>
        kubectl get svc -n <namespace>

    Check logs:
        kubectl logs -n <namespace> <pod-name>

CLEANUP:
    To remove a deployment:
        NAMESPACE=<namespace> ../cleanup_crapi.sh

EOF
    exit 0
}

# Parse arguments
for arg in "$@"; do
    case $arg in
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

cd "$(dirname $0)"

# Set namespace with default value
NAMESPACE=${NAMESPACE:-crapi}

echo "Deploying crAPI to namespace: ${NAMESPACE}"

# Create namespace (ignore error if it already exists)
kubectl create namespace ${NAMESPACE} 2>/dev/null || echo "Namespace ${NAMESPACE} already exists"

# Create temporary directory for processed manifests
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

echo "Processing RBAC manifests..."
# Copy and process RBAC files with namespace substitution
mkdir -p ${TEMP_DIR}/rbac
for file in ./rbac/*.yaml; do
    sed "s/NAMESPACE/${NAMESPACE}/g" "$file" > "${TEMP_DIR}/rbac/$(basename $file)"
done

# Apply manifests
echo "Applying RBAC..."
kubectl apply -f ${TEMP_DIR}/rbac

echo "Deploying database services..."
kubectl apply -n ${NAMESPACE} -f ./mongodb
kubectl apply -n ${NAMESPACE} -f ./postgres

echo "Deploying application services..."
kubectl apply -n ${NAMESPACE} -f ./mailhog
kubectl apply -n ${NAMESPACE} -f ./identity
kubectl apply -n ${NAMESPACE} -f ./community
kubectl apply -n ${NAMESPACE} -f ./workshop
kubectl apply -n ${NAMESPACE} -f ./payments
kubectl apply -n ${NAMESPACE} -f ./web

echo ""
echo "✓ Deployment complete!"
echo "Namespace: ${NAMESPACE}"
echo ""
echo "Check status with: kubectl get pods -n ${NAMESPACE}"
