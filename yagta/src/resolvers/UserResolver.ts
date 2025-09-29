import { Resolver, Query, Arg, Ctx, Authorized } from 'type-graphql';
import { User } from '../models/User';
import { dataStore } from '../utils/dataStore';
import { MyContext } from './AuthResolver';

@Resolver(() => User)
export class UserResolver {
  @Query(() => [User])
  // BUA VULNERABILITY: Removed @Authorized() decorator to allow unauthenticated access
  // This allows anyone to access all user data without authentication
  async users(): Promise<User[]> {
    return dataStore.getAllUsers();
  }

  @Query(() => User, { nullable: true })
  // BUA VULNERABILITY: Removed @Authorized() decorator to allow unauthenticated access
  // This allows anyone to access any user's profile by ID without authentication
  async user(@Arg('id') id: string): Promise<User | undefined> {
    return dataStore.findUserById(id);
  }

  @Query(() => User, { nullable: true })
  @Authorized()
  async me(@Ctx() { req }: MyContext): Promise<User | undefined> {
    if (!req.user) {
      return undefined;
    }
    return dataStore.findUserById(req.user.userId);
  }
} 