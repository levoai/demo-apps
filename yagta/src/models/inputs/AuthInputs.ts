import { InputType, Field } from 'type-graphql';
import { IsEmail, MinLength, IsNotEmpty } from 'class-validator';

@InputType()
export class RegisterInput {
  @Field()
  @IsEmail()
  email!: string;

  @Field()
  @MinLength(8)
  password!: string;

  @Field()
  @IsNotEmpty()
  firstName!: string;

  @Field()
  @IsNotEmpty()
  lastName!: string;
}

@InputType()
export class LoginInput {
  @Field()
  @IsEmail()
  email!: string;

  @Field()
  @IsNotEmpty()
  password!: string;
} 