import { Resolver, Mutation, Arg, ObjectType, Field } from 'type-graphql';
import { LoginInput, RegisterInput } from '../models/inputs/AuthInputs';
import { User, UserRole } from '../models/User';
import { comparePassword, hashPassword, validatePassword } from '../utils/password';
import { generateToken } from '../utils/jwt';
import { dataStore } from '../utils/dataStore';
import { AuthenticatedRequest } from '../middleware/auth';

@ObjectType()
export class AuthResponse {
  @Field()
  token!: string;

  @Field(() => User)
  user!: User;
}

export interface MyContext {
  req: AuthenticatedRequest;
}

@Resolver()
export class AuthResolver {
  @Mutation(() => AuthResponse)
  async register(@Arg('input') input: RegisterInput): Promise<AuthResponse> {
    // Check if user already exists
    const existingUser = await dataStore.findUserByEmail(input.email);
    if (existingUser) {
      throw new Error('User with this email already exists');
    }

    // Validate password
    if (!validatePassword(input.password)) {
      throw new Error('Password must be at least 8 characters long');
    }

    // Hash password
    const hashedPassword = await hashPassword(input.password);

    // Create user
    const user = await dataStore.createUser({
      email: input.email,
      firstName: input.firstName,
      lastName: input.lastName,
      password: hashedPassword,
      role: UserRole.USER,
    });

    // Generate token
    const token = generateToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    return { token, user };
  }

  @Mutation(() => AuthResponse)
  async login(@Arg('input') input: LoginInput): Promise<AuthResponse> {
    // Find user by email
    const user = await dataStore.findUserByEmail(input.email);
    if (!user) {
      throw new Error('Invalid email or password');
    }

    // Verify password
    const isValidPassword = await comparePassword(input.password, user.password);
    if (!isValidPassword) {
      throw new Error('Invalid email or password');
    }

    // Generate token
    const token = generateToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    return { token, user };
  }
} 