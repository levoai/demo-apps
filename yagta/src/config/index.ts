import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

export const config = {
  server: {
    port: process.env["PORT"] || 4000,
    nodeEnv: process.env["NODE_ENV"] || 'development',
  },
  jwt: {
    secret: process.env["JWT_SECRET"] || 'fallback-secret-key',
    expiresIn: process.env["JWT_EXPIRES_IN"] || '24h',
  },
  security: {
    bcryptRounds: parseInt(process.env["BCRYPT_ROUNDS"] || '12'),
    corsOrigin: process.env["CORS_ORIGIN"] || 'http://localhost:3000',
  },
  database: {
    url: process.env["DATABASE_URL"] || 'postgresql://user:password@localhost:5432/graphql_testing_db',
  },
  logging: {
    level: process.env["LOG_LEVEL"] || 'info',
  },
} as const;

export type Config = typeof config; 