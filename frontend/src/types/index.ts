/**
 * Type definitions for Litea frontend
 * Matches backend API schemas
 */

export interface Task {
  id: number
  name: string
  prompt: string
  keywords: Array<{ keyword: string; is_user_defined: boolean }> | string[]
  sources: Array<{ source_name: string; parameters: Record<string, any> }> | string[]
  schedule_config?: ScheduleConfig
  run_at_hour?: number | null
  run_at_minute?: number
  run_timezone?: string
  notification_config?: NotificationConfig
  notification?: {
    channel: string
    recipients: string[]
    schedule: string | null
    options: Record<string, any>
  }
  status: 'inactive' | 'active'
  created_at: string
  updated_at: string
  last_run_at?: string
  next_run_at?: string
}

export interface ScheduleConfig {
  hour: number
  minute: number
}

export interface NotificationConfig {
  enabled: boolean
  channels: string[]
  email?: string
  wechat_webhook?: string
  webhook_url?: string
}

// Old backend types (for compatibility)
export interface NotificationChannel {
  channel_type: string
  config: Record<string, any>
}

export interface TaskSource {
  source_name: string
  parameters: Record<string, any>
}

export interface Document {
  id: number
  task_id: number
  run_id: string
  source: string  // Simplified field name
  source_name?: string  // For compatibility
  external_id: string
  title: string
  authors: string[]
  abstract: string
  url: string
  pdf_url?: string
  published_date?: string  // Simplified field name
  published_at?: string  // For compatibility
  citation_count?: number
  keywords: string[]
  user_keywords?: string[]
  extra_metadata?: Record<string, any>
  is_filtered_in?: boolean
  rank_score?: number
  zotero_key?: string
  summary?: DocumentSummary
  created_at?: string
}

export interface DocumentSummary {
  summary: string
  highlights: string[]
  research_trends: string[]
  agent_metadata: Record<string, any>
  created_at: string
}

export interface RetrievalSource {
  name: string
  display_name: string
  description: string
  enabled: boolean
}

export interface TaskTrend {
  date: string
  total_count: number
  filtered_count: number
}

export interface KeywordDistribution {
  keyword: string
  count: number
}

export interface SourceDistribution {
  source_name: string
  count: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  pagination: {
    limit: number
    offset: number
  }
}

export interface ApiError {
  error: string
  details?: any
}

// Form types
export interface TaskFormData {
  name: string
  prompt: string
  keywords: string[]
  sources: string[]
  schedule_config: ScheduleConfig
  notification_config: NotificationConfig
}

export interface DocumentFilters {
  page?: number
  page_size?: number
  task_id?: number
  source?: string
  keyword?: string
  search?: string
  sort?: string
  year_from?: number
  year_to?: number
  citations_min?: number
  citations_max?: number
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}
