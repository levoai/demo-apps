#!/usr/bin/env bash

NAMESPACE={$NAMESPACE:-crapi}

# Delete the persistent volumes
kubectl get pvc -n $NAMESPACE

# Delete the persistent volume claims
kubectl get pvc -n $NAMESPACE -o name | xargs kubectl delete pvc -n $NAMESPACE

# Delete the entire crapi namespace
kubectl delete namespace --wait=true $NAMESPACE

exit 0