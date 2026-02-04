#!/usr/bin/env bash
set -e

# Usage information
usage() {
    cat << EOF
Usage: [NAMESPACE=<namespace>] $0 [OPTIONS]

Clean up and remove a crAPI deployment from a Kubernetes cluster.

OPTIONS:
    -h, --help     Show this help message and exit
    -y, --yes      Skip confirmation prompt (auto-confirm deletion)

ENVIRONMENT VARIABLES:
    NAMESPACE      Target Kubernetes namespace to delete (default: crapi)

EXAMPLES:
    # Clean up default namespace (crapi) with confirmation
    $0

    # Clean up custom namespace
    NAMESPACE=crapi-dev $0

    # Clean up without confirmation prompt
    NAMESPACE=crapi-staging $0 -y

    # Clean up and auto-confirm
    NAMESPACE=crapi-test $0 --yes

DESCRIPTION:
    This script performs a complete cleanup of a crAPI deployment:
    1. Lists all persistent volume claims in the namespace
    2. Deletes all PVCs (PostgreSQL and MongoDB data)
    3. Deletes the entire namespace (removes all resources)
    4. Removes namespace-specific ClusterRoleBinding (waitfor-grant-NAMESPACE)

WARNING:
    This action is DESTRUCTIVE and will delete:
    - All pods, services, and deployments
    - All database data (PostgreSQL and MongoDB)
    - All ConfigMaps and secrets
    - The entire namespace

    Data cannot be recovered after deletion!

VERIFICATION:
    Before cleanup, check what will be deleted:
        kubectl get all -n <namespace>
        kubectl get pvc -n <namespace>

    After cleanup, verify namespace is gone:
        kubectl get namespace <namespace>

EOF
    exit 0
}

# Parse arguments
AUTO_CONFIRM=false
for arg in "$@"; do
    case $arg in
        -h|--help)
            usage
            ;;
        -y|--yes)
            AUTO_CONFIRM=true
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

NAMESPACE=${NAMESPACE:-crapi}

echo "============================================"
echo "crAPI Cleanup Script"
echo "============================================"
echo "Target namespace: $NAMESPACE"
echo ""

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "Error: Namespace '$NAMESPACE' does not exist"
    exit 1
fi

# Show what will be deleted
echo "Resources that will be deleted:"
echo ""
echo "--- Pods ---"
kubectl get pods -n "$NAMESPACE" 2>/dev/null || echo "No pods found"
echo ""
echo "--- Services ---"
kubectl get svc -n "$NAMESPACE" 2>/dev/null || echo "No services found"
echo ""
echo "--- Persistent Volume Claims ---"
kubectl get pvc -n "$NAMESPACE" 2>/dev/null || echo "No PVCs found"
echo ""

# Confirmation prompt
if [ "$AUTO_CONFIRM" = false ]; then
    echo "============================================"
    echo "WARNING: This will DELETE ALL resources in namespace '$NAMESPACE'"
    echo "This action CANNOT be undone!"
    echo "============================================"
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Cleanup cancelled."
        exit 0
    fi
fi

echo ""
echo "Starting cleanup..."
echo ""

# Delete persistent volume claims
echo "Deleting persistent volume claims..."
if kubectl get pvc -n "$NAMESPACE" -o name 2>/dev/null | grep -q .; then
    kubectl delete pvc --all -n "$NAMESPACE" --wait=true
    echo "✓ PVCs deleted"
else
    echo "No PVCs to delete"
fi

# Delete namespace-specific ClusterRoleBinding
echo ""
echo "Deleting ClusterRoleBinding..."
if kubectl get clusterrolebinding "waitfor-grant-$NAMESPACE" &> /dev/null; then
    kubectl delete clusterrolebinding "waitfor-grant-$NAMESPACE"
    echo "✓ ClusterRoleBinding 'waitfor-grant-$NAMESPACE' deleted"
else
    echo "ClusterRoleBinding not found (may have been deleted already)"
fi

# Delete the entire namespace
echo ""
echo "Deleting namespace '$NAMESPACE'..."
kubectl delete namespace --wait=true "$NAMESPACE"

echo ""
echo "============================================"
echo "✓ Cleanup complete!"
echo "Namespace '$NAMESPACE' has been removed."
echo "============================================"

exit 0