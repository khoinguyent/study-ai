import { User, AuthResponse } from '../types';

interface TokenData {
  token: string;
  expiresAt: number;
  user?: User;
}

class AuthService {
  private readonly TOKEN_KEY = 'study_ai_token';
  private readonly TOKEN_EXPIRY_KEY = 'study_ai_token_expiry';
  private readonly USER_KEY = 'study_ai_user';

  // Store token with expiration
  setToken(authResponse: AuthResponse): void {
    const expiresAt = Date.now() + (24 * 60 * 60 * 1000); // 24 hours from now
    
    localStorage.setItem(this.TOKEN_KEY, authResponse.access_token);
    localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiresAt.toString());
    
    if (authResponse.user) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(authResponse.user));
    }
  }

  // Get current token
  getToken(): string | null {
    const token = localStorage.getItem(this.TOKEN_KEY);
    const expiresAt = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    
    if (!token || !expiresAt) {
      return null;
    }
    
    // Check if token is expired
    if (Date.now() > parseInt(expiresAt)) {
      this.clearToken();
      return null;
    }
    
    return token;
  }

  // Get current user
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) {
      return null;
    }
    
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  // Clear all auth data
  clearToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  // Update user data
  updateUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  // Get auth headers for API calls
  getAuthHeaders(): HeadersInit {
    const token = this.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }
}

export const authService = new AuthService();
export default authService; 