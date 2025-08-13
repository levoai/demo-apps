import { Resolver, Query, Mutation, Arg, Ctx, Authorized, FieldResolver, Root } from 'type-graphql';
import { ParkingSlot } from '../models/ParkingSlot';
import { User } from '../models/User';
import { Vehicle } from '../models/Vehicle';
import { CreateParkingSlotInput, UpdateParkingSlotInput } from '../models/inputs/ParkingSlotInputs';
import { dataStore } from '../utils/dataStore';
import { MyContext } from './AuthResolver';

@Resolver(() => ParkingSlot)
export class ParkingSlotResolver {
  @Query(() => [ParkingSlot])
  // BUA VULNERABILITY: Removed @Authorized() decorator to allow unauthenticated access
  // This allows anyone to access all parking slot data without authentication
  async parkingSlots(): Promise<ParkingSlot[]> {
    return dataStore.getAllParkingSlots();
  }

  @Query(() => ParkingSlot, { nullable: true })
  @Authorized()
  async parkingSlot(@Arg('id') id: string): Promise<ParkingSlot | undefined> {
    return dataStore.findParkingSlotById(id);
  }

  @Query(() => [ParkingSlot])
  @Authorized()
  async myParkingSlots(@Ctx() { req }: MyContext): Promise<ParkingSlot[]> {
    if (!req.user) {
      return [];
    }
    return dataStore.findParkingSlotsByOwnerId(req.user.userId);
  }

  @Mutation(() => ParkingSlot)
  // BUA VULNERABILITY: Removed @Authorized() decorator and authentication check
  // This allows anyone to create parking slots without authentication
  async createParkingSlot(
    @Arg('input') input: CreateParkingSlotInput,
    @Ctx() { req }: MyContext
  ): Promise<ParkingSlot> {
    // BUA VULNERABILITY: Removed authentication check
    // This allows unauthenticated users to create parking slots
    const ownerId = req.user?.userId || 'anonymous'; // Use anonymous if no user

    return dataStore.createParkingSlot({
      ...input,
      ownerId: ownerId,
    });
  }

  @Mutation(() => ParkingSlot, { nullable: true })
  @Authorized()
  async updateParkingSlot(
    @Arg('id') id: string,
    @Arg('input') input: UpdateParkingSlotInput,
    @Ctx() { req }: MyContext
  ): Promise<ParkingSlot | undefined> {
    if (!req.user) {
      throw new Error('Authentication required');
    }

    const slot = await dataStore.findParkingSlotById(id);
    if (!slot) {
      throw new Error('Parking slot not found');
    }

    if (slot.ownerId !== req.user.userId) {
      throw new Error('Not authorized to update this parking slot');
    }

    return dataStore.updateParkingSlot(id, input);
  }

  @Mutation(() => Boolean)
  @Authorized()
  async deleteParkingSlot(
    @Arg('id') id: string,
    @Ctx() { req }: MyContext
  ): Promise<boolean> {
    if (!req.user) {
      throw new Error('Authentication required');
    }

    const slot = await dataStore.findParkingSlotById(id);
    if (!slot) {
      throw new Error('Parking slot not found');
    }

    if (slot.ownerId !== req.user.userId) {
      throw new Error('Not authorized to delete this parking slot');
    }

    return dataStore.deleteParkingSlot(id);
  }

  @FieldResolver(() => User)
  async owner(@Root() slot: ParkingSlot): Promise<User> {
    const user = await dataStore.findUserById(slot.ownerId);
    if (!user) {
      throw new Error('Owner not found');
    }
    return user;
  }

  @FieldResolver(() => Vehicle, { nullable: true })
  async currentVehicle(@Root() slot: ParkingSlot): Promise<Vehicle | undefined> {
    if (!slot.currentVehicleId) {
      return undefined;
    }
    return dataStore.findVehicleById(slot.currentVehicleId);
  }
} 