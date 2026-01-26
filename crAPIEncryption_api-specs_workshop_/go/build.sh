#!/bin/bash

# Build script for Go MCP server binary
# Usage: ./build.sh

set -e

echo "Building Go MCP Server Binary..."

# Create bin directory if it doesn't exist
mkdir -p bin

# Build the binary with optimizations
echo "Compiling Go binary..."
go build -ldflags="-s -w" -o bin/mcp-server

# Make binary executable
chmod +x bin/mcp-server

# Get current directory path
CURRENT_DIR=$(pwd)

# Update mcp-stdio.json with current directory
if [ -f "mcp-stdio.json" ]; then
    echo "Updating mcp-stdio.json with current directory: $CURRENT_DIR"
    sed -i.bak "s|\"/path/to/your/go/mcp/server/directory\"|\"$CURRENT_DIR\"|g" mcp-stdio.json
    sed -i.bak "s|\"./bin/mcp-server\"|\"$CURRENT_DIR/bin/mcp-server\"|g" mcp-stdio.json
    rm -f mcp-stdio.json.bak
    echo "mcp-stdio.json updated successfully!"
else
    echo "mcp-stdio.json not found, creating with current directory: $CURRENT_DIR"
    cat > mcp-stdio.json << EOF
{
  "mcpServers": {
    "mcp-server-stdio": {
      "command": "$CURRENT_DIR/bin/mcp-server",
      "env": {
        "API_BASE_URL": "https://your-api-base-url",
        "BEARER_TOKEN": "your-bearer-token"
      }
    }
  }
}
EOF
fi


EOF
fi

echo "Binary built successfully!"
echo "Usage: ./bin/mcp-server"
echo "MCP Config: mcp-stdio.json (updated with current directory)"
