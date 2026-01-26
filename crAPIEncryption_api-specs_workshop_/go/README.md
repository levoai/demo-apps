# OWASP crAPI Workshop API MCP Server

This MCP (Model Content Protocol) server provides access to OWASP crAPI Workshop API API functionality through HTTP, HTTPS, and STDIO transport modes.

## Features

- Multiple transport mode support (HTTP, HTTPS, and STDIO)
- Dynamic configuration through HTTP headers
- Automatic tool generation from API documentation
- Docker support for easy deployment
- Cross-platform Go binary compilation
- Production-ready deployment workflows


## Prerequisites

- Go 1.24.6 or later installed
- Docker (for containerized deployment)
- Git (for cloning the repository)

## Building the Project

### Option 1: Direct Go Build
1. Clone the repository
2. Navigate to the project directory
3. Build the project:

```bash
go build -o mcp-server
```

### Option 2: Using Build Script
1. Make the build script executable:
```bash
chmod +x build.sh
```
2. Run the build script:
```bash
./build.sh
```

This will:
- Build the Go binary into `bin/mcp-server`
- Generates ready to use `mcp-stdio.json` with the correct paths

## Running the MCP Server

The server can run in three modes [STDIO, HTTP, HTTPS] based on the **TRANSPORT** environment variable:

### Transport Modes for Configuring MCP Servers

| Transport Mode | Use Case | Configuration File | 
|----------------|----------|----------------------|
| **STDIO**      | Direct integration           | `mcp-stdio.json`   | 
| **STDIO/HTTP** | Directly run docker image    | `mcp-docker.json`  | 
| **HTTP**       | Web service on localhost/remote server | `mcp-http.json` | 
| **HTTPS**      | Secure web service with SSL/TLS | `mcp-https.json` | 


### Method 1: Direct Binary Execution
**Best for**: STDIO mode for local development and direct Cursor integration

**Step 1: Build the Server**
```bash
# Option A: Direct build
go build -o mcp-server

# Option B: Using build script (recommended)
chmod +x build.sh
./build.sh
```

**Step 2: Configure MCP Server**
Use the generated `mcp-stdio.json` file:

```json
{
  "mcpServers": {
    "OWASP crAPI Workshop API-mcp-server-stdio": {
      "command": "/path/to/your/project/mcp-server",
      "env": {
        "API_BASE_URL": "https://your-api-base-url",
        "BEARER_TOKEN": "your-bearer-token"
        // Alternative authentication options (use only one):
        // "API_KEY": "your-api-key",
        // "BASIC_AUTH": "your-basic-auth-credentials",
      }
    }
  }
}
```


### Method 2: Docker Mode (Containerized Deployment)
**Best for**: HTTP or HTTPS Docker mode for production deployment, scaling, and consistent environments

**Step 1: Build Docker Image**
```bash
docker build -t OWASP crAPI Workshop API-mcp-server .
```

***Option A: Let agent run the container directly:***

```json
{
  "mcpServers": {
    "OWASP crAPI Workshop API-mcp-server-docker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-p", "8080:8080",
        "-e", "API_BASE_URL=https://your.api.url",
        "-e", "BEARER_TOKEN=your-token-here",
        // Alternative authentication options (use any one):
        // "-e", "API_KEY=your-api-key",
        // "-e", "BASIC_AUTH=your-basic-auth-credentials",
        "OWASP crAPI Workshop API-mcp-server"
      ]
    }
  }
}
```


***Option B: Run the container manually:***
```bash
docker run -d \
  --name OWASP crAPI Workshop API-mcp-server \
  -p 8080:8080 \
  -e API_BASE_URL="https://your-api-base-url" \
  -e BEARER_TOKEN="your-bearer-token" \
  // Alternative authentication options (use any one):
  // "-e", "API_KEY=your-api-key",
  // "-e", "BASIC_AUTH=your-basic-auth-credentials",
  -e TRANSPORT="http" \
  -e PORT="8080" \
  OWASP crAPI Workshop API-mcp-server
```

***Option C: Docker Compose (Recommended)***

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```



**Step 2: Configure MCP Server**

- HTTP Mode `mcp-http.json`

```json
{
  "mcpServers": {
    "OWASP crAPI Workshop API-mcp-server-http": {
      "url": "http://localhost:8080/mcp" or "http://remote-server:8080/mcp",
      "headers": {
        "API_BASE_URL": "https://your-api-base-url",
        "BEARER_TOKEN": "your-bearer-token"
        // Alternative authentication options (use any one):
        // "API_KEY": "your-api-key",
        // "BASIC_AUTH": "your-basic-auth-credentials",
      }
    }
  }
}
```

- HTTPS Mode `mcp-https.json`
```json
{
  "mcpServers": {
    "OWASP crAPI Workshop API-mcp-server-https": {
      "url": "https://localhost:8443/mcp" or "https://remote-server:8443/mcp",
      "headers": {
        "API_BASE_URL": "https://your-api-base-url",
        "BEARER_TOKEN": "your-bearer-token",
        "CERT_FILE": "./certs/cert.pem",
        "KEY_FILE": "./certs/key.pem"
        // Alternative authentication options (use any one):
        // "API_KEY": "your-api-key",
        // "BASIC_AUTH": "your-basic-auth-credentials",
      }
    }
  }
}
```


#### Required Environment Variables for HTTPS Mode:
- `TRANSPORT`: Set to "http" or "https" **(Required)**
- `PORT`: Server port **(Required)**
- `CERT_FILE`: Path to SSL certificate file (for HTTPS mode)
- `KEY_FILE`: Path to SSL private key file (for HTTPS mode)

#### Configuration through HTTP Headers:
In HTTP mode, API configuration is provided via HTTP headers for each request:
- `API_BASE_URL`: **(Required)** Base URL for the API
- `BEARER_TOKEN`: Bearer token for authentication
- `API_KEY`: API key for authentication
- `BASIC_AUTH`: Basic authentication credentials

The server will start on the configured port with the following endpoints:
- `/mcp`: HTTP/HTTPS endpoint for MCP communication (requires API_BASE_URL header)
- `/`: Health check endpoint

**Note**: At least one authentication header (BEARER_TOKEN, API_KEY, or BASIC_AUTH) should be provided unless the API explicitly doesn't require authentication.

## Environment Variable Case Sensitivity

The server supports both uppercase and lowercase transport environment variables:
- `TRANSPORT` (uppercase) - checked first
- `transport` (lowercase) - fallback if uppercase not set

Valid values: "http", "HTTP", "https", "HTTPS", "stdio", or unset (defaults to STDIO)

## Authentication

### HTTP Mode
Authentication is provided through HTTP headers on each request:
- `BEARER_TOKEN`: Bearer token
- `API_KEY`: API key
- `BASIC_AUTH`: Basic authentication

### STDIO Mode
Authentication is provided through environment variables:
- `BEARER_TOKEN`: Bearer token
- `API_KEY`: API key
- `BASIC_AUTH`: Basic authentication

## Health Check

When running in HTTP mode, you can check server health at the root endpoint (`/`).
Expected response: `{"status":"ok"}`

## Transport Modes Summary

### STDIO Mode (TRANSPORT=stdio or unset)
- Uses standard input/output for communication
- Configuration through environment variables only
- Requires API_BASE_URL environment variable
- Suitable for command-line usage

### HTTP Mode (TRANSPORT=http or TRANSPORT=HTTP)
- Uses streamable HTTP server
- Configuration provided via HTTP headers for each request
- Requires API_BASE_URL header for each request
- Endpoint: `/mcp`
- Port configured via PORT environment variable (defaults to 8080)

### HTTPS Mode (TRANSPORT=https or TRANSPORT=HTTPS)
- Uses streamable HTTPS server with SSL/TLS encryption
- Configuration provided via HTTP headers for each request
- Requires API_BASE_URL header for each request
- Endpoint: `/mcp`
- Port configured via PORT environment variable (defaults to 8443)
- **Requires SSL certificate and private key files (CERT_FILE and KEY_FILE)**

## License

Generated by CodeGlide MCP Generator

