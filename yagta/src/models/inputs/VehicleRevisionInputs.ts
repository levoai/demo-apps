import { InputType, Field } from 'type-graphql';
import { IsNotEmpty, IsNumber, Min, IsEnum, IsDateString } from 'class-validator';
import { RevisionType, RevisionStatus } from '../VehicleRevision';

@InputType()
export class CreateVehicleRevisionInput {
  @Field()
  @IsNotEmpty()
  vehicleId!: string;

  @Field(() => RevisionType)
  @IsEnum(RevisionType)
  type!: RevisionType;

  @Field(() => RevisionStatus)
  @IsEnum(RevisionStatus)
  status!: RevisionStatus;

  @Field()
  @IsNotEmpty()
  description!: string;

  @Field()
  @IsDateString()
  scheduledDate!: string;

  @Field({ nullable: true })
  @IsNumber()
  @Min(0)
  cost?: number;

  @Field({ nullable: true })
  notes?: string;
}

@InputType()
export class UpdateVehicleRevisionInput {
  @Field(() => RevisionType, { nullable: true })
  @IsEnum(RevisionType)
  type?: RevisionType;

  @Field(() => RevisionStatus, { nullable: true })
  @IsEnum(RevisionStatus)
  status?: RevisionStatus;

  @Field({ nullable: true })
  description?: string;

  @Field({ nullable: true })
  @IsDateString()
  scheduledDate?: string;

  @Field({ nullable: true })
  @IsDateString()
  completedDate?: string;

  @Field({ nullable: true })
  @IsNumber()
  @Min(0)
  cost?: number;

  @Field({ nullable: true })
  notes?: string;
} 