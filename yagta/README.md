# GraphQL Testing API

A comprehensive GraphQL API built with Node.js, TypeScript, and Apollo Server for security testing purposes. This application provides a complete vehicle and parking management system with JWT-based authentication.

## Features

- **JWT Authentication**: Secure login and registration with JWT tokens
- **User Management**: User registration, login, and profile management
- **Vehicle Management**: CRUD operations for vehicles with various types and fuel types
- **Parking Slot Management**: Manage parking slots with different types and statuses
- **Vehicle Revisions**: Track maintenance, inspections, and repairs
- **GraphQL API**: Full GraphQL schema with queries and mutations
- **TypeScript**: Fully typed with TypeScript for better development experience
- **Docker Support**: Complete Docker and Docker Compose setup

## Technology Stack

- **Runtime**: Node.js 18
- **Language**: TypeScript
- **Framework**: Express.js
- **GraphQL**: Apollo Server with TypeGraphQL
- **Authentication**: JWT with bcrypt for password hashing
- **Package Manager**: Yarn
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL (configured but using in-memory for testing)

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd yagta
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Access the API**
   - GraphQL Playground: http://localhost:4000/graphql
   - Health Check: http://localhost:4000/health
   - Database Admin: http://localhost:8080 (Adminer)

### Local Development

1. **Install dependencies**
   ```bash
   yarn install
   ```

2. **Start development server**
   ```bash
   yarn dev
   ```

3. **Build for production**
   ```bash
   yarn build
   yarn start
   ```

## Default Users

The application comes with pre-configured users for testing:

- **Admin User**
  - Email: `admin@test.com`
  - Password: `admin123`
  - Role: `ADMIN`

- **Regular User**
  - Email: `user@test.com`
  - Password: `user123`
  - Role: `USER`

## API Documentation

### Authentication

#### Register User
```graphql
mutation Register($input: RegisterInput!) {
  register(input: $input) {
    token
    user {
      id
      email
      firstName
      lastName
      role
    }
  }
}
```

#### Login
```graphql
mutation Login($input: LoginInput!) {
  login(input: $input) {
    token
    user {
      id
      email
      firstName
      lastName
      role
    }
  }
}
```

### Users

#### Get Current User
```graphql
query Me {
  me {
    id
    email
    firstName
    lastName
    role
    createdAt
  }
}
```

#### Get All Users (Admin only)
```graphql
query Users {
  users {
    id
    email
    firstName
    lastName
    role
    createdAt
  }
}
```

### Vehicles

#### Create Vehicle
```graphql
mutation CreateVehicle($input: CreateVehicleInput!) {
  createVehicle(input: $input) {
    id
    licensePlate
    make
    model
    year
    type
    fuelType
    color
    vin
    ownerId
    createdAt
  }
}
```

#### Get My Vehicles
```graphql
query MyVehicles {
  myVehicles {
    id
    licensePlate
    make
    model
    year
    type
    fuelType
    color
    vin
    owner {
      id
      firstName
      lastName
    }
    revisions {
      id
      type
      status
      description
      scheduledDate
    }
  }
}
```

### Parking Slots

#### Create Parking Slot
```graphql
mutation CreateParkingSlot($input: CreateParkingSlotInput!) {
  createParkingSlot(input: $input) {
    id
    slotNumber
    location
    type
    status
    hourlyRate
    ownerId
    createdAt
  }
}
```

#### Get My Parking Slots
```graphql
query MyParkingSlots {
  myParkingSlots {
    id
    slotNumber
    location
    type
    status
    hourlyRate
    owner {
      id
      firstName
      lastName
    }
    currentVehicle {
      id
      licensePlate
      make
      model
    }
  }
}
```

### Vehicle Revisions

#### Create Vehicle Revision
```graphql
mutation CreateVehicleRevision($input: CreateVehicleRevisionInput!) {
  createVehicleRevision(input: $input) {
    id
    vehicleId
    type
    status
    description
    scheduledDate
    cost
    notes
    vehicle {
      id
      licensePlate
      make
      model
    }
  }
}
```

#### Get Vehicle Revisions
```graphql
query VehicleRevisions($vehicleId: String!) {
  vehicleRevisionsByVehicle(vehicleId: $vehicleId) {
    id
    type
    status
    description
    scheduledDate
    completedDate
    cost
    notes
    vehicle {
      id
      licensePlate
      make
      model
    }
  }
}
```

## Environment Variables

Create a `.env` file based on `env.example`:

```env
# Server Configuration
PORT=4000
NODE_ENV=development

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=24h

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/graphql_testing_db

# Security Configuration
BCRYPT_ROUNDS=12
CORS_ORIGIN=http://localhost:3000

# Logging
LOG_LEVEL=info
```

## Data Models

### User
- `id`: Unique identifier
- `email`: User email (unique)
- `firstName`: User's first name
- `lastName`: User's last name
- `role`: User role (USER/ADMIN)
- `password`: Hashed password (not exposed in GraphQL)
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp

### Vehicle
- `id`: Unique identifier
- `licensePlate`: Vehicle license plate
- `make`: Vehicle manufacturer
- `model`: Vehicle model
- `year`: Manufacturing year
- `type`: Vehicle type (CAR/MOTORCYCLE/TRUCK/VAN)
- `fuelType`: Fuel type (GASOLINE/DIESEL/ELECTRIC/HYBRID)
- `color`: Vehicle color
- `vin`: Vehicle Identification Number
- `ownerId`: Reference to user who owns the vehicle
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp

### ParkingSlot
- `id`: Unique identifier
- `slotNumber`: Parking slot number
- `location`: Parking location
- `type`: Slot type (STANDARD/HANDICAP/ELECTRIC/MOTORCYCLE)
- `status`: Slot status (AVAILABLE/OCCUPIED/RESERVED/MAINTENANCE)
- `hourlyRate`: Hourly parking rate
- `ownerId`: Reference to user who owns the slot
- `currentVehicleId`: Reference to vehicle currently parked (optional)
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp

### VehicleRevision
- `id`: Unique identifier
- `vehicleId`: Reference to the vehicle
- `type`: Revision type (MAINTENANCE/INSPECTION/REPAIR/UPGRADE)
- `status`: Revision status (SCHEDULED/IN_PROGRESS/COMPLETED/CANCELLED)
- `description`: Revision description
- `scheduledDate`: Scheduled date for revision
- `completedDate`: Completion date (optional)
- `cost`: Revision cost (optional)
- `notes`: Additional notes (optional)
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt for secure password storage
- **Input Validation**: Class-validator for input sanitization
- **CORS Protection**: Configurable CORS settings
- **Helmet Security**: Security headers middleware
- **Authorization**: Role-based access control
- **Rate Limiting**: Ready for implementation

## Development

### Project Structure
```
src/
├── config/          # Configuration management
├── middleware/      # Express middleware
├── models/          # GraphQL models and types
│   └── inputs/     # Input types for mutations
├── resolvers/       # GraphQL resolvers
├── utils/           # Utility functions
└── index.ts         # Main application entry point
```

### Available Scripts

- `yarn dev`: Start development server with hot reload
- `yarn build`: Build the application for production
- `yarn start`: Start the production server
- `yarn clean`: Clean build artifacts

### Testing

This application is designed for security testing. It includes:

- Multiple user roles and permissions
- Complex data relationships
- Various input validation scenarios
- Authentication and authorization flows
- CRUD operations on all entities
- GraphQL introspection enabled

## Docker Services

The Docker Compose setup includes:

- **graphql-api**: Main application service
- **postgres**: PostgreSQL database
- **redis**: Redis cache (for future use)
- **adminer**: Database management interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details 