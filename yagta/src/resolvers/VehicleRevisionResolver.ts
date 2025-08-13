import { Resolver, Query, Mutation, Arg, Ctx, Authorized, FieldResolver, Root } from 'type-graphql';
import { VehicleRevision } from '../models/VehicleRevision';
import { Vehicle } from '../models/Vehicle';
import { CreateVehicleRevisionInput, UpdateVehicleRevisionInput } from '../models/inputs/VehicleRevisionInputs';
import { dataStore } from '../utils/dataStore';
import { MyContext } from './AuthResolver';

@Resolver(() => VehicleRevision)
export class VehicleRevisionResolver {
  @Query(() => [VehicleRevision])
  // BUA VULNERABILITY: Removed @Authorized() decorator to allow unauthenticated access
  // This allows anyone to access all vehicle revision data without authentication
  async vehicleRevisions(): Promise<VehicleRevision[]> {
    return dataStore.getAllVehicleRevisions();
  }

  @Query(() => VehicleRevision, { nullable: true })
  @Authorized()
  async vehicleRevision(@Arg('id') id: string): Promise<VehicleRevision | undefined> {
    return dataStore.findVehicleRevisionById(id);
  }

  @Query(() => [VehicleRevision])
  // BUA VULNERABILITY: Removed @Authorized() decorator to allow unauthenticated access
  // This allows anyone to access vehicle revision data by vehicle ID without authentication
  async vehicleRevisionsByVehicle(@Arg('vehicleId') vehicleId: string): Promise<VehicleRevision[]> {
    return dataStore.findVehicleRevisionsByVehicleId(vehicleId);
  }

  @Mutation(() => VehicleRevision)
  @Authorized()
  async createVehicleRevision(
    @Arg('input') input: CreateVehicleRevisionInput,
    @Ctx() { req }: MyContext
  ): Promise<VehicleRevision> {
    if (!req.user) {
      throw new Error('Authentication required');
    }

    // Verify the vehicle exists and belongs to the user
    const vehicle = await dataStore.findVehicleById(input.vehicleId);
    if (!vehicle) {
      throw new Error('Vehicle not found');
    }

    if (vehicle.ownerId !== req.user.userId) {
      throw new Error('Not authorized to create revisions for this vehicle');
    }

    return dataStore.createVehicleRevision({
      ...input,
      scheduledDate: new Date(input.scheduledDate),
    });
  }

  @Mutation(() => VehicleRevision, { nullable: true })
  @Authorized()
  async updateVehicleRevision(
    @Arg('id') id: string,
    @Arg('input') input: UpdateVehicleRevisionInput,
    @Ctx() { req }: MyContext
  ): Promise<VehicleRevision | undefined> {
    if (!req.user) {
      throw new Error('Authentication required');
    }

    const revision = await dataStore.findVehicleRevisionById(id);
    if (!revision) {
      throw new Error('Vehicle revision not found');
    }

    // Verify the vehicle belongs to the user
    const vehicle = await dataStore.findVehicleById(revision.vehicleId);
    if (!vehicle || vehicle.ownerId !== req.user.userId) {
      throw new Error('Not authorized to update this revision');
    }

    const updates: Partial<VehicleRevision> = {};
    if (input.type !== undefined) updates.type = input.type;
    if (input.status !== undefined) updates.status = input.status;
    if (input.description !== undefined) updates.description = input.description;
    if (input.scheduledDate !== undefined) updates.scheduledDate = new Date(input.scheduledDate);
    if (input.completedDate !== undefined) updates.completedDate = new Date(input.completedDate);
    if (input.cost !== undefined) updates.cost = input.cost;
    if (input.notes !== undefined) updates.notes = input.notes;

    return dataStore.updateVehicleRevision(id, updates);
  }

  @Mutation(() => Boolean)
  @Authorized()
  async deleteVehicleRevision(
    @Arg('id') id: string,
    @Ctx() { req }: MyContext
  ): Promise<boolean> {
    if (!req.user) {
      throw new Error('Authentication required');
    }

    const revision = await dataStore.findVehicleRevisionById(id);
    if (!revision) {
      throw new Error('Vehicle revision not found');
    }

    // Verify the vehicle belongs to the user
    const vehicle = await dataStore.findVehicleById(revision.vehicleId);
    if (!vehicle || vehicle.ownerId !== req.user.userId) {
      throw new Error('Not authorized to delete this revision');
    }

    return dataStore.deleteVehicleRevision(id);
  }

  @FieldResolver(() => Vehicle)
  async vehicle(@Root() revision: VehicleRevision): Promise<Vehicle> {
    const vehicle = await dataStore.findVehicleById(revision.vehicleId);
    if (!vehicle) {
      throw new Error('Vehicle not found');
    }
    return vehicle;
  }
} 