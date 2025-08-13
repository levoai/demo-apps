#!/bin/bash

# Get target URL from command line arguments or use default
BASE_URL="${1:-http://localhost:4000}"

echo "🎯 Target URL: $BASE_URL"

echo "🚀 Quick API Test Script"
echo "========================"

# Get tokens
echo "🔐 Getting authentication tokens..."

USER_TOKEN=$(curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation Login($input: LoginInput!) { login(input: $input) { token } }",
    "variables": { "input": { "email": "user@test.com", "password": "user123" } }
  }' | jq -r '.data.login.token')

ADMIN_TOKEN=$(curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation Login($input: LoginInput!) { login(input: $input) { token } }",
    "variables": { "input": { "email": "admin@test.com", "password": "admin123" } }
  }' | jq -r '.data.login.token')

echo "✅ User token: ${USER_TOKEN:0:20}..."
echo "✅ Admin token: ${ADMIN_TOKEN:0:20}..."

# Test REST endpoints
echo ""
echo "📊 Testing REST Endpoints..."
echo "============================"

echo "🔍 Testing / (root)"
curl -s $BASE_URL/ | head -c 100

echo ""
echo "🔍 Testing /health"
curl -s $BASE_URL/health

echo ""
echo "🔍 Testing /api/users (no auth)"
curl -s $BASE_URL/api/users | jq '.users | length'

echo ""
echo "🔍 Testing /api/users (with user token)"
curl -s -H "Authorization: Bearer $USER_TOKEN" $BASE_URL/api/users | jq '.users | length'

echo ""
echo "🔍 Testing /api/vehicles (no auth)"
curl -s $BASE_URL/api/vehicles | jq '.vehicles | length'

echo ""
echo "🔍 Testing /api/vehicles (with admin token)"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" $BASE_URL/api/vehicles | jq '.vehicles | length'

# Test GraphQL queries
echo ""
echo "📊 Testing GraphQL Queries..."
echo "============================="

echo "🔍 Testing users query (no auth)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { id email firstName lastName role } }"}' | jq '.data.users | length'

echo ""
echo "🔍 Testing users query (with user token)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"query": "{ users { id email firstName lastName role } }"}' | jq '.data.users | length'

echo ""
echo "🔍 Testing vehicles query (no auth)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ vehicles { id licensePlate make model ownerId } }"}' | jq '.data.vehicles | length'

echo ""
echo "🔍 Testing vehicles query (with admin token)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"query": "{ vehicles { id licensePlate make model ownerId } }"}' | jq '.data.vehicles | length'

echo ""
echo "🔍 Testing parkingSlots query (no auth)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ parkingSlots { id slotNumber location hourlyRate ownerId } }"}' | jq '.data.parkingSlots | length'

echo ""
echo "🔍 Testing parkingSlots query (with user token)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"query": "{ parkingSlots { id slotNumber location hourlyRate ownerId } }"}' | jq '.data.parkingSlots | length'

# Test GraphQL mutations
echo ""
echo "📊 Testing GraphQL Mutations..."
echo "==============================="

echo "🔍 Testing createVehicle mutation (no auth)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation CreateVehicle($input: CreateVehicleInput!) { createVehicle(input: $input) { id licensePlate make model } }",
    "variables": {
      "input": {
        "licensePlate": "TEST123",
        "make": "Tesla",
        "model": "Model 3",
        "year": 2023,
        "type": "CAR",
        "fuelType": "ELECTRIC",
        "color": "Red",
        "vin": "TEST123456789"
      }
    }
  }' | jq '.data.createVehicle.id'

echo ""
echo "🔍 Testing createVehicle mutation (with user token)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{
    "query": "mutation CreateVehicle($input: CreateVehicleInput!) { createVehicle(input: $input) { id licensePlate make model } }",
    "variables": {
      "input": {
        "licensePlate": "AUTH123",
        "make": "BMW",
        "model": "X5",
        "year": 2022,
        "type": "CAR",
        "fuelType": "GASOLINE",
        "color": "Blue",
        "vin": "AUTH123456789"
      }
    }
  }' | jq '.data.createVehicle.id'

echo ""
echo "🔍 Testing createParkingSlot mutation (no auth)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation CreateParkingSlot($input: CreateParkingSlotInput!) { createParkingSlot(input: $input) { id slotNumber location hourlyRate } }",
    "variables": {
      "input": {
        "slotNumber": "TEST-A1",
        "location": "Test Parking Lot",
        "type": "STANDARD",
        "status": "AVAILABLE",
        "hourlyRate": 5.0
      }
    }
  }' | jq '.data.createParkingSlot.id'

echo ""
echo "🔍 Testing createParkingSlot mutation (with admin token)"
curl -s -X POST $BASE_URL/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "query": "mutation CreateParkingSlot($input: CreateParkingSlotInput!) { createParkingSlot(input: $input) { id slotNumber location hourlyRate } }",
    "variables": {
      "input": {
        "slotNumber": "AUTH-B1",
        "location": "Auth Parking Lot",
        "type": "PREMIUM",
        "status": "AVAILABLE",
        "hourlyRate": 10.0
      }
    }
  }' | jq '.data.createParkingSlot.id'

echo ""
echo "✅ Quick test completed!"
echo "📊 Summary: All endpoints tested with and without authentication"
echo "🎯 Ready for API discovery tools!" 