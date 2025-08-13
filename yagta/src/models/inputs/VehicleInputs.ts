import { InputType, Field } from 'type-graphql';
import { IsNotEmpty, IsNumber, Min, Max, IsEnum } from 'class-validator';
import { VehicleType, FuelType } from '../Vehicle';

@InputType()
export class CreateVehicleInput {
  @Field()
  @IsNotEmpty()
  licensePlate!: string;

  @Field()
  @IsNotEmpty()
  make!: string;

  @Field()
  @IsNotEmpty()
  model!: string;

  @Field()
  @IsNumber()
  @Min(1900)
  @Max(new Date().getFullYear() + 1)
  year!: number;

  @Field(() => VehicleType)
  @IsEnum(VehicleType)
  type!: VehicleType;

  @Field(() => FuelType)
  @IsEnum(FuelType)
  fuelType!: FuelType;

  @Field()
  @IsNotEmpty()
  color!: string;

  @Field()
  @IsNotEmpty()
  vin!: string;
}

@InputType()
export class UpdateVehicleInput {
  @Field({ nullable: true })
  licensePlate?: string;

  @Field({ nullable: true })
  make?: string;

  @Field({ nullable: true })
  model?: string;

  @Field({ nullable: true })
  @IsNumber()
  @Min(1900)
  @Max(new Date().getFullYear() + 1)
  year?: number;

  @Field(() => VehicleType, { nullable: true })
  @IsEnum(VehicleType)
  type?: VehicleType;

  @Field(() => FuelType, { nullable: true })
  @IsEnum(FuelType)
  fuelType?: FuelType;

  @Field({ nullable: true })
  color?: string;

  @Field({ nullable: true })
  vin?: string;
} 