# Running crAPIEncryption with Docker

## Quick Start

1. **Navigate to the docker directory:**
   ```bash
   cd /Users/jeevanchavva/Desktop/demo-apps/crAPIEncryption/deploy/docker
   ```

2. **Build and start all services:**
   ```bash
   docker-compose up -d --build
   ```

   This will:
   - Build the custom `crapi-identity` image with encryption changes
   - Start PostgreSQL database
   - Start MongoDB
   - Start MailHog (for email testing)
   - Start the identity service

3. **Check if services are running:**
   ```bash
   docker-compose ps
   ```

4. **View logs:**
   ```bash
   # View all logs
   docker-compose logs -f
   
   # View only identity service logs
   docker-compose logs -f crapi-identity
   ```

5. **Stop all services:**
   ```bash
   docker-compose down
   ```

6. **Stop and remove volumes (clean start):**
   ```bash
   docker-compose down -v
   ```

## Accessing the Application

Once running, the application will be available at:
- **API Base URL:** `http://localhost:8080`
- **Health Check:** `http://localhost:8080/identity/health_check`
- **Encryption API:** `http://localhost:8080/identity/api/encryption/encrypt`
- **Decryption API:** `http://localhost:8080/identity/api/encryption/decrypt`

## Testing the Encryption APIs

### Encrypt data:
```bash
curl -X POST http://localhost:8080/identity/api/encryption/encrypt \
  -H "Content-Type: application/json" \
  -d '{"data":"hello world"}'
```

### Decrypt data:
```bash
curl -X POST http://localhost:8080/identity/api/encryption/decrypt \
  -H "Content-Type: application/json" \
  -d '{"data":"<encrypted_string_from_previous_response>"}'
```

## Troubleshooting

- **If build fails:** Make sure you have Docker and Docker Compose installed
- **If port 8080 is in use:** Stop the service using that port or change the port mapping in `docker-compose.yml`
- **If database connection fails:** Wait a few seconds for PostgreSQL to fully start, then restart the identity service: `docker-compose restart crapi-identity`
