import { InputType, Field } from 'type-graphql';
import { IsNotEmpty, IsNumber, Min, IsEnum } from 'class-validator';
import { ParkingSlotType, ParkingSlotStatus } from '../ParkingSlot';

@InputType()
export class CreateParkingSlotInput {
  @Field()
  @IsNotEmpty()
  slotNumber!: string;

  @Field()
  @IsNotEmpty()
  location!: string;

  @Field(() => ParkingSlotType)
  @IsEnum(ParkingSlotType)
  type!: ParkingSlotType;

  @Field(() => ParkingSlotStatus)
  @IsEnum(ParkingSlotStatus)
  status!: ParkingSlotStatus;

  @Field()
  @IsNumber()
  @Min(0)
  hourlyRate!: number;
}

@InputType()
export class UpdateParkingSlotInput {
  @Field({ nullable: true })
  slotNumber?: string;

  @Field({ nullable: true })
  location?: string;

  @Field(() => ParkingSlotType, { nullable: true })
  @IsEnum(ParkingSlotType)
  type?: ParkingSlotType;

  @Field(() => ParkingSlotStatus, { nullable: true })
  @IsEnum(ParkingSlotStatus)
  status?: ParkingSlotStatus;

  @Field({ nullable: true })
  @IsNumber()
  @Min(0)
  hourlyRate?: number;

  @Field({ nullable: true })
  currentVehicleId?: string;
} 