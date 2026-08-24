export type UserRole = 'USER' | 'ADMIN';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserQuota {
  user_id: number;
  monthly_meeting_limit: number;
  monthly_credits: number;
  created_at: string;
  updated_at: string;
}

export interface UserCredits {
  user_id: number;
  balance: number;
  updated_at: string;
}

export interface UserUsage {
  id: string;
  user_id: number;
  month: string; // YYYY-MM-DD
  meetings_processed: number;
  tokens_used: number;
  credits_consumed: number;
  created_at: string;
  updated_at: string;
}

export interface UserProfileResponse {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  quota?: UserQuota | null;
  credits?: UserCredits | null;
  usage?: UserUsage[] | null;
}

export interface UserUpdateSelf {
  full_name?: string;
}
