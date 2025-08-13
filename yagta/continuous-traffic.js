const axios = require('axios');

// Get target URL from command line arguments or use default
const BASE_URL = process.argv[2] || 'http://localhost:4000';

console.log(`🎯 Target URL: ${BASE_URL}`);

// Simplified operations for continuous traffic
const OPERATIONS = [
  // Authentication
  {
    name: 'Login User',
    query: `
      mutation Login($input: LoginInput!) {
        login(input: $input) {
          token
          user { id email firstName lastName role }
        }
      }
    `,
    variables: {
      input: { email: 'user@test.com', password: 'user123' }
    }
  },
  {
    name: 'Login Admin',
    query: `
      mutation Login($input: LoginInput!) {
        login(input: $input) {
          token
          user { id email firstName lastName role }
        }
      }
    `,
    variables: {
      input: { email: 'admin@test.com', password: 'admin123' }
    }
  },

  // User queries
  {
    name: 'Get All Users',
    query: `query { users { id email firstName lastName role } }`
  },
  {
    name: 'Get User by ID',
    query: `query User($id: String!) { user(id: $id) { id email firstName lastName role } }`,
    variables: { id: '1' }
  },
  {
    name: 'Get Current User',
    query: `query { me { id email firstName lastName role } }`
  },

  // Vehicle queries
  {
    name: 'Get All Vehicles',
    query: `query { vehicles { id licensePlate make model ownerId } }`
  },
  {
    name: 'Get Vehicle by ID',
    query: `query Vehicle($id: String!) { vehicle(id: $id) { id licensePlate make model ownerId } }`,
    variables: { id: '1' }
  },
  {
    name: 'Get My Vehicles',
    query: `query { myVehicles { id licensePlate make model ownerId } }`
  },

  // Vehicle mutations
  {
    name: 'Create Vehicle',
    query: `
      mutation CreateVehicle($input: CreateVehicleInput!) {
        createVehicle(input: $input) { id licensePlate make model ownerId }
      }
    `,
    variables: {
      input: {
        licensePlate: 'CONT' + Math.floor(Math.random() * 1000),
        make: 'Tesla',
        model: 'Model 3',
        year: 2023,
        type: 'CAR',
        fuelType: 'ELECTRIC',
        color: 'Red',
        vin: 'CONT' + Math.floor(Math.random() * 1000000)
      }
    }
  },

  // Parking slot queries
  {
    name: 'Get All Parking Slots',
    query: `query { parkingSlots { id slotNumber location hourlyRate ownerId } }`
  },
  {
    name: 'Get Parking Slot by ID',
    query: `query ParkingSlot($id: String!) { parkingSlot(id: $id) { id slotNumber location hourlyRate ownerId } }`,
    variables: { id: '1' }
  },
  {
    name: 'Get My Parking Slots',
    query: `query { myParkingSlots { id slotNumber location hourlyRate ownerId } }`
  },

  // Parking slot mutations
  {
    name: 'Create Parking Slot',
    query: `
      mutation CreateParkingSlot($input: CreateParkingSlotInput!) {
        createParkingSlot(input: $input) { id slotNumber location hourlyRate ownerId }
      }
    `,
    variables: {
      input: {
        slotNumber: 'CONT' + Math.floor(Math.random() * 100),
        location: 'Continuous Traffic Lot',
        type: 'STANDARD',
        status: 'AVAILABLE',
        hourlyRate: 5.0 + Math.random() * 5
      }
    }
  },

  // Vehicle revision queries
  {
    name: 'Get All Vehicle Revisions',
    query: `query { vehicleRevisions { id vehicleId type status description } }`
  },
  {
    name: 'Get Vehicle Revision by ID',
    query: `query VehicleRevision($id: String!) { vehicleRevision(id: $id) { id vehicleId type status description } }`,
    variables: { id: '1' }
  },
  {
    name: 'Get Vehicle Revisions by Vehicle',
    query: `query VehicleRevisionsByVehicle($vehicleId: String!) { vehicleRevisionsByVehicle(vehicleId: $vehicleId) { id vehicleId type status description } }`,
    variables: { vehicleId: '1' }
  },

  // Vehicle revision mutations
  {
    name: 'Create Vehicle Revision',
    query: `
      mutation CreateVehicleRevision($input: CreateVehicleRevisionInput!) {
        createVehicleRevision(input: $input) { id vehicleId type status description }
      }
    `,
    variables: {
      input: {
        vehicleId: '1',
        type: 'MAINTENANCE',
        status: 'SCHEDULED',
        description: 'Continuous traffic maintenance',
        scheduledDate: new Date(Date.now() + 86400000).toISOString(),
        cost: 50 + Math.floor(Math.random() * 50)
      }
    }
  }
];

// REST endpoints
const REST_ENDPOINTS = [
  '/',
  '/health',
  '/api/users',
  '/api/vehicles'
];

let tokens = [];

// Get valid tokens
async function getTokens() {
  try {
    const userResponse = await axios.post(`${BASE_URL}/graphql`, {
      query: `
        mutation Login($input: LoginInput!) {
          login(input: $input) { token user { id email } }
        }
      `,
      variables: {
        input: { email: 'user@test.com', password: 'user123' }
      }
    });

    const adminResponse = await axios.post(`${BASE_URL}/graphql`, {
      query: `
        mutation Login($input: LoginInput!) {
          login(input: $input) { token user { id email } }
        }
      `,
      variables: {
        input: { email: 'admin@test.com', password: 'admin123' }
      }
    });

    tokens = [
      { name: 'User', token: userResponse.data.data?.login?.token },
      { name: 'Admin', token: adminResponse.data.data?.login?.token }
    ].filter(t => t.token);

    console.log(`✅ Got ${tokens.length} valid tokens`);
  } catch (error) {
    console.log('❌ Error getting tokens:', error.message);
  }
}

// Make GraphQL request
async function makeGraphQLRequest(operation, token = null) {
  try {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await axios.post(`${BASE_URL}/graphql`, {
      query: operation.query,
      variables: operation.variables || {}
    }, { headers });

    return { success: true, operation: operation.name };
  } catch (error) {
    return { success: false, operation: operation.name, error: error.message };
  }
}

// Make REST request
async function makeRESTRequest(endpoint, token = null) {
  try {
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await axios.get(`${BASE_URL}${endpoint}`, { headers });
    return { success: true, endpoint };
  } catch (error) {
    return { success: false, endpoint, error: error.message };
  }
}

// Generate traffic
async function generateTraffic() {
  console.log(`\n🔄 Generating traffic... (${new Date().toLocaleTimeString()})`);
  
  const results = [];

  // Test GraphQL operations
  for (const operation of OPERATIONS) {
    // Test without token
    const noTokenResult = await makeGraphQLRequest(operation);
    results.push(noTokenResult);
    
    // Test with each token
    for (const tokenInfo of tokens) {
      const withTokenResult = await makeGraphQLRequest(operation, tokenInfo.token);
      results.push(withTokenResult);
    }

    // Small delay
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  // Test REST endpoints
  for (const endpoint of REST_ENDPOINTS) {
    // Test without token
    const noTokenResult = await makeRESTRequest(endpoint);
    results.push(noTokenResult);
    
    // Test with each token
    for (const tokenInfo of tokens) {
      const withTokenResult = await makeRESTRequest(endpoint, tokenInfo.token);
      results.push(withTokenResult);
    }

    // Small delay
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`✅ Success: ${successful}, ❌ Failed: ${failed}, 📊 Total: ${results.length}`);
  
  return results;
}

// Main function
async function startContinuousTraffic() {
  console.log('🚀 Starting Continuous Traffic Generation for API Discovery');
  console.log('='.repeat(60));
  console.log('This script will generate continuous traffic to help API discovery tools');
  console.log('Press Ctrl+C to stop');
  console.log('='.repeat(60));

  // Get initial tokens
  await getTokens();

  let cycle = 1;
  
  // Continuous loop
  while (true) {
    try {
      console.log(`\n🔄 Cycle ${cycle}`);
      await generateTraffic();
      
      // Refresh tokens every 10 cycles
      if (cycle % 10 === 0) {
        console.log('🔄 Refreshing tokens...');
        await getTokens();
      }
      
      cycle++;
      
      // Wait between cycles
      await new Promise(resolve => setTimeout(resolve, 2000));
      
    } catch (error) {
      console.error('❌ Error in traffic generation:', error.message);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Stopping continuous traffic generation...');
  process.exit(0);
});

// Start continuous traffic
startContinuousTraffic().catch(console.error); 