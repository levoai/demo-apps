#!/bin/bash
set -e
cd "$(dirname $0)"

NAMESPACE=${NAMESPACE:-crapi}

kubectl create namespace $NAMESPACE | true
#kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

# Replace NAMESPACE in rbac files
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS version
    find ./rbac -type f -exec sed -i '' "s/NAMESPACE/${NAMESPACE}/g" {} +
else
    # Linux version
    find ./rbac -type f -exec sed -i "s/NAMESPACE/${NAMESPACE}/g" {} +
fi

kubectl apply -n $NAMESPACE -f ../base/rbac
kubectl apply -n $NAMESPACE -f ../base/mongodb
kubectl apply -n $NAMESPACE -f ../base/postgres
kubectl apply -n $NAMESPACE -f ./mailhog # Has Levo specific static IP address
kubectl apply -n $NAMESPACE -f ../base/identity
kubectl apply -n $NAMESPACE -f ../base/community
kubectl apply -n $NAMESPACE -f ../base/workshop
kubectl apply -n $NAMESPACE -f ./web # Has Levo specific static IP address
