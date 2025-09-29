import { ObjectType, Field, ID, registerEnumType } from 'type-graphql';

export enum UserRole {
  USER = 'USER',
  ADMIN = 'ADMIN',
}

registerEnumType(UserRole, {
  name: 'UserRole',
  description: 'User role enumeration',
});

@ObjectType()
export class User {
  @Field(() => ID)
  id!: string;

  @Field()
  email!: string;

  @Field()
  firstName!: string;

  @Field()
  lastName!: string;

  @Field(() => UserRole)
  role!: UserRole;

  @Field()
  createdAt!: Date;

  @Field()
  updatedAt!: Date;

  // Password is not exposed in GraphQL
  password!: string;
} 