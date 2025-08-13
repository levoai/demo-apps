import 'reflect-metadata';
import express from 'express';
import { ApolloServer } from 'apollo-server-express';
import { buildSchema } from 'type-graphql';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { config } from './config';
import { authMiddleware } from './middleware/auth';
import { dataStore } from './utils/dataStore';

// Import resolvers
import { AuthResolver } from './resolvers/AuthResolver';
import { UserResolver } from './resolvers/UserResolver';
import { VehicleResolver } from './resolvers/VehicleResolver';
import { ParkingSlotResolver } from './resolvers/ParkingSlotResolver';
import { VehicleRevisionResolver } from './resolvers/VehicleRevisionResolver';

// Import models for schema generation
import './models/User';
import './models/Vehicle';
import './models/ParkingSlot';
import './models/VehicleRevision';

async function startServer() {
  // Create Express app
  const app = express();

  // Body parsing middleware - CRITICAL: Must be FIRST, before any other middleware
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Security middleware
  app.use(helmet());
  app.use(cors({
    origin: config.security.corsOrigin,
    credentials: true,
  }));

  // Logging middleware
  app.use(morgan('combined'));

  // Authentication middleware
  app.use(authMiddleware);

  // Build GraphQL schema
  const schema = await buildSchema({
    resolvers: [
      AuthResolver,
      UserResolver,
      VehicleResolver,
      ParkingSlotResolver,
      VehicleRevisionResolver,
    ],
    validate: false, // We'll handle validation manually
    authChecker: ({ context }) => {
      const { req: _req } = context as { req: any };
      // BUA VULNERABILITY: Always return true to bypass authentication
      // This allows any request to pass authentication checks
      return true;
    },
  });

  // Create Apollo Server
  const server = new ApolloServer({
    schema,
    context: ({ req }) => ({ req }),
    introspection: config.server.nodeEnv === 'development',
  });

  // Apply Apollo Server to Express
  await server.start();
  server.applyMiddleware({ 
    app, 
    path: '/graphql',
    bodyParserConfig: false // Disable Apollo's body parser to use Express's
  });

  // Health check endpoint
  app.get('/health', (_req, res) => {
    res.json({ status: 'OK', timestamp: new Date().toISOString() });
  });

  // Root endpoint
  app.get('/', (_req, res) => {
    res.json({
      message: 'GraphQL Testing API',
      version: '1.0.0',
      endpoints: {
        graphql: '/graphql',
        health: '/health',
      },
      documentation: 'Visit /graphql for GraphQL Playground',
    });
  });

  // BUA VULNERABILITY: Sensitive data endpoint without authentication
  // This endpoint exposes sensitive user data without any authentication
  app.get('/api/users', async (_req, res) => {
    try {
      const users = await dataStore.getAllUsers();
      // BUA VULNERABILITY: Expose sensitive user data without authentication
      res.json({
        users: users.map((user: any) => ({
          id: user.id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          role: user.role,
          createdAt: user.createdAt
        }))
      });
    } catch (error) {
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  // BUA VULNERABILITY: Sensitive data endpoint without authentication
  // This endpoint exposes sensitive vehicle data without any authentication
  app.get('/api/vehicles', async (_req, res) => {
    try {
      const vehicles = await dataStore.getAllVehicles();
      // BUA VULNERABILITY: Expose sensitive vehicle data without authentication
      res.json({
        vehicles: vehicles.map((vehicle: any) => ({
          id: vehicle.id,
          licensePlate: vehicle.licensePlate,
          make: vehicle.make,
          model: vehicle.model,
          year: vehicle.year,
          type: vehicle.type,
          fuelType: vehicle.fuelType,
          color: vehicle.color,
          vin: vehicle.vin,
          ownerId: vehicle.ownerId,
          createdAt: vehicle.createdAt
        }))
      });
    } catch (error) {
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  // Start server
  const port = config.server.port;
  app.listen(port, () => {
    console.log(`🚀 Server ready at http://localhost:${port}`);
    console.log(`📊 GraphQL Playground available at http://localhost:${port}/graphql`);
    console.log(`🔐 Default users:`);
    console.log(`   Admin: admin@test.com / admin123`);
    console.log(`   User: user@test.com / user123`);
  });
}

startServer().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
}); 