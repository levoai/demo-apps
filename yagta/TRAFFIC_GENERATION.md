# Traffic Generation Scripts for API Discovery

This document describes the traffic generation scripts designed to help API discovery tools identify all available GraphQL operations and REST endpoints in the testing application.

## 🎯 Purpose

These scripts generate comprehensive traffic against all GraphQL operations and REST endpoints with valid authentication tokens, enabling API discovery tools to:

- **Discover all available endpoints** through traffic analysis
- **Map authentication requirements** by testing with and without tokens
- **Identify BUA vulnerabilities** by comparing authenticated vs unauthenticated responses
- **Generate realistic traffic patterns** for security testing

## 📁 Available Scripts

### 1. Quick Test Script (`quick-test.sh`)

**Purpose**: Fast verification of all endpoints with basic testing

**Usage**:
```bash
# Make executable (first time only)
chmod +x quick-test.sh

# Run quick test (localhost)
./quick-test.sh

# Run quick test (remote)
./quick-test.sh https://api.example.com

# Or use npm script (localhost)
yarn test:quick
```

**Features**:
- ✅ Tests all REST endpoints (`/`, `/health`, `/api/users`, `/api/vehicles`)
- ✅ Tests key GraphQL queries (`users`, `vehicles`, `parkingSlots`)
- ✅ Tests key GraphQL mutations (`createVehicle`, `createParkingSlot`)
- ✅ Tests with and without authentication
- ✅ Uses both user and admin tokens
- ✅ Provides summary statistics

**Output Example**:
```
🚀 Quick API Test Script
========================
🔐 Getting authentication tokens...
✅ User token: eyJhbGciOiJIUzI1NiIs...
✅ Admin token: eyJhbGciOiJIUzI1NiIs...

📊 Testing REST Endpoints...
============================
🔍 Testing / (root)
{"message":"GraphQL Testing API","version":"1.0.0"...}

🔍 Testing /health
{"status":"OK","timestamp":"2025-08-04T12:40:55.152Z"}

🔍 Testing /api/users (no auth)
2

🔍 Testing /api/users (with user token)
2

📊 Testing GraphQL Queries...
=============================
🔍 Testing users query (no auth)
2

🔍 Testing users query (with user token)
2

✅ Quick test completed!
📊 Summary: All endpoints tested with and without authentication
🎯 Ready for API discovery tools!
```

### 2. Comprehensive Traffic Generator (`generate-traffic.js`)

**Purpose**: Complete testing of all GraphQL operations and REST endpoints

**Usage**:
```bash
# Install axios if not already installed
yarn add axios

# Run comprehensive traffic generation (localhost)
node generate-traffic.js

# Run comprehensive traffic generation (remote)
node generate-traffic.js https://api.example.com

# Or use npm script (localhost)
yarn test:traffic
```

**Features**:
- ✅ **Authentication Operations**: Login, Register
- ✅ **User Operations**: Get all users, Get user by ID, Get current user
- ✅ **Vehicle Operations**: Get all vehicles, Get vehicle by ID, Get my vehicles, Create/Update/Delete vehicle
- ✅ **Parking Slot Operations**: Get all parking slots, Get parking slot by ID, Get my parking slots, Create/Update/Delete parking slot
- ✅ **Vehicle Revision Operations**: Get all revisions, Get revision by ID, Get revisions by vehicle, Create/Update/Delete revision
- ✅ **REST Endpoints**: All available REST endpoints
- ✅ **Multiple Authentication Scenarios**: No token, User token, Admin token
- ✅ **Detailed Reporting**: Success/failure statistics and operation summaries

**Tested Operations**:

#### Authentication
- `Login User` - Login with user credentials
- `Login Admin` - Login with admin credentials  
- `Register New User` - Register new user account

#### User Queries
- `Get All Users` - Retrieve all users
- `Get User by ID` - Get specific user by ID
- `Get Current User` - Get authenticated user profile

#### Vehicle Queries
- `Get All Vehicles` - Retrieve all vehicles
- `Get Vehicle by ID` - Get specific vehicle by ID
- `Get My Vehicles` - Get vehicles owned by current user

#### Vehicle Mutations
- `Create Vehicle` - Create new vehicle
- `Update Vehicle` - Update existing vehicle
- `Delete Vehicle` - Delete vehicle

#### Parking Slot Queries
- `Get All Parking Slots` - Retrieve all parking slots
- `Get Parking Slot by ID` - Get specific parking slot by ID
- `Get My Parking Slots` - Get parking slots owned by current user

#### Parking Slot Mutations
- `Create Parking Slot` - Create new parking slot
- `Update Parking Slot` - Update existing parking slot
- `Delete Parking Slot` - Delete parking slot

#### Vehicle Revision Queries
- `Get All Vehicle Revisions` - Retrieve all vehicle revisions
- `Get Vehicle Revision by ID` - Get specific revision by ID
- `Get Vehicle Revisions by Vehicle` - Get revisions for specific vehicle

#### Vehicle Revision Mutations
- `Create Vehicle Revision` - Create new vehicle revision
- `Update Vehicle Revision` - Update existing revision
- `Delete Vehicle Revision` - Delete revision

#### REST Endpoints
- `/` - Root endpoint
- `/health` - Health check
- `/api/users` - Users API
- `/api/vehicles` - Vehicles API

### 3. Continuous Traffic Generator (`continuous-traffic.js`)

**Purpose**: Ongoing traffic generation for long-term API discovery and monitoring

**Usage**:
```bash
# Run continuous traffic generation (localhost)
node continuous-traffic.js

# Run continuous traffic generation (remote)
node continuous-traffic.js https://api.example.com

# Or use npm script (localhost)
yarn test:continuous
```

**Features**:
- ✅ **Continuous Operation**: Runs indefinitely until stopped (Ctrl+C)
- ✅ **Token Refresh**: Automatically refreshes authentication tokens every 10 cycles
- ✅ **Randomized Data**: Uses random values for mutations to create varied traffic
- ✅ **Error Handling**: Graceful error handling with automatic retry
- ✅ **Progress Monitoring**: Real-time progress updates and statistics
- ✅ **Graceful Shutdown**: Clean shutdown on Ctrl+C

**Output Example**:
```
🚀 Starting Continuous Traffic Generation for API Discovery
============================================================
This script will generate continuous traffic to help API discovery tools
Press Ctrl+C to stop
============================================================
✅ Got 2 valid tokens

🔄 Cycle 1
🔄 Generating traffic... (12:40:55 PM)
✅ Success: 45, ❌ Failed: 0, 📊 Total: 45

🔄 Cycle 2
🔄 Generating traffic... (12:40:58 PM)
✅ Success: 45, ❌ Failed: 0, 📊 Total: 45

🔄 Refreshing tokens...
✅ Got 2 valid tokens
```

## 🔧 Configuration

### Target URL
All scripts now support parameterized target URLs for remote testing:

#### Local Testing (Default)
```bash
# Quick test (localhost)
yarn test:quick

# Comprehensive traffic (localhost)
yarn test:traffic

# Continuous traffic (localhost)
yarn test:continuous
```

#### Remote Testing
```bash
# Using the remote test helper (recommended)
./remote-test.sh https://api.example.com
./remote-test.sh https://staging-api.company.com traffic
./remote-test.sh https://prod-api.company.com continuous

# Direct script usage
./quick-test.sh https://api.example.com
node generate-traffic.js https://api.example.com
node continuous-traffic.js https://api.example.com
```

#### Manual Configuration
If you need to modify the default URL:

1. **Quick Test Script**: Edit `BASE_URL` variable in `quick-test.sh`
2. **JavaScript Scripts**: Edit `BASE_URL` constant in the respective `.js` files

### Authentication Credentials
Default test credentials:
- **User**: `user@test.com` / `user123`
- **Admin**: `admin@test.com` / `admin123`

To change credentials, update the login requests in the scripts.

### Request Delays
- **Quick Test**: No delays (fast execution)
- **Comprehensive Traffic**: 100ms delay between operations
- **Continuous Traffic**: 50ms delay between operations, 2s between cycles

## 📊 Expected Results

### BUA Vulnerability Confirmation
All scripts should demonstrate that:

1. **Same Response for Authenticated/Unauthenticated Requests**
   - GraphQL queries return identical data regardless of authentication
   - REST endpoints return identical data regardless of authentication

2. **Invalid Tokens Accepted**
   - Requests with invalid tokens succeed instead of failing
   - Anonymous user assigned automatically

3. **Sensitive Data Exposure**
   - User data accessible without authentication
   - Vehicle data accessible without authentication
   - Parking slot data accessible without authentication

### API Discovery Benefits
The traffic generation helps discovery tools identify:

- **All GraphQL Operations**: Queries and mutations
- **All REST Endpoints**: Available API routes
- **Authentication Patterns**: Token-based auth implementation
- **Data Models**: Entity relationships and structures
- **Error Handling**: Response patterns for various scenarios

## 🚀 Integration with Security Tools

### For API Discovery Tools
1. **Run continuous traffic**: `yarn test:continuous`
2. **Monitor traffic patterns**: Analyze request/response patterns
3. **Map endpoints**: Identify all available operations
4. **Detect vulnerabilities**: Compare authenticated vs unauthenticated responses

### For Security Testing Tools
1. **Baseline traffic**: Use comprehensive script for initial discovery
2. **Vulnerability testing**: Compare responses with and without authentication
3. **BUA detection**: Identify broken authentication patterns
4. **Continuous monitoring**: Use continuous script for ongoing testing

## 📝 Troubleshooting

### Common Issues

1. **"axios not found"**
   ```bash
   yarn add axios
   ```

2. **"Permission denied" for quick-test.sh**
   ```bash
   chmod +x quick-test.sh
   ```

3. **"Connection refused"**
   - Ensure the GraphQL server is running: `yarn dev`
   - Check the base URL configuration

4. **"jq command not found"**
   - Install jq: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)
   - Or remove jq usage from quick-test.sh

### Debug Mode
Add debug logging to any script by adding:
```javascript
console.log('Request:', { url, headers, data });
console.log('Response:', response.data);
```

## 🎯 Best Practices

1. **Start with Quick Test**: Use `quick-test.sh` for initial verification
2. **Use Comprehensive for Discovery**: Use `generate-traffic.js` for thorough testing
3. **Use Continuous for Monitoring**: Use `continuous-traffic.js` for ongoing discovery
4. **Monitor Results**: Check success/failure rates to ensure proper operation
5. **Verify BUA**: Confirm that authenticated and unauthenticated responses are identical

## 📈 Performance Considerations

- **Quick Test**: ~30 seconds for complete test
- **Comprehensive Traffic**: ~2-3 minutes for full coverage
- **Continuous Traffic**: Runs indefinitely, ~45 requests per cycle

## 🔒 Security Notes

⚠️ **Important**: These scripts are designed for testing purposes only. The BUA vulnerabilities are intentionally implemented for security testing. Do not use this application in production environments.

The scripts generate traffic that demonstrates:
- Broken User Authentication (BUA) vulnerabilities
- Sensitive data exposure without authentication
- Invalid token acceptance
- Authentication bypass patterns

This makes the application ideal for testing security tools that detect authentication bypass vulnerabilities. 