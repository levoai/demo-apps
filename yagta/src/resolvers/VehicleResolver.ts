import { Resolver, Query, Mutation, Arg, Ctx, Authorized, FieldResolver, Root } from 'type-graphql';
import { Vehicle } from '../models/Vehicle';
import { User } from '../models/User';
import { VehicleRevision } from '../models/VehicleRevision';
import { CreateVehicleInput, UpdateVehicleInput } from '../models/inputs/VehicleInputs';
import { dataStore } from '../utils/dataStore';
import { MyContext } from './AuthResolver';

@Resolver(() => Vehicle)
export class VehicleResolver {
  @Query(() => [Vehicle])
  // BUA VULNERABILITY: Removed @Authorized() decorator to allow unauthenticated access
  // This allows anyone to access all vehicle data without authentication
  async vehicles(): Promise<Vehicle[]> {
    return dataStore.getAllVehicles();
  }

  @Query(() => Vehicle, { nullable: true })
  @Authorized()
  async vehicle(@Arg('id') id: string): Promise<Vehicle | undefined> {
    return dataStore.findVehicleById(id);
  }

  @Query(() => [Vehicle])
  @Authorized()
  async myVehicles(@Ctx() { req }: MyContext): Promise<Vehicle[]> {
    if (!req.user) {
      return [];
    }
    return dataStore.findVehiclesByOwnerId(req.user.userId);
  }

  @Mutation(() => Vehicle)
  // BUA VULNERABILITY: Removed @Authorized() decorator and authentication check
  // This allows anyone to create vehicles without authentication
  async createVehicle(
    @Arg('input') input: CreateVehicleInput,
    @Ctx() { req }: MyContext
  ): Promise<Vehicle> {
    // BUA VULNERABILITY: Removed authentication check
    // This allows unauthenticated users to create vehicles
    const ownerId = req.user?.userId || 'anonymous'; // Use anonymous if no user

    return dataStore.createVehicle({
      ...input,
      ownerId: ownerId,
    });
  }

  @Mutation(() => Vehicle, { nullable: true })
  @Authorized()
  async updateVehicle(
    @Arg('id') id: string,
    @Arg('input') input: UpdateVehicleInput,
    @Ctx() { req }: MyContext
  ): Promise<Vehicle | undefined> {
    if (!req.user) {
      throw new Error('Authentication required');
    }

    const vehicle = await dataStore.findVehicleById(id);
    if (!vehicle) {
      throw new Error('Vehicle not found');
    }

    if (vehicle.ownerId !== req.user.userId) {
      throw new Error('Not authorized to update this vehicle');
    }

    return dataStore.updateVehicle(id, input);
  }

  @Mutation(() => Boolean)
  @Authorized()
  async deleteVehicle(
    @Arg('id') id: string,
    @Ctx() { req }: MyContext
  ): Promise<boolean> {
    if (!req.user) {
      throw new Error('Authentication required');
    }

    const vehicle = await dataStore.findVehicleById(id);
    if (!vehicle) {
      throw new Error('Vehicle not found');
    }

    if (vehicle.ownerId !== req.user.userId) {
      throw new Error('Not authorized to delete this vehicle');
    }

    return dataStore.deleteVehicle(id);
  }

  @FieldResolver(() => User)
  async owner(@Root() vehicle: Vehicle): Promise<User> {
    const user = await dataStore.findUserById(vehicle.ownerId);
    if (!user) {
      throw new Error('Owner not found');
    }
    return user;
  }

  @FieldResolver(() => [VehicleRevision])
  async revisions(@Root() vehicle: Vehicle): Promise<VehicleRevision[]> {
    return dataStore.findVehicleRevisionsByVehicleId(vehicle.id);
  }
} 