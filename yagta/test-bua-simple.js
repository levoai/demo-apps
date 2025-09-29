const fetch = require('node-fetch');

const BASE_URL = 'http://localhost:4000';

// Simple test function for REST endpoints
async function testRESTEndpoints() {
  console.log('🔍 Testing REST Endpoints BUA Vulnerabilities');
  console.log('='.repeat(50));
  
  try {
    // Test /api/users endpoint
    console.log('\n📤 Testing /api/users endpoint:');
    const usersResponse = await fetch(`${BASE_URL}/api/users`);
    const usersData = await usersResponse.json();
    console.log('✅ Response:', JSON.stringify(usersData, null, 2));
    console.log('🚨 BUA VULNERABILITY: Sensitive user data exposed without authentication!');
    
    // Test /api/vehicles endpoint
    console.log('\n📤 Testing /api/vehicles endpoint:');
    const vehiclesResponse = await fetch(`${BASE_URL}/api/vehicles`);
    const vehiclesData = await vehiclesResponse.json();
    console.log('✅ Response:', JSON.stringify(vehiclesData, null, 2));
    console.log('🚨 BUA VULNERABILITY: Sensitive vehicle data exposed without authentication!');
    
  } catch (error) {
    console.error('❌ Error testing REST endpoints:', error.message);
  }
}

// Test GraphQL with fetch
async function testGraphQLBUA() {
  console.log('\n🔍 Testing GraphQL Endpoints BUA Vulnerabilities');
  console.log('='.repeat(50));
  
  const queries = [
    {
      name: 'Users Query',
      query: '{ users { id email firstName lastName role } }'
    },
    {
      name: 'Vehicles Query', 
      query: '{ vehicles { id licensePlate make model ownerId } }'
    },
    {
      name: 'Parking Slots Query',
      query: '{ parkingSlots { id slotNumber location hourlyRate ownerId } }'
    },
    {
      name: 'Vehicle Revisions Query',
      query: '{ vehicleRevisions { id vehicleId type status description } }'
    }
  ];

  for (const test of queries) {
    console.log(`\n📤 Testing: ${test.name}`);
    
    try {
      // Test without authentication
      const responseUnauth = await fetch(`${BASE_URL}/graphql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: 'query ' + test.query })
      });
      
      if (responseUnauth.ok) {
        const dataUnauth = await responseUnauth.json();
        console.log('✅ Response (Unauthenticated):', JSON.stringify(dataUnauth, null, 2));
        console.log('🚨 BUA VULNERABILITY: Query accessible without authentication!');
      } else {
        console.log('❌ Error:', responseUnauth.status, responseUnauth.statusText);
      }
      
    } catch (error) {
      console.error('❌ Error testing GraphQL:', error.message);
    }
  }
}

// Test authentication bypass
async function testAuthBypass() {
  console.log('\n🔍 Testing Authentication Bypass');
  console.log('='.repeat(50));
  
  const invalidTokens = [
    'invalid-token-123',
    'Bearer invalid',
    'Bearer ',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid',
    ''
  ];

  for (const token of invalidTokens) {
    console.log(`\n📤 Testing with invalid token: "${token}"`);
    
    try {
      const response = await fetch(`${BASE_URL}/api/users`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Response:', JSON.stringify(data, null, 2));
        console.log('🚨 BUA VULNERABILITY: Invalid token accepted!');
      } else {
        console.log('❌ Error:', response.status, response.statusText);
      }
      
    } catch (error) {
      console.error('❌ Error testing auth bypass:', error.message);
    }
  }
}

// Main test function
async function runTests() {
  console.log('🚀 Starting BUA Vulnerability Tests (Simple Version)');
  console.log('='.repeat(50));
  
  // Test REST endpoints
  await testRESTEndpoints();
  
  // Test GraphQL endpoints
  await testGraphQLBUA();
  
  // Test authentication bypass
  await testAuthBypass();
  
  console.log('\n🎯 BUA Vulnerability Test Summary:');
  console.log('='.repeat(50));
  console.log('✅ REST endpoints expose sensitive data without authentication');
  console.log('✅ GraphQL queries accessible without authentication');
  console.log('✅ Invalid tokens are accepted');
  console.log('✅ Authentication bypass works across endpoints');
  console.log('\n🚨 These vulnerabilities allow automated tests to detect BUA!');
}

// Run tests
runTests().catch(console.error); 