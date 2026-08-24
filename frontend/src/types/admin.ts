import { UserRole, UserQuota, UserCredits, UserUsage } from './user';
import { MeetingStatus } from './meeting';

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_meetings: number;
  meetings_today: number;
  meetings_this_week: number;
  meetings_this_month: number;
  successful_meetings: number;
  failed_meetings: number;
  processing_meetings: number;
  total_tokens_used: number;
  emails_sent: number;
  total_credits_issued: number;
  total_credits_consumed: number;
}

export interface AdminUserListItem {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  quota_limit: number;
  credits_balance: number;
  meetings_this_month: number;
}

export interface AdminUserDetail {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  quota?: UserQuota | null;
  credits?: UserCredits | null;
  usage?: UserUsage[] | null;
}

export interface AdminUserUpdate {
  full_name?: string | null;
  is_active?: boolean | null;
  role?: UserRole | null;
}

export interface AdminMeetingListItem {
  id: string;
  user_id: number;
  user_email: string;
  user_name: string;
  title: string;
  meeting_date: string;
  status: MeetingStatus;
  tokens_used: number;
  created_at: string;
  updated_at: string;
}

export interface AdminMeetingStatusResponse {
  meeting_id: string;
  user_id: number;
  user_email: string;
  title: string;
  status: MeetingStatus;
  current_stage?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  tokens_used: number;
  created_at: string;
  updated_at: string;
  thread_id?: string | null;
}
