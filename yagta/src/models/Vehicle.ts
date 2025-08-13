import { ObjectType, Field, ID, registerEnumType } from 'type-graphql';

export enum VehicleType {
  CAR = 'CAR',
  MOTORCYCLE = 'MOTORCYCLE',
  TRUCK = 'TRUCK',
  VAN = 'VAN',
}

export enum FuelType {
  GASOLINE = 'GASOLINE',
  DIESEL = 'DIESEL',
  ELECTRIC = 'ELECTRIC',
  HYBRID = 'HYBRID',
}

registerEnumType(VehicleType, {
  name: 'VehicleType',
  description: 'Vehicle type enumeration',
});

registerEnumType(FuelType, {
  name: 'FuelType',
  description: 'Fuel type enumeration',
});

@ObjectType()
export class Vehicle {
  @Field(() => ID)
  id!: string;

  @Field()
  licensePlate!: string;

  @Field()
  make!: string;

  @Field()
  model!: string;

  @Field()
  year!: number;

  @Field(() => VehicleType)
  type!: VehicleType;

  @Field(() => FuelType)
  fuelType!: FuelType;

  @Field()
  color!: string;

  @Field()
  vin!: string;

  @Field()
  ownerId!: string;

  @Field()
  createdAt!: Date;

  @Field()
  updatedAt!: Date;
} 