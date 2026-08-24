export type UsageMode = 'app_credits' | 'byok';

export interface ProfileSettings {
  display_name: string;
  email: string;
  timezone: string;
  language: 'en' | 'ur';
  date_format: 'yyyy-mm-dd' | 'dd-mm-yyyy' | 'mm-dd-yyyy';
  time_format: '12h' | '24h';
  organization?: string | null;
  job_title?: string | null;
}

export interface ProviderModel {
  id: string;
  name: string;
  tier: string;
  speed: string;
  quality: string;
  recommended_for: string;
}

export interface ProviderCatalogItem {
  name: string;
  enabled: boolean;
  capabilities: string[];
  models: {
    chat?: ProviderModel[];
    transcription?: ProviderModel[];
  };
}

export type ProviderCatalog = Record<string, ProviderCatalogItem>;

export interface CredentialPublic {
  provider: string;
  has_api_key: boolean;
  api_key_hint?: string | null;
  is_valid: boolean;
  last_tested_at?: string | null;
  last_test_error?: string | null;
  configuration: Record<string, string>;
}

export interface AISettings {
  llm_usage_mode: UsageMode;
  llm_provider: string;
  llm_model: string;
  transcription_usage_mode: UsageMode;
  transcription_provider: string;
  transcription_model: string;
  temperature: number;
  max_output_tokens: number;
  response_language: string;
  credentials: CredentialPublic[];
}

export interface TranscriptionSettings {
  usage_mode: UsageMode;
  provider: string;
  model: string;
  language: string;
  credentials: CredentialPublic[];
}

export type SummaryStyle = 'short' | 'standard' | 'detailed' | 'executive' | 'technical' | 'custom';
export type SummarySection = 'main_topics' | 'decisions' | 'risks' | 'questions' | 'action_items' | 'deadlines' | 'follow_up_recommendations';

export interface MeetingDefaults {
  default_meeting_type: 'general' | 'planning' | 'standup' | 'interview' | 'client';
  generate_summary: boolean;
  generate_action_items: boolean;
  generate_decisions: boolean;
  generate_insights: boolean;
  generate_follow_up_email: boolean;
  require_human_review: boolean;
  require_email_approval: boolean;
  redact_sensitive_information: boolean;
  summary_style: SummaryStyle;
  summary_sections: SummarySection[];
  custom_instructions?: string | null;
}

export interface EmailSettings {
  email_mode: UsageMode;
  provider: string;
  sender_name?: string | null;
  sender_email?: string | null;
  reply_to_email?: string | null;
  sending_domain?: string | null;
  domain_status?: string | null;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_username?: string | null;
  smtp_use_tls: boolean;
}

export interface NotificationSettings {
  processing_finished: boolean;
  processing_failed: boolean;
  review_required: boolean;
  email_approval_required: boolean;
  credits_low: boolean;
  delivery_available: boolean;
}

export interface PrivacySettings {
  recording_retention: 'never' | '24_hours' | '7_days' | '30_days';
  keep_transcript: boolean;
  automatic_cleanup_available: boolean;
}

export interface UsageSummary {
  balance: number;
  meetings_processed: number;
  tokens_used: number;
  credits_consumed: number;
  llm_requests: number;
  llm_credits: number;
  transcription_requests: number;
  transcription_credits: number;
}

export interface CreditTransaction {
  id: string;
  meeting_id?: string | null;
  amount: number;
  balance_after: number;
  transaction_type: string;
  service_type?: string | null;
  provider?: string | null;
  model?: string | null;
  usage_mode?: UsageMode | null;
  description?: string | null;
  created_at: string;
}

export interface UsageRecord {
  id: string;
  meeting_id: string;
  service_type: string;
  provider: string;
  model: string;
  usage_mode: UsageMode;
  credits_cost: number;
  status: string;
  created_at: string;
  meeting_title?: string | null;
}

export interface MeetingOverride {
  llm_usage_mode?: UsageMode | null;
  llm_provider?: string | null;
  llm_model?: string | null;
  transcription_usage_mode?: UsageMode | null;
  transcription_provider?: string | null;
  transcription_model?: string | null;
  email_mode?: UsageMode | null;
  email_provider?: string | null;
}
