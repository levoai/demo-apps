#!/bin/bash

# Remote Testing Helper Script
# Usage: ./remote-test.sh <target-url> [script-type]

TARGET_URL="$1"
SCRIPT_TYPE="${2:-quick}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if target URL is provided
if [ -z "$TARGET_URL" ]; then
    print_error "Target URL is required!"
    echo ""
    echo "Usage: $0 <target-url> [script-type]"
    echo ""
    echo "Examples:"
    echo "  $0 https://api.example.com"
    echo "  $0 https://api.example.com quick"
    echo "  $0 https://api.example.com traffic"
    echo "  $0 https://api.example.com continuous"
    echo ""
    echo "Available script types:"
    echo "  quick       - Quick test (default)"
    echo "  traffic     - Comprehensive traffic generation"
    echo "  continuous  - Continuous traffic generation"
    echo ""
    echo "Examples:"
    echo "  ./remote-test.sh https://my-api.example.com"
    echo "  ./remote-test.sh https://staging-api.company.com traffic"
    echo "  ./remote-test.sh https://prod-api.company.com continuous"
    exit 1
fi

# Validate URL format
if [[ ! "$TARGET_URL" =~ ^https?:// ]]; then
    print_error "Invalid URL format. Must start with http:// or https://"
    echo "Example: https://api.example.com"
    exit 1
fi

# Remove trailing slash if present
TARGET_URL="${TARGET_URL%/}"

print_status "Target URL: $TARGET_URL"
print_status "Script type: $SCRIPT_TYPE"

# Test connectivity
print_status "Testing connectivity to target URL..."
if curl -s --connect-timeout 10 "$TARGET_URL/health" > /dev/null 2>&1; then
    print_success "Connection successful!"
else
    print_warning "Could not connect to health endpoint. Continuing anyway..."
fi

# Run the appropriate script
case "$SCRIPT_TYPE" in
    "quick")
        print_status "Running quick test..."
        ./quick-test.sh "$TARGET_URL"
        ;;
    "traffic")
        print_status "Running comprehensive traffic generation..."
        node generate-traffic.js "$TARGET_URL"
        ;;
    "continuous")
        print_status "Running continuous traffic generation..."
        print_warning "This will run indefinitely. Press Ctrl+C to stop."
        node continuous-traffic.js "$TARGET_URL"
        ;;
    *)
        print_error "Unknown script type: $SCRIPT_TYPE"
        echo "Available types: quick, traffic, continuous"
        exit 1
        ;;
esac

print_success "Remote testing completed!" 