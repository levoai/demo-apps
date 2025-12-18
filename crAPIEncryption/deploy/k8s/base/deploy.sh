#!/bin/bash
cd "$(dirname $0)"

# Set namespace with default value
NAMESPACE=${NAMESPACE:-crapi}

kubectl create namespace ${NAMESPACE}
#kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

# Replace NAMESPACE in rbac files
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS version
    find ./rbac -type f -exec sed -i '' "s/NAMESPACE/${NAMESPACE}/g" {} +
else
    # Linux version
    find ./rbac -type f -exec sed -i "s/NAMESPACE/${NAMESPACE}/g" {} +
fi

kubectl apply -n ${NAMESPACE} -f ./rbac
kubectl apply -n ${NAMESPACE} -f ./mongodb
kubectl apply -n ${NAMESPACE} -f ./postgres
kubectl apply -n ${NAMESPACE} -f ./mailhog
kubectl apply -n ${NAMESPACE} -f ./identity
kubectl apply -n ${NAMESPACE} -f ./community
kubectl apply -n ${NAMESPACE} -f ./workshop
kubectl apply -n ${NAMESPACE} -f ./web
