import { Task } from './task';

export type MeetingStatus =
  | 'draft'
  | 'uploaded'
  | 'queued'
  | 'processing'
  | 'awaiting_review'
  | 'revision_requested'
  | 'awaiting_email_review'
  | 'completed'
  | 'rejected'
  | 'failed'
  | 'cancelled';

export interface Attendee {
  id?: number;
  meeting_id?: string;
  name: string;
  email: string;
  created_at?: string;
}

export interface MeetingListItem {
  id: string;
  title: string;
  meeting_date: string;
  meeting_time?: string | null;
  project_name?: string | null;
  team_id: string;
  project_id?: string | null;
  created_by: number;
  status: MeetingStatus;
  created_at: string;
  updated_at: string;
}

export interface Meeting {
  id: string;
  user_id: number;
  team_id: string;
  project_id?: string | null;
  created_by: number;
  title: string;
  meeting_date: string;
  meeting_time?: string | null;
  project_name?: string | null;
  agenda: string[];
  notes?: string | null;
  attendees: Attendee[];
  status: MeetingStatus;
  audio_file_path?: string | null;
  transcript_file_path?: string | null;
  transcript_text?: string | null;
  raw_transcription?: string | null;
  cleaned_transcription?: string | null;
  summary?: string | null;
  decisions: string[];
  action_items: string[];
  redacted_transcription?: string | null;
  redacted_summary?: string | null;
  redacted_decisions: string[];
  redacted_action_items: string[];
  email_draft?: string | null;
  email_sent: boolean;
  email_response?: Record<string, unknown> | null;
  tokens_used: number;
  thread_id?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MeetingCreateRequest {
  title: string;
  meeting_date?: string;
  meeting_time?: string | null;
  project_name?: string | null;
  team_id?: string;
  project_id?: string | null;
  agenda?: string[];
  notes?: string | null;
  attendees: Array<{ name: string; email: string }>;
  transcript_text?: string | null;
  audio_file_path?: string | null;
  transcript_file_path?: string | null;
}

export interface MeetingUpdateRequest {
  title?: string;
  meeting_date?: string;
  meeting_time?: string | null;
  project_name?: string | null;
  project_id?: string | null;
  agenda?: string[];
  notes?: string | null;
  attendees?: Array<{ name: string; email: string }>;
}

export interface MeetingStatusResponse {
  meeting_id: string;
  status: MeetingStatus;
  current_stage?: string | null;
  error?: string | null;
  progress_percentage?: number | null;
}

export interface MeetingResultResponse {
  meeting_id: string;
  title: string;
  meeting_date: string;
  summary?: string | null;
  decisions: string[];
  action_items: string[];
  redacted_summary?: string | null;
  redacted_decisions: string[];
  redacted_action_items: string[];
  email_draft?: string | null;
  email_sent: boolean;
  tasks: Task[];
  status: MeetingStatus;
  tokens_used: number;
}

export interface ReviewContentResponse {
  meeting_id: string;
  meeting_title: string;
  redacted_transcription: string;
  redacted_summary: string;
  redacted_decisions: string[];
  redacted_action_items: string[];
}

export interface ReviewRequest {
  decision: 'approve' | 'reject' | 'revise';
  instructions?: string | null;
}

export interface ReviewResponse {
  meeting_id: string;
  decision: string;
  message: string;
  next_status: string;
}

export interface EmailDraftResponse {
  meeting_id: string;
  meeting_title: string;
  email_draft: string;
  redacted_summary: string;
  redacted_decisions: string[];
  redacted_action_items: string[];
  delivery_error?: string | null;
}

export interface EmailReviewRequest {
  decision: 'approve' | 'reject' | 'revise';
  instructions?: string | null;
}

export interface EmailSendResponse {
  meeting_id: string;
  sent: boolean;
  response?: Record<string, unknown> | null;
  message: string;
}
