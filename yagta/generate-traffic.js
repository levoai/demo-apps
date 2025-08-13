const axios = require('axios');

// Get target URL from command line arguments or use default
const BASE_URL = process.argv[2] || 'http://localhost:4000';

console.log(`🎯 Target URL: ${BASE_URL}`);

// GraphQL queries and mutations to test
const GRAPHQL_OPERATIONS = [
  // Authentication operations
  {
    name: 'Login User',
    query: `
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
    `,
    variables: {
      input: {
        email: 'user@test.com',
        password: 'user123'
      }
    }
  },
  {
    name: 'Login Admin',
    query: `
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
    `,
    variables: {
      input: {
        email: 'admin@test.com',
        password: 'admin123'
      }
    }
  },
  {
    name: 'Register New User',
    query: `
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
    `,
    variables: {
      input: {
        email: 'newuser@test.com',
        password: 'newuser123',
        firstName: 'New',
        lastName: 'User'
      }
    }
  },

  // User queries
  {
    name: 'Get All Users',
    query: `
      query Users {
        users {
          id
          email
          firstName
          lastName
          role
          createdAt
          updatedAt
        }
      }
    `
  },
  {
    name: 'Get User by ID',
    query: `
      query User($id: String!) {
        user(id: $id) {
          id
          email
          firstName
          lastName
          role
          createdAt
          updatedAt
        }
      }
    `,
    variables: {
      id: '1'
    }
  },
  {
    name: 'Get Current User',
    query: `
      query Me {
        me {
          id
          email
          firstName
          lastName
          role
          createdAt
          updatedAt
        }
      }
    `
  },

  // Vehicle queries
  {
    name: 'Get All Vehicles',
    query: `
      query Vehicles {
        vehicles {
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
          updatedAt
          owner {
            id
            firstName
            lastName
            email
          }
          revisions {
            id
            type
            status
            description
            scheduledDate
            completedDate
            cost
          }
        }
      }
    `
  },
  {
    name: 'Get Vehicle by ID',
    query: `
      query Vehicle($id: String!) {
        vehicle(id: $id) {
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
          updatedAt
          owner {
            id
            firstName
            lastName
            email
          }
          revisions {
            id
            type
            status
            description
            scheduledDate
            completedDate
            cost
          }
        }
      }
    `,
    variables: {
      id: '1'
    }
  },
  {
    name: 'Get My Vehicles',
    query: `
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
          ownerId
          createdAt
          updatedAt
          owner {
            id
            firstName
            lastName
            email
          }
          revisions {
            id
            type
            status
            description
            scheduledDate
            completedDate
            cost
          }
        }
      }
    `
  },

  // Vehicle mutations
  {
    name: 'Create Vehicle',
    query: `
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
          updatedAt
        }
      }
    `,
    variables: {
      input: {
        licensePlate: 'TEST123',
        make: 'Tesla',
        model: 'Model 3',
        year: 2023,
        type: 'CAR',
        fuelType: 'ELECTRIC',
        color: 'Red',
        vin: 'TEST123456789'
      }
    }
  },
  {
    name: 'Update Vehicle',
    query: `
      mutation UpdateVehicle($id: String!, $input: UpdateVehicleInput!) {
        updateVehicle(id: $id, input: $input) {
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
          updatedAt
        }
      }
    `,
    variables: {
      id: '1',
      input: {
        color: 'Blue',
        year: 2021
      }
    }
  },
  {
    name: 'Delete Vehicle',
    query: `
      mutation DeleteVehicle($id: String!) {
        deleteVehicle(id: $id)
      }
    `,
    variables: {
      id: '2'
    }
  },

  // Parking slot queries
  {
    name: 'Get All Parking Slots',
    query: `
      query ParkingSlots {
        parkingSlots {
          id
          slotNumber
          location
          type
          status
          hourlyRate
          ownerId
          currentVehicleId
          createdAt
          updatedAt
          owner {
            id
            firstName
            lastName
            email
          }
          currentVehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `
  },
  {
    name: 'Get Parking Slot by ID',
    query: `
      query ParkingSlot($id: String!) {
        parkingSlot(id: $id) {
          id
          slotNumber
          location
          type
          status
          hourlyRate
          ownerId
          currentVehicleId
          createdAt
          updatedAt
          owner {
            id
            firstName
            lastName
            email
          }
          currentVehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `,
    variables: {
      id: '1'
    }
  },
  {
    name: 'Get My Parking Slots',
    query: `
      query MyParkingSlots {
        myParkingSlots {
          id
          slotNumber
          location
          type
          status
          hourlyRate
          ownerId
          currentVehicleId
          createdAt
          updatedAt
          owner {
            id
            firstName
            lastName
            email
          }
          currentVehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `
  },

  // Parking slot mutations
  {
    name: 'Create Parking Slot',
    query: `
      mutation CreateParkingSlot($input: CreateParkingSlotInput!) {
        createParkingSlot(input: $input) {
          id
          slotNumber
          location
          type
          status
          hourlyRate
          ownerId
          currentVehicleId
          createdAt
          updatedAt
        }
      }
    `,
    variables: {
      input: {
        slotNumber: 'C3',
        location: 'Downtown Parking',
        type: 'STANDARD',
        status: 'AVAILABLE',
        hourlyRate: 6.0
      }
    }
  },
  {
    name: 'Update Parking Slot',
    query: `
      mutation UpdateParkingSlot($id: String!, $input: UpdateParkingSlotInput!) {
        updateParkingSlot(id: $id, input: $input) {
          id
          slotNumber
          location
          type
          status
          hourlyRate
          ownerId
          currentVehicleId
          createdAt
          updatedAt
        }
      }
    `,
    variables: {
      id: '1',
      input: {
        status: 'OCCUPIED',
        hourlyRate: 8.0
      }
    }
  },
  {
    name: 'Delete Parking Slot',
    query: `
      mutation DeleteParkingSlot($id: String!) {
        deleteParkingSlot(id: $id)
      }
    `,
    variables: {
      id: '2'
    }
  },

  // Vehicle revision queries
  {
    name: 'Get All Vehicle Revisions',
    query: `
      query VehicleRevisions {
        vehicleRevisions {
          id
          vehicleId
          type
          status
          description
          scheduledDate
          completedDate
          cost
          notes
          createdAt
          updatedAt
          vehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `
  },
  {
    name: 'Get Vehicle Revision by ID',
    query: `
      query VehicleRevision($id: String!) {
        vehicleRevision(id: $id) {
          id
          vehicleId
          type
          status
          description
          scheduledDate
          completedDate
          cost
          notes
          createdAt
          updatedAt
          vehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `,
    variables: {
      id: '1'
    }
  },
  {
    name: 'Get Vehicle Revisions by Vehicle',
    query: `
      query VehicleRevisionsByVehicle($vehicleId: String!) {
        vehicleRevisionsByVehicle(vehicleId: $vehicleId) {
          id
          vehicleId
          type
          status
          description
          scheduledDate
          completedDate
          cost
          notes
          createdAt
          updatedAt
          vehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `,
    variables: {
      vehicleId: '1'
    }
  },

  // Vehicle revision mutations
  {
    name: 'Create Vehicle Revision',
    query: `
      mutation CreateVehicleRevision($input: CreateVehicleRevisionInput!) {
        createVehicleRevision(input: $input) {
          id
          vehicleId
          type
          status
          description
          scheduledDate
          completedDate
          cost
          notes
          createdAt
          updatedAt
          vehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `,
    variables: {
      input: {
        vehicleId: '1',
        type: 'MAINTENANCE',
        status: 'SCHEDULED',
        description: 'Regular oil change and inspection',
        scheduledDate: '2024-02-15T10:00:00Z',
        cost: 85.0,
        notes: 'Include filter replacement'
      }
    }
  },
  {
    name: 'Update Vehicle Revision',
    query: `
      mutation UpdateVehicleRevision($id: String!, $input: UpdateVehicleRevisionInput!) {
        updateVehicleRevision(id: $id, input: $input) {
          id
          vehicleId
          type
          status
          description
          scheduledDate
          completedDate
          cost
          notes
          createdAt
          updatedAt
          vehicle {
            id
            licensePlate
            make
            model
          }
        }
      }
    `,
    variables: {
      id: '1',
      input: {
        status: 'COMPLETED',
        completedDate: '2024-01-15T14:30:00Z',
        cost: 90.0,
        notes: 'Service completed successfully'
      }
    }
  },
  {
    name: 'Delete Vehicle Revision',
    query: `
      mutation DeleteVehicleRevision($id: String!) {
        deleteVehicleRevision(id: $id)
      }
    `,
    variables: {
      id: '2'
    }
  }
];

// REST endpoints to test
const REST_ENDPOINTS = [
  '/',
  '/health',
  '/api/users',
  '/api/vehicles'
];

// Function to get valid tokens
async function getValidTokens() {
  const tokens = [];
  
  try {
    // Get user token
    const userResponse = await axios.post(`${BASE_URL}/graphql`, {
      query: `
        mutation Login($input: LoginInput!) {
          login(input: $input) {
            token
            user {
              id
              email
            }
          }
        }
      `,
      variables: {
        input: {
          email: 'user@test.com',
          password: 'user123'
        }
      }
    });
    
    if (userResponse.data.data?.login?.token) {
      tokens.push({
        name: 'User Token',
        token: userResponse.data.data.login.token,
        user: userResponse.data.data.login.user
      });
    }

    // Get admin token
    const adminResponse = await axios.post(`${BASE_URL}/graphql`, {
      query: `
        mutation Login($input: LoginInput!) {
          login(input: $input) {
            token
            user {
              id
              email
            }
          }
        }
      `,
      variables: {
        input: {
          email: 'admin@test.com',
          password: 'admin123'
        }
      }
    });
    
    if (adminResponse.data.data?.login?.token) {
      tokens.push({
        name: 'Admin Token',
        token: adminResponse.data.data.login.token,
        user: adminResponse.data.data.login.user
      });
    }

  } catch (error) {
    console.error('Error getting tokens:', error.message);
  }

  return tokens;
}

// Function to make GraphQL requests
async function makeGraphQLRequest(operation, token = null) {
  try {
    const headers = {
      'Content-Type': 'application/json'
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await axios.post(`${BASE_URL}/graphql`, {
      query: operation.query,
      variables: operation.variables || {}
    }, { headers });

    return {
      success: true,
      operation: operation.name,
      token: token ? 'Valid Token' : 'No Token',
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      operation: operation.name,
      token: token ? 'Valid Token' : 'No Token',
      error: error.message
    };
  }
}

// Function to make REST requests
async function makeRESTRequest(endpoint, token = null) {
  try {
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await axios.get(`${BASE_URL}${endpoint}`, { headers });
    
    return {
      success: true,
      endpoint,
      token: token ? 'Valid Token' : 'No Token',
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      endpoint,
      token: token ? 'Valid Token' : 'No Token',
      error: error.message
    };
  }
}

// Main traffic generation function
async function generateTraffic() {
  console.log('🚀 Starting Traffic Generation for API Discovery');
  console.log('='.repeat(60));

  // Get valid tokens
  console.log('🔐 Getting valid authentication tokens...');
  const tokens = await getValidTokens();
  
  if (tokens.length === 0) {
    console.log('❌ No valid tokens obtained. Exiting.');
    return;
  }

  console.log(`✅ Obtained ${tokens.length} valid tokens:`);
  tokens.forEach(t => console.log(`   - ${t.name}: ${t.user.email}`));
  console.log();

  // Test GraphQL operations
  console.log('📊 Testing GraphQL Operations...');
  console.log('='.repeat(60));

  const results = [];

  for (const operation of GRAPHQL_OPERATIONS) {
    console.log(`\n🔍 Testing: ${operation.name}`);
    
    // Test without token
    const noTokenResult = await makeGraphQLRequest(operation);
    results.push(noTokenResult);
    
    // Test with each token
    for (const tokenInfo of tokens) {
      const withTokenResult = await makeGraphQLRequest(operation, tokenInfo.token);
      results.push(withTokenResult);
    }

    // Add delay between requests
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Test REST endpoints
  console.log('\n📊 Testing REST Endpoints...');
  console.log('='.repeat(60));

  for (const endpoint of REST_ENDPOINTS) {
    console.log(`\n🔍 Testing: ${endpoint}`);
    
    // Test without token
    const noTokenResult = await makeRESTRequest(endpoint);
    results.push(noTokenResult);
    
    // Test with each token
    for (const tokenInfo of tokens) {
      const withTokenResult = await makeRESTRequest(endpoint, tokenInfo.token);
      results.push(withTokenResult);
    }

    // Add delay between requests
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Print summary
  console.log('\n📈 Traffic Generation Summary');
  console.log('='.repeat(60));
  
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`✅ Successful requests: ${successful}`);
  console.log(`❌ Failed requests: ${failed}`);
  console.log(`📊 Total requests: ${results.length}`);
  
  console.log('\n🔍 GraphQL Operations Tested:');
  const graphqlOps = [...new Set(results.filter(r => r.operation).map(r => r.operation))];
  graphqlOps.forEach(op => console.log(`   - ${op}`));
  
  console.log('\n🔍 REST Endpoints Tested:');
  const restEndpoints = [...new Set(results.filter(r => r.endpoint).map(r => r.endpoint))];
  restEndpoints.forEach(endpoint => console.log(`   - ${endpoint}`));
  
  console.log('\n🎯 API Discovery Ready!');
  console.log('All GraphQL operations and REST endpoints have been tested with valid authentication.');
  console.log('This traffic will help API discovery tools identify all available endpoints.');
}

// Run traffic generation
generateTraffic().catch(console.error); 