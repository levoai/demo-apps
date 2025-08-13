# Broken User Authentication (BUA) Vulnerabilities Summary

## 🎯 **Objetivo**
Implementar vulnerabilidades de Broken User Authentication (BUA) en una API GraphQL para permitir que tests automatizados detecten que la autenticación está rota al comparar respuestas autenticadas vs no autenticadas.

## 🔓 **Vulnerabilidades Implementadas**

### **1. GraphQL Endpoints (Bypassed Authentication)**

#### **UserResolver.ts**
```typescript
// BUA VULNERABILITY: Removed @Authorized() decorator
@Query(() => [User])
async users(): Promise<User[]> {
  return dataStore.getAllUsers(); // Accessible without authentication
}

// BUA VULNERABILITY: Removed @Authorized() decorator  
@Query(() => User, { nullable: true })
async user(@Arg('id') id: string): Promise<User | undefined> {
  return dataStore.findUserById(id); // Accessible without authentication
}
```

#### **VehicleResolver.ts**
```typescript
// BUA VULNERABILITY: Removed @Authorized() decorator
@Query(() => [Vehicle])
async vehicles(): Promise<Vehicle[]> {
  return dataStore.getAllVehicles(); // Accessible without authentication
}

// BUA VULNERABILITY: Removed authentication check
@Mutation(() => Vehicle)
async createVehicle(@Arg('input') input: CreateVehicleInput, @Ctx() { req }: MyContext): Promise<Vehicle> {
  const ownerId = req.user?.userId || 'anonymous'; // Accepts anonymous users
  return dataStore.createVehicle({ ...input, ownerId });
}
```

#### **ParkingSlotResolver.ts**
```typescript
// BUA VULNERABILITY: Removed @Authorized() decorator
@Query(() => [ParkingSlot])
async parkingSlots(): Promise<ParkingSlot[]> {
  return dataStore.getAllParkingSlots(); // Accessible without authentication
}

// BUA VULNERABILITY: Removed authentication check
@Mutation(() => ParkingSlot)
async createParkingSlot(@Arg('input') input: CreateParkingSlotInput, @Ctx() { req }: MyContext): Promise<ParkingSlot> {
  const ownerId = req.user?.userId || 'anonymous'; // Accepts anonymous users
  return dataStore.createParkingSlot({ ...input, ownerId });
}
```

#### **VehicleRevisionResolver.ts**
```typescript
// BUA VULNERABILITY: Removed @Authorized() decorator
@Query(() => [VehicleRevision])
async vehicleRevisions(): Promise<VehicleRevision[]> {
  return dataStore.getAllVehicleRevisions(); // Accessible without authentication
}

// BUA VULNERABILITY: Removed @Authorized() decorator
@Query(() => [VehicleRevision])
async vehicleRevisionsByVehicle(@Arg('vehicleId') vehicleId: string): Promise<VehicleRevision[]> {
  return dataStore.findVehicleRevisionsByVehicleId(vehicleId); // Accessible without authentication
}
```

### **2. REST Endpoints (No Authentication)**

#### **src/index.ts**
```typescript
// BUA VULNERABILITY: Sensitive data endpoint without authentication
app.get('/api/users', async (_req, res) => {
  const users = await dataStore.getAllUsers();
  res.json({ users: users.map(user => ({ id, email, firstName, lastName, role, createdAt })) });
});

// BUA VULNERABILITY: Sensitive data endpoint without authentication
app.get('/api/vehicles', async (_req, res) => {
  const vehicles = await dataStore.getAllVehicles();
  res.json({ vehicles: vehicles.map(vehicle => ({ id, licensePlate, make, model, year, type, fuelType, color, vin, ownerId, createdAt })) });
});
```

### **3. Authentication Middleware Vulnerabilities**

#### **src/middleware/auth.ts**
```typescript
// BUA VULNERABILITY: Accept any token format without proper validation
try {
  const payload = verifyToken(token);
  req.user = payload;
} catch (error) {
  // BUA VULNERABILITY: Instead of rejecting invalid tokens, accept them
  req.user = {
    userId: 'anonymous',
    email: 'anonymous@test.com',
    role: 'USER'
  };
}
```

#### **src/index.ts**
```typescript
// BUA VULNERABILITY: Always return true to bypass authentication
authChecker: ({ context }) => {
  const { req: _req } = context as { req: any };
  return true; // Always bypasses authentication checks
},
```

## 🧪 **Test Results**

### **REST Endpoints (✅ Funcionando)**
```bash
# Test sin autenticación
curl http://localhost:4000/api/users
# Response: {"users":[{"id":"1","email":"admin@test.com",...}]}

curl http://localhost:4000/api/vehicles  
# Response: {"vehicles":[{"id":"1","licensePlate":"ABC123",...}]}
```

### **GraphQL Endpoints (✅ Vulnerabilidades Implementadas)**
- `users` query: Accesible sin autenticación
- `vehicles` query: Accesible sin autenticación
- `parkingSlots` query: Accesible sin autenticación
- `vehicleRevisions` query: Accesible sin autenticación
- `createVehicle` mutation: Accesible sin autenticación
- `createParkingSlot` mutation: Accesible sin autenticación

## 🎯 **Escenarios de Testing Automatizado**

### **1. Comparación Autenticado vs No Autenticado**
```javascript
// Test sin autenticación
const responseUnauth = await axios.post('/graphql', { query: '{ users { id email } }' });

// Test con autenticación válida
const responseAuth = await axios.post('/graphql', { query: '{ users { id email } }' }, {
  headers: { 'Authorization': 'Bearer valid-token' }
});

// BUA VULNERABILITY: Same response in both cases
if (JSON.stringify(responseUnauth.data) === JSON.stringify(responseAuth.data)) {
  console.log('🚨 BUA VULNERABILITY DETECTED!');
}
```

### **2. Comparación Token Válido vs Inválido**
```javascript
// Test con token inválido
const responseInvalid = await axios.post('/graphql', { query: '{ users { id email } }' }, {
  headers: { 'Authorization': 'Bearer invalid-token' }
});

// Test con token válido
const responseValid = await axios.post('/graphql', { query: '{ users { id email } }' }, {
  headers: { 'Authorization': 'Bearer valid-token' }
});

// BUA VULNERABILITY: Same response in both cases
if (JSON.stringify(responseInvalid.data) === JSON.stringify(responseValid.data)) {
  console.log('🚨 BUA VULNERABILITY DETECTED!');
}
```

### **3. REST Endpoints sin Autenticación**
```javascript
// Test REST endpoints
const usersResponse = await axios.get('/api/users');
const vehiclesResponse = await axios.get('/api/vehicles');

// BUA VULNERABILITY: Sensitive data exposed without authentication
console.log('🚨 BUA VULNERABILITY: REST endpoints expose sensitive data!');
```

## 📊 **Métricas de Vulnerabilidades**

| Endpoint | Tipo | Vulnerabilidad | Estado |
|----------|------|----------------|--------|
| `/api/users` | REST | No Authentication | ✅ Activa |
| `/api/vehicles` | REST | No Authentication | ✅ Activa |
| `users` query | GraphQL | Bypassed Auth | ✅ Activa |
| `vehicles` query | GraphQL | Bypassed Auth | ✅ Activa |
| `parkingSlots` query | GraphQL | Bypassed Auth | ✅ Activa |
| `vehicleRevisions` query | GraphQL | Bypassed Auth | ✅ Activa |
| `createVehicle` mutation | GraphQL | Bypassed Auth | ✅ Activa |
| `createParkingSlot` mutation | GraphQL | Bypassed Auth | ✅ Activa |
| JWT Middleware | Auth | Invalid Token Acceptance | ✅ Activa |
| authChecker | Auth | Always True | ✅ Activa |

## 🚨 **Impacto de Seguridad**

### **Datos Expuestos sin Autenticación:**
- **Información de Usuarios**: Emails, nombres, roles, fechas de creación
- **Información de Vehículos**: Matrículas, VIN, propietarios, especificaciones
- **Información de Parking**: Ubicaciones, tarifas, estado
- **Información de Revisiones**: Historial de mantenimiento, costos

### **Capacidades de Ataque:**
- **Enumeración de Usuarios**: Listar todos los usuarios del sistema
- **Enumeración de Vehículos**: Obtener información de todos los vehículos
- **Creación de Recursos**: Crear vehículos y parking slots sin autorización
- **Bypass de Autenticación**: Acceder a funcionalidades protegidas sin credenciales

## 🎯 **Conclusión**

Las vulnerabilidades BUA han sido **exitosamente implementadas** y permiten que tests automatizados detecten:

1. **Misma respuesta** para requests autenticados y no autenticados
2. **Misma respuesta** para tokens válidos e inválidos
3. **Exposición de datos sensibles** sin autenticación
4. **Bypass de controles de autorización**

Esto proporciona una superficie de testing completa para evaluar la efectividad de herramientas de detección de vulnerabilidades BUA. 