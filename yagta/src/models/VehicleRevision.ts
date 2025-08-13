import { ObjectType, Field, ID, registerEnumType } from 'type-graphql';

export enum RevisionType {
  MAINTENANCE = 'MAINTENANCE',
  INSPECTION = 'INSPECTION',
  REPAIR = 'REPAIR',
  UPGRADE = 'UPGRADE',
}

export enum RevisionStatus {
  SCHEDULED = 'SCHEDULED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
}

registerEnumType(RevisionType, {
  name: 'RevisionType',
  description: 'Revision type enumeration',
});

registerEnumType(RevisionStatus, {
  name: 'RevisionStatus',
  description: 'Revision status enumeration',
});

@ObjectType()
export class VehicleRevision {
  @Field(() => ID)
  id!: string;

  @Field()
  vehicleId!: string;

  @Field(() => RevisionType)
  type!: RevisionType;

  @Field(() => RevisionStatus)
  status!: RevisionStatus;

  @Field()
  description!: string;

  @Field()
  scheduledDate!: Date;

  @Field({ nullable: true })
  completedDate?: Date;

  @Field({ nullable: true })
  cost?: number;

  @Field({ nullable: true })
  notes?: string;

  @Field()
  createdAt!: Date;

  @Field()
  updatedAt!: Date;
} 