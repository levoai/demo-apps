import { Request, Response, NextFunction } from 'express';
import { verifyToken, JWTPayload } from '../utils/jwt';
import { dataStore } from '../utils/dataStore';

export interface AuthenticatedRequest extends Request {
  user?: JWTPayload | undefined;
}

export const authMiddleware = async (
  req: AuthenticatedRequest,
  _res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      req.user = undefined;
      return next();
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix
    
    // BUA VULNERABILITY: Accept any token format without proper validation
    // This allows invalid tokens to be accepted as valid
    try {
      const payload = verifyToken(token);
      
      // Verify user still exists in our data store
      const user = await dataStore.findUserById(payload.userId);
      if (!user) {
        req.user = undefined;
        return next();
      }

      req.user = payload;
    } catch (error) {
      // BUA VULNERABILITY: Instead of rejecting invalid tokens, accept them
      // This allows any malformed or invalid token to be treated as valid
      req.user = {
        userId: 'anonymous',
        email: 'anonymous@test.com',
        role: 'USER'
      };
    }
    
    next();
  } catch (error) {
    // BUA VULNERABILITY: Even if there's an error, set a default user
    req.user = {
      userId: 'anonymous',
      email: 'anonymous@test.com',
      role: 'USER'
    };
    next();
  }
};

export const requireAuth = (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): void => {
  if (!req.user) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }
  next();
};

export const requireAdmin = (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): void => {
  if (!req.user) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }

  // For this simple implementation, we'll check if the user is admin
  // In a real app, you'd check the user's role from the database
  if (req.user.email === 'admin@test.com') {
    next();
  } else {
    res.status(403).json({ error: 'Admin access required' });
  }
}; 