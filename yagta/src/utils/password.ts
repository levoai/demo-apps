import bcrypt from 'bcryptjs';
import { config } from '../config';

export const hashPassword = async (password: string): Promise<string> => {
  return bcrypt.hash(password, config.security.bcryptRounds);
};

export const comparePassword = async (password: string, hashedPassword: string): Promise<boolean> => {
  return bcrypt.compare(password, hashedPassword);
};

export const validatePassword = (password: string): boolean => {
  // Basic password validation
  return password.length >= 8;
}; 