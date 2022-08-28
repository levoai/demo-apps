#!/usr/bin/env bash

# Delete the entire crapi namespace
kubectl delete namespace --wait=true crapi

# Delete the persistent volumes
kubectl get pvc -ncrapi

for pv in `kubectl get pv`
do
  kubectl delete pv --grace-period=0 --timeout=0s --force=true $pv
done

exit 0