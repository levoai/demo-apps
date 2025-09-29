import { ObjectType, Field, ID, registerEnumType } from 'type-graphql';

export enum ParkingSlotStatus {
  AVAILABLE = 'AVAILABLE',
  OCCUPIED = 'OCCUPIED',
  RESERVED = 'RESERVED',
  MAINTENANCE = 'MAINTENANCE',
}

export enum ParkingSlotType {
  STANDARD = 'STANDARD',
  HANDICAP = 'HANDICAP',
  ELECTRIC = 'ELECTRIC',
  MOTORCYCLE = 'MOTORCYCLE',
}

registerEnumType(ParkingSlotStatus, {
  name: 'ParkingSlotStatus',
  description: 'Parking slot status enumeration',
});

registerEnumType(ParkingSlotType, {
  name: 'ParkingSlotType',
  description: 'Parking slot type enumeration',
});

@ObjectType()
export class ParkingSlot {
  @Field(() => ID)
  id!: string;

  @Field()
  slotNumber!: string;

  @Field()
  location!: string;

  @Field(() => ParkingSlotType)
  type!: ParkingSlotType;

  @Field(() => ParkingSlotStatus)
  status!: ParkingSlotStatus;

  @Field()
  hourlyRate!: number;

  @Field()
  ownerId!: string;

  @Field({ nullable: true })
  currentVehicleId?: string;

  @Field()
  createdAt!: Date;

  @Field()
  updatedAt!: Date;
} 