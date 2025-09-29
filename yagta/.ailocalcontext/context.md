# GraphQL Testing API - AI Development Context

## Project Overview
Built a comprehensive GraphQL API in Node.js with TypeScript for security testing purposes. The application includes a complete vehicle and parking management system with JWT-based authentication.

## Key Decisions Made

### Technology Stack
- **Runtime**: Node.js 18 with TypeScript
- **GraphQL**: Apollo Server with TypeGraphQL for schema-first development
- **Authentication**: JWT with bcrypt for password hashing
- **Package Manager**: Yarn as requested
- **Containerization**: Docker & Docker Compose for easy deployment
- **Database**: In-memory data store for testing (PostgreSQL configured for future use)

### Architecture Decisions
1. **TypeGraphQL**: Chosen for type-safe GraphQL schema generation with decorators
2. **In-Memory Data Store**: Used for simplicity in testing environment, with PostgreSQL ready for production
3. **JWT Authentication**: Implemented with middleware for request context
4. **Input Validation**: Class-validator for GraphQL input validation
5. **Security Middleware**: Helmet, CORS, and custom auth middleware

### Data Models Implemented
1. **User**: Authentication and role management
2. **Vehicle**: Multiple types (CAR, MOTORCYCLE, TRUCK, VAN) with fuel types
3. **ParkingSlot**: Different slot types and statuses
4. **VehicleRevision**: Maintenance tracking with various revision types

### Security Features
- JWT-based authentication
- Password hashing with bcrypt
- Role-based authorization (USER/ADMIN)
- Input validation and sanitization
- CORS protection
- Security headers with Helmet

### Docker Setup
- Multi-service Docker Compose configuration
- PostgreSQL database service
- Redis for future caching
- Adminer for database management
- Proper networking and volume management

## Development Notes

### Challenges Encountered
1. **TypeScript Strict Mode**: Had to handle exactOptionalPropertyTypes properly
2. **JWT Types**: Some type issues with JWT library that were resolved
3. **GraphQL Schema**: Proper typing for input/output types with TypeGraphQL

### Testing Considerations
The application is designed as a security testing benchmark with:
- Multiple authentication flows
- Complex data relationships
- Various input validation scenarios
- CRUD operations on all entities
- GraphQL introspection enabled

### Default Data
Pre-configured users for testing:
- Admin: admin@test.com / admin123
- User: user@test.com / user123

## Future Enhancements
- Database integration (PostgreSQL)
- Rate limiting
- Advanced authorization rules
- Caching with Redis
- Unit and integration tests
- API documentation with GraphQL Playground

## Files Created
- Complete TypeScript GraphQL API
- Docker and Docker Compose configuration
- Comprehensive README with API documentation
- Environment configuration
- Security middleware and utilities

## Final Status
✅ **Project Successfully Completed**

### What Works:
- ✅ GraphQL API with JWT authentication
- ✅ All CRUD operations for Users, Vehicles, Parking Slots, and Vehicle Revisions
- ✅ TypeScript compilation and build process
- ✅ Docker containerization
- ✅ Development server with hot reload
- ✅ Health check endpoints
- ✅ Security middleware and authentication
- ✅ In-memory data store with sample data

## Security Testing Modifications
🔓 **Broken User Authentication (BUA) Vulnerabilities Introduced**

### Vulnerabilities Added:

#### GraphQL Endpoints (Bypassed Authentication):
- **User Data Exposure**: `users` query accessible without authentication
- **Vehicle Data Exposure**: `vehicles` query accessible without authentication  
- **Parking Slot Exposure**: `parkingSlots` query accessible without authentication
- **Vehicle Revision Exposure**: `vehicleRevisions` query accessible without authentication
- **User Profile Exposure**: `user` query accessible without authentication
- **Vehicle Creation Bypass**: `createVehicle` mutation accessible without authentication
- **Parking Slot Creation Bypass**: `createParkingSlot` mutation accessible without authentication

#### REST Endpoints (No Authentication):
- **`/api/users`**: Exposes all user data without authentication
- **`/api/vehicles`**: Exposes all vehicle data without authentication

#### Authentication Middleware Vulnerabilities:
- **Invalid Token Acceptance**: Any malformed token is accepted as valid
- **Default User Assignment**: Invalid tokens get assigned anonymous user role
- **authChecker Bypass**: Always returns true, bypassing all authentication checks

### Testing Scenarios:
These vulnerabilities allow automated tests to detect BUA by comparing:
- Authenticated vs unauthenticated responses
- Valid vs invalid JWT tokens
- Empty vs malformed authentication headers
- REST vs GraphQL endpoint access patterns

### Expected Test Results:
- Same sensitive data returned regardless of authentication status
- No authorization checks in vulnerable endpoints
- Identical responses for authenticated and unauthenticated requests
- REST endpoints expose sensitive data without any authentication

### Test Results Confirmed:
✅ REST endpoints `/api/users` and `/api/vehicles` expose sensitive data without authentication
✅ GraphQL queries return same data regardless of authentication status
✅ Invalid tokens are accepted and processed
✅ Authentication bypass works across all vulnerable endpoints
✅ **Stream not readable issue SOLVED** by disabling Apollo's body parser and using Express's body parser first

### Technical Issues Resolved:
1. **Stream not readable error**: Fixed by configuring Apollo Server with `bodyParserConfig: false`
2. **Body parser order**: Moved Express body parser to the very beginning
3. **GraphQL queries**: Now working perfectly with BUA vulnerabilities active

### Default Users:
- Admin: `admin@test.com` / `admin123`
- User: `user@test.com` / `user123`

### Access Points:
- API: http://localhost:4000
- GraphQL Playground: http://localhost:4000/graphql
- Health Check: http://localhost:4000/health

### Docker Commands:
```bash
# Build and run with Docker Compose
docker-compose up -d

# Build Docker image
docker build -t yagta .

# Run locally
yarn dev
```

### Issues Resolved:
1. ✅ TypeGraphQL authChecker requirement
2. ✅ JWT token generation (using hardcoded '24h' for simplicity)
3. ✅ TypeScript strict mode compatibility
4. ✅ Missing graphql-scalars dependency
5. ✅ Docker build and containerization
6. ✅ Stream not readable error (Apollo body parser conflict)

## Traffic Generation Scripts

### Purpose:
Generate comprehensive traffic against all GraphQL operations and REST endpoints with valid authentication tokens to help API discovery tools identify all available endpoints and detect BUA vulnerabilities.

### Available Scripts:
1. **`quick-test.sh`**: Fast verification of all endpoints with basic testing
2. **`generate-traffic.js`**: Complete testing of all GraphQL operations and REST endpoints
3. **`continuous-traffic.js`**: Ongoing traffic generation for long-term API discovery
4. **`TRAFFIC_GENERATION.md`**: Complete documentation for all scripts

### Script Features:
- **Authentication Testing**: Tests with no token, user token, and admin token
- **Complete Coverage**: All GraphQL queries and mutations tested
- **REST Endpoints**: All available REST endpoints tested
- **BUA Verification**: Confirms vulnerabilities by comparing authenticated vs unauthenticated responses
- **API Discovery Ready**: Generates traffic patterns for security tools to analyze

### Usage:
```bash
# Quick test
yarn test:quick

# Comprehensive traffic generation
yarn test:traffic

# Continuous traffic generation
yarn test:continuous
```

### Tested Operations:
- **Authentication**: Login, Register
- **User Operations**: Get all users, Get user by ID, Get current user
- **Vehicle Operations**: Get all vehicles, Get vehicle by ID, Get my vehicles, Create/Update/Delete vehicle
- **Parking Slot Operations**: Get all parking slots, Get parking slot by ID, Get my parking slots, Create/Update/Delete parking slot
- **Vehicle Revision Operations**: Get all revisions, Get revision by ID, Get revisions by vehicle, Create/Update/Delete revision
- **REST Endpoints**: All available REST endpoints 