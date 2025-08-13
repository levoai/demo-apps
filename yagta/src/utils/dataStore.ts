import { User, UserRole } from '../models/User';
import { Vehicle, VehicleType, FuelType } from '../models/Vehicle';
import { ParkingSlot, ParkingSlotStatus, ParkingSlotType } from '../models/ParkingSlot';
import { VehicleRevision, RevisionType, RevisionStatus } from '../models/VehicleRevision';
import { hashPassword } from './password';

// In-memory data store for testing
class DataStore {
  private users: Map<string, User> = new Map();
  private vehicles: Map<string, Vehicle> = new Map();
  private parkingSlots: Map<string, ParkingSlot> = new Map();
  private vehicleRevisions: Map<string, VehicleRevision> = new Map();

  constructor() {
    this.initializeData();
  }

  private async initializeData() {
    // Create default admin user
    const adminUser: User = {
      id: '1',
      email: 'admin@test.com',
      firstName: 'Admin',
      lastName: 'User',
      role: UserRole.ADMIN,
      password: await hashPassword('admin123'),
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    // Create default regular user
    const regularUser: User = {
      id: '2',
      email: 'user@test.com',
      firstName: 'Regular',
      lastName: 'User',
      role: UserRole.USER,
      password: await hashPassword('user123'),
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    // Create sample vehicles
    const vehicle1: Vehicle = {
      id: '1',
      licensePlate: 'ABC123',
      make: 'Toyota',
      model: 'Camry',
      year: 2020,
      type: VehicleType.CAR,
      fuelType: FuelType.GASOLINE,
      color: 'Silver',
      vin: '1HGBH41JXMN109186',
      ownerId: '2',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const vehicle2: Vehicle = {
      id: '2',
      licensePlate: 'XYZ789',
      make: 'Honda',
      model: 'Civic',
      year: 2019,
      type: VehicleType.CAR,
      fuelType: FuelType.GASOLINE,
      color: 'Blue',
      vin: '2T1BURHE0JC123456',
      ownerId: '2',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    // Create sample parking slots
    const parkingSlot1: ParkingSlot = {
      id: '1',
      slotNumber: 'A1',
      location: 'Main Parking Lot',
      type: ParkingSlotType.STANDARD,
      status: ParkingSlotStatus.AVAILABLE,
      hourlyRate: 5.0,
      ownerId: '2',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const parkingSlot2: ParkingSlot = {
      id: '2',
      slotNumber: 'B2',
      location: 'Main Parking Lot',
      type: ParkingSlotType.ELECTRIC,
      status: ParkingSlotStatus.OCCUPIED,
      hourlyRate: 7.5,
      ownerId: '2',
      currentVehicleId: '1',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    // Create sample vehicle revisions
    const revision1: VehicleRevision = {
      id: '1',
      vehicleId: '1',
      type: RevisionType.MAINTENANCE,
      status: RevisionStatus.COMPLETED,
      description: 'Oil change and filter replacement',
      scheduledDate: new Date('2024-01-15'),
      completedDate: new Date('2024-01-15'),
      cost: 75.0,
      notes: 'Regular maintenance completed',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const revision2: VehicleRevision = {
      id: '2',
      vehicleId: '1',
      type: RevisionType.INSPECTION,
      status: RevisionStatus.SCHEDULED,
      description: 'Annual safety inspection',
      scheduledDate: new Date('2024-03-20'),
      cost: 50.0,
      notes: 'Scheduled for annual inspection',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    // Add to data store
    this.users.set(adminUser.id, adminUser);
    this.users.set(regularUser.id, regularUser);
    this.vehicles.set(vehicle1.id, vehicle1);
    this.vehicles.set(vehicle2.id, vehicle2);
    this.parkingSlots.set(parkingSlot1.id, parkingSlot1);
    this.parkingSlots.set(parkingSlot2.id, parkingSlot2);
    this.vehicleRevisions.set(revision1.id, revision1);
    this.vehicleRevisions.set(revision2.id, revision2);
  }

  // User methods
  async findUserByEmail(email: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(user => user.email === email);
  }

  async findUserById(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async createUser(user: Omit<User, 'id' | 'createdAt' | 'updatedAt'>): Promise<User> {
    const newUser: User = {
      ...user,
      id: Date.now().toString(),
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.users.set(newUser.id, newUser);
    return newUser;
  }

  async updateUser(id: string, updates: Partial<User>): Promise<User | undefined> {
    const user = this.users.get(id);
    if (!user) return undefined;

    const updatedUser: User = {
      ...user,
      ...updates,
      updatedAt: new Date(),
    };
    this.users.set(id, updatedUser);
    return updatedUser;
  }

  async getAllUsers(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  // Vehicle methods
  async findVehicleById(id: string): Promise<Vehicle | undefined> {
    return this.vehicles.get(id);
  }

  async findVehiclesByOwnerId(ownerId: string): Promise<Vehicle[]> {
    return Array.from(this.vehicles.values()).filter(vehicle => vehicle.ownerId === ownerId);
  }

  async createVehicle(vehicle: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>): Promise<Vehicle> {
    const newVehicle: Vehicle = {
      ...vehicle,
      id: Date.now().toString(),
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.vehicles.set(newVehicle.id, newVehicle);
    return newVehicle;
  }

  async updateVehicle(id: string, updates: Partial<Vehicle>): Promise<Vehicle | undefined> {
    const vehicle = this.vehicles.get(id);
    if (!vehicle) return undefined;

    const updatedVehicle: Vehicle = {
      ...vehicle,
      ...updates,
      updatedAt: new Date(),
    };
    this.vehicles.set(id, updatedVehicle);
    return updatedVehicle;
  }

  async deleteVehicle(id: string): Promise<boolean> {
    return this.vehicles.delete(id);
  }

  async getAllVehicles(): Promise<Vehicle[]> {
    return Array.from(this.vehicles.values());
  }

  // Parking slot methods
  async findParkingSlotById(id: string): Promise<ParkingSlot | undefined> {
    return this.parkingSlots.get(id);
  }

  async findParkingSlotsByOwnerId(ownerId: string): Promise<ParkingSlot[]> {
    return Array.from(this.parkingSlots.values()).filter(slot => slot.ownerId === ownerId);
  }

  async createParkingSlot(slot: Omit<ParkingSlot, 'id' | 'createdAt' | 'updatedAt'>): Promise<ParkingSlot> {
    const newSlot: ParkingSlot = {
      ...slot,
      id: Date.now().toString(),
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.parkingSlots.set(newSlot.id, newSlot);
    return newSlot;
  }

  async updateParkingSlot(id: string, updates: Partial<ParkingSlot>): Promise<ParkingSlot | undefined> {
    const slot = this.parkingSlots.get(id);
    if (!slot) return undefined;

    const updatedSlot: ParkingSlot = {
      ...slot,
      ...updates,
      updatedAt: new Date(),
    };
    this.parkingSlots.set(id, updatedSlot);
    return updatedSlot;
  }

  async deleteParkingSlot(id: string): Promise<boolean> {
    return this.parkingSlots.delete(id);
  }

  async getAllParkingSlots(): Promise<ParkingSlot[]> {
    return Array.from(this.parkingSlots.values());
  }

  // Vehicle revision methods
  async findVehicleRevisionById(id: string): Promise<VehicleRevision | undefined> {
    return this.vehicleRevisions.get(id);
  }

  async findVehicleRevisionsByVehicleId(vehicleId: string): Promise<VehicleRevision[]> {
    return Array.from(this.vehicleRevisions.values()).filter(revision => revision.vehicleId === vehicleId);
  }

  async createVehicleRevision(revision: Omit<VehicleRevision, 'id' | 'createdAt' | 'updatedAt'>): Promise<VehicleRevision> {
    const newRevision: VehicleRevision = {
      ...revision,
      id: Date.now().toString(),
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.vehicleRevisions.set(newRevision.id, newRevision);
    return newRevision;
  }

  async updateVehicleRevision(id: string, updates: Partial<VehicleRevision>): Promise<VehicleRevision | undefined> {
    const revision = this.vehicleRevisions.get(id);
    if (!revision) return undefined;

    const updatedRevision: VehicleRevision = {
      ...revision,
      ...updates,
      updatedAt: new Date(),
    };
    this.vehicleRevisions.set(id, updatedRevision);
    return updatedRevision;
  }

  async deleteVehicleRevision(id: string): Promise<boolean> {
    return this.vehicleRevisions.delete(id);
  }

  async getAllVehicleRevisions(): Promise<VehicleRevision[]> {
    return Array.from(this.vehicleRevisions.values());
  }
}

export const dataStore = new DataStore(); 