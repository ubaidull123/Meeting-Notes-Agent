import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, LoginPayload, RegisterPayload } from '../api/auth';
import { tokenStorage } from '../api/client';
import { PlatformRole, UserProfileResponse, UserRole } from '../types/user';

interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  platform_role: PlatformRole;
  is_active: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  profile: UserProfileResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
  login: (payload: LoginPayload) => Promise<UserProfileResponse>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const normalizeRole = (role: string): UserRole => role.toUpperCase() as UserRole;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchProfile = useCallback(async (): Promise<UserProfileResponse | null> => {
    try {
      const data = await authApi.getMe();
      const normalizedData = {
        ...data,
        role: normalizeRole(data.role),
      };
      setProfile(normalizedData);
      setUser({
        id: normalizedData.id,
        email: normalizedData.email,
        full_name: normalizedData.full_name,
        role: normalizedData.role,
        platform_role: normalizedData.platform_role,
        is_active: normalizedData.is_active,
      });
      return normalizedData;
    } catch {
      tokenStorage.clearTokens();
      setUser(null);
      setProfile(null);
      return null;
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      const token = tokenStorage.getAccessToken();
      if (token) {
        await fetchProfile();
      }
      setIsLoading(false);
    };

    initAuth();

    // Listen for auth expired event dispatched from Axios interceptor
    const handleAuthExpired = () => {
      setUser(null);
      setProfile(null);
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => window.removeEventListener('auth:expired', handleAuthExpired);
  }, [fetchProfile]);

  const login = async (payload: LoginPayload) => {
    const data = await authApi.login(payload);
    tokenStorage.setTokens(data.access_token, data.refresh_token);
    const profile = await fetchProfile();
    if (!profile) {
      throw new Error('Could not load profile after login.');
    }
    return profile;
  };

  const register = async (payload: RegisterPayload) => {
    await authApi.register(payload);
    // Automatically log in after registration
    await login({ email: payload.email, password: payload.password });
  };

  const logout = async () => {
    await authApi.logout();
    tokenStorage.clearTokens();
    setUser(null);
    setProfile(null);
  };

  const refreshProfile = useCallback(async () => {
    await fetchProfile();
  }, [fetchProfile]);

  const value: AuthContextType = {
    user,
    profile,
    isAuthenticated: !!user,
    isLoading,
    isAdmin: user?.platform_role === 'platform_admin',
    login,
    register,
    logout,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
