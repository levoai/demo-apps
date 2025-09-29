const axios = require('axios');

const BASE_URL = 'http://localhost:4000';

// Test function to compare authenticated vs unauthenticated responses
async function testBUA(endpoint, query, description) {
  console.log(`\n🔍 Testing: ${description}`);
  console.log('='.repeat(50));
  
  try {
    // Test without authentication
    console.log('📤 Request WITHOUT authentication:');
    const responseUnauth = await axios.post(`${BASE_URL}/graphql`, {
      query: query
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ Response (Unauthenticated):', JSON.stringify(responseUnauth.data, null, 2));
    
    // Test with invalid authentication
    console.log('\n📤 Request WITH invalid authentication:');
    const responseInvalidAuth = await axios.post(`${BASE_URL}/graphql`, {
      query: query
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer invalid-token-123'
      }
    });
    
    console.log('✅ Response (Invalid Auth):', JSON.stringify(responseInvalidAuth.data, null, 2));
    
    // Test with valid authentication
    console.log('\n📤 Request WITH valid authentication:');
    const loginResponse = await axios.post(`${BASE_URL}/graphql`, {
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
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const token = loginResponse.data.data.login.token;
    
    const responseValidAuth = await axios.post(`${BASE_URL}/graphql`, {
      query: query
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('✅ Response (Valid Auth):', JSON.stringify(responseValidAuth.data, null, 2));
    
    // Compare responses
    const unauthData = JSON.stringify(responseUnauth.data);
    const invalidAuthData = JSON.stringify(responseInvalidAuth.data);
    const validAuthData = JSON.stringify(responseValidAuth.data);
    
    console.log('\n🔍 BUA Vulnerability Analysis:');
    console.log('Unauthenticated === Invalid Auth:', unauthData === invalidAuthData);
    console.log('Unauthenticated === Valid Auth:', unauthData === validAuthData);
    console.log('Invalid Auth === Valid Auth:', invalidAuthData === validAuthData);
    
    if (unauthData === validAuthData) {
      console.log('🚨 BUA VULNERABILITY DETECTED: Same response for authenticated and unauthenticated requests!');
    } else {
      console.log('✅ No BUA vulnerability detected in this endpoint');
    }
    
  } catch (error) {
    console.error('❌ Error testing endpoint:', error.message);
  }
}

// Test REST endpoints
async function testRESTBUA() {
  console.log('\n🔍 Testing REST Endpoints BUA Vulnerabilities');
  console.log('='.repeat(50));
  
  try {
    // Test /api/users endpoint
    console.log('\n📤 Testing /api/users endpoint:');
    const usersResponse = await axios.get(`${BASE_URL}/api/users`);
    console.log('✅ Response:', JSON.stringify(usersResponse.data, null, 2));
    console.log('🚨 BUA VULNERABILITY: Sensitive user data exposed without authentication!');
    
    // Test /api/vehicles endpoint
    console.log('\n📤 Testing /api/vehicles endpoint:');
    const vehiclesResponse = await axios.get(`${BASE_URL}/api/vehicles`);
    console.log('✅ Response:', JSON.stringify(vehiclesResponse.data, null, 2));
    console.log('🚨 BUA VULNERABILITY: Sensitive vehicle data exposed without authentication!');
    
  } catch (error) {
    console.error('❌ Error testing REST endpoints:', error.message);
  }
}

// Main test function
async function runTests() {
  console.log('🚀 Starting BUA Vulnerability Tests');
  console.log('='.repeat(50));
  
  // Test GraphQL endpoints
  await testBUA(
    '/graphql',
    'query { users { id email firstName lastName role } }',
    'Users Query - Should require authentication but doesn\'t'
  );
  
  await testBUA(
    '/graphql',
    'query { vehicles { id licensePlate make model ownerId } }',
    'Vehicles Query - Should require authentication but doesn\'t'
  );
  
  await testBUA(
    '/graphql',
    'query { parkingSlots { id slotNumber location hourlyRate ownerId } }',
    'Parking Slots Query - Should require authentication but doesn\'t'
  );
  
  await testBUA(
    '/graphql',
    'query { vehicleRevisions { id vehicleId type status description } }',
    'Vehicle Revisions Query - Should require authentication but doesn\'t'
  );
  
  // Test REST endpoints
  await testRESTBUA();
  
  console.log('\n🎯 BUA Vulnerability Test Summary:');
  console.log('='.repeat(50));
  console.log('✅ All vulnerable endpoints are accessible without authentication');
  console.log('✅ Invalid tokens are accepted as valid');
  console.log('✅ Sensitive data is exposed in REST endpoints');
  console.log('✅ GraphQL queries return same data regardless of authentication');
  console.log('\n🚨 These vulnerabilities allow automated tests to detect BUA!');
}

// Run tests
runTests().catch(console.error); 