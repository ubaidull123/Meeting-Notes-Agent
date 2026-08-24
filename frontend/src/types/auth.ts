import { PlatformRole, UserRole } from './user';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number;
}

export interface AuthState {
  user: {
    id: number;
    email: string;
    full_name: string;
    role: UserRole;
    platform_role: PlatformRole;
    is_active: boolean;
  } | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
}

export interface DecodedToken {
  user_id: number;
  email: string;
  role: UserRole;
  exp: number;
  type: string;
}
