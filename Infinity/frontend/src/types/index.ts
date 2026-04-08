// Common types
export interface PaginatedResponse<T> {
  total: number
  page: number
  limit: number
  total_pages: number
  data: T[]
}

export interface SuccessMessage {
  message: string
}

// ============ LEADS ============
export interface Lead {
  id: string
  user_id: string
  name: string | null
  phone: string | null
  email: string | null
  gender: string | null
  marital_status: string | null
  occupation: string | null
  income_group: string | null
  age_group: string | null
  area: string | null
  source: string | null
  referred_by: string | null
  dependants: number | null
  source_description: string | null
  status: string
  scheduled_date: string | null
  scheduled_time: string | null
  all_day: boolean | null
  notes: string | null
  converted_to_client_id: string | null
  conversion_date: string | null
  tat_days: number | null
  created_at: string
  updated_at: string
}

export interface LeadCreate {
  name: string
  phone: string
  email?: string | null
  gender?: string | null
  marital_status?: string | null
  occupation?: string | null
  income_group?: string | null
  age_group?: string | null
  area?: string | null
  source: string
  referred_by?: string | null
  dependants?: number | null
  source_description?: string | null
  status?: string
  scheduled_date?: string | null
  scheduled_time?: string | null
  all_day?: boolean | null
  notes?: string | null
}

export type LeadUpdate = Partial<LeadCreate>

export interface LeadListResponse {
  leads: Lead[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface LeadStatusUpdate {
  status: string
  scheduled_date?: string | null
  scheduled_time?: string | null
  notes?: string | null
}

// ============ CLIENTS ============
export interface Client {
  id: string
  user_id: string
  name: string
  phone: string
  email: string | null
  birthdate: string | null
  age: number | null
  age_group: string | null
  gender: string | null
  marital_status: string | null
  occupation: string | null
  income_group: string | null
  address: string | null
  area: string | null
  risk_profile: string | null
  source: string | null
  referred_by: string | null
  term_insurance: number | null
  health_insurance: number | null
  aum: number | null
  aum_bracket: string | null
  sip_amount: number | null
  sip_bracket: string | null
  dependants: number | null
  notes: string | null
  converted_from_lead_id: string | null
  conversion_date: string | null
  created_at: string
  updated_at: string
}

export interface ClientCreate {
  name: string
  phone: string
  email?: string | null
  birthdate?: string | null
  gender: string
  marital_status?: string | null
  occupation?: string | null
  income_group?: string | null
  address?: string | null
  area?: string | null
  risk_profile?: string | null
  source: string
  referred_by?: string | null
  term_insurance?: number | null
  health_insurance?: number | null
  aum?: number | null
  sip_amount?: number | null
  notes?: string | null
}

export type ClientUpdate = Partial<ClientCreate>

export interface ClientListResponse {
  clients: Client[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface ClientOverview {
  client: Client
  goals: Goal[]
  recent_touchpoints: Touchpoint[]
  open_opportunities: BusinessOpportunity[]
  pending_tasks: Task[]
  stats: Record<string, unknown>
}

export interface ConvertLeadRequest {
  lead_id: string
  birthdate: string
  email?: string | null
  address?: string | null
  risk_profile?: string | null
}

// ============ TASKS ============
export interface Task {
  id: string
  user_id: string
  title: string | null
  description?: string | null
  client_id: string | null
  lead_id: string | null
  client_name: string | null
  lead_name: string | null
  priority: string
  medium: string | null
  due_date: string
  due_time: string | null
  status: string
  completed_at: string | null
  original_due_date: string | null
  carry_forward_count: number
  all_day: boolean | null
  product_type: string | null
  is_business_opportunity: boolean | null
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string | null
  client_id?: string | null
  lead_id?: string | null
  priority?: string
  medium?: string | null
  due_date: string
  due_time?: string | null
  all_day?: boolean | null
  product_type?: string | null
  is_business_opportunity?: boolean | null
}

export type TaskUpdate = Partial<TaskCreate> & { status?: string }

export interface TaskListResponse {
  tasks: Task[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface TodayTasksResponse {
  pending: Task[]
  completed: Task[]
  overdue: Task[]
  pending_count: number
  completed_count: number
  overdue_count: number
}

// ============ TOUCHPOINTS ============
export interface Touchpoint {
  id: string
  user_id: string
  client_id: string | null
  lead_id: string | null
  client_name: string | null
  lead_name: string | null
  interaction_type: string
  scheduled_date: string
  scheduled_time: string | null
  location: string | null
  agenda: string | null
  status: string
  completed_at: string | null
  mom_text: string | null
  mom_pdf_url: string | null
  created_at: string
  updated_at: string
}

export interface TouchpointCreate {
  client_id?: string | null
  lead_id?: string | null
  interaction_type: string
  scheduled_date: string
  scheduled_time?: string | null
  location?: string | null
  agenda?: string | null
  status?: string
}

export type TouchpointUpdate = Partial<TouchpointCreate> & { mom_text?: string | null }

export interface TouchpointListResponse {
  touchpoints: Touchpoint[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface TouchpointComplete {
  actual_date?: string | null
  actual_time?: string | null
  duration_minutes?: number | null
  notes?: string | null
  mom_text?: string | null
  outcome?: string
  create_follow_up_task?: boolean
  follow_up_task_title?: string | null
  follow_up_task_date?: string | null
  create_business_opportunity?: boolean
  opportunity_type?: string | null
  opportunity_amount?: number | null
}

// ============ BUSINESS OPPORTUNITIES ============
export interface BusinessOpportunity {
  id: string
  user_id: string
  client_id: string | null
  lead_id: string | null
  client_name: string | null
  lead_name: string | null
  opportunity_type: string
  opportunity_stage: string
  opportunity_source: string | null
  expected_amount: number | null
  due_date: string | null
  notes: string | null
  outcome: string | null
  outcome_date: string | null
  outcome_amount: number | null
  tat_days: number | null
  created_at: string
  updated_at: string
}

export interface BOCreate {
  client_id?: string | null
  lead_id?: string | null
  opportunity_type: string
  opportunity_stage?: string
  opportunity_source?: string | null
  expected_amount: number
  due_date?: string | null
  notes?: string | null
}

export type BOUpdate = Partial<BOCreate> & {
  outcome?: string
  outcome_date?: string | null
  outcome_amount?: number | null
}

export interface BOListResponse {
  opportunities: BusinessOpportunity[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface BOPipelineStage {
  stage: string
  count: number
  total_amount: number
  opportunities: BusinessOpportunity[]
}

export interface BOPipelineResponse {
  stages: BOPipelineStage[]
  total_open: number
  total_open_amount: number
  total_won: number
  total_won_amount: number
  total_lost: number
}

export interface BOOutcomeUpdate {
  outcome: string
  outcome_date: string
  outcome_amount?: number | null
  notes?: string | null
}

// ============ GOALS ============
export interface GoalProduct {
  name: string
  type: string
  amount: number
  return_rate?: number | null
}

export interface Goal {
  id: string
  user_id: string
  client_id: string
  client_name: string | null
  goal_type: string
  goal_name: string
  target_amount: number
  target_date: string | null
  target_age: number | null
  current_investment: number
  monthly_sip: number
  lumpsum_investment: number
  expected_return_rate: number | null
  products: GoalProduct[] | null
  parent_goal_id: string | null
  child_name: string | null
  child_current_age: number | null
  lifestyle_subtype: string | null
  vehicle_type: string | null
  calculator_type: string | null
  calculator_inputs: Record<string, unknown> | null
  calculator_outputs: Record<string, unknown> | null
  progress_percent: number
  status: string
  pdf_url: string | null
  created_at: string
  updated_at: string
}

export interface GoalCreate {
  client_id: string
  goal_type: string
  goal_name: string
  target_amount: number
  target_date?: string | null
  target_age?: number | null
  current_investment?: number
  monthly_sip?: number
  lumpsum_investment?: number
  expected_return_rate?: number | null
  products?: GoalProduct[] | null
  parent_goal_id?: string | null
  child_name?: string | null
  child_current_age?: number | null
  lifestyle_subtype?: string | null
  vehicle_type?: string | null
}

export type GoalUpdate = Partial<GoalCreate> & { status?: string }

export interface GoalListResponse {
  goals: Goal[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface GoalWithSubgoals {
  parent_goal: Goal
  sub_goals: Goal[]
  total_target: number
  total_monthly_sip: number
}

// ============ CLIENT PRODUCTS ============
export interface ClientProduct {
  id: string
  user_id: string
  client_id: string
  product_id: string | null
  product_name: string
  category: string
  sub_category: string | null
  provider_name: string | null
  investment_type: string
  status: string
  invested_amount: number
  current_value: number
  units: number | null
  nav: number | null
  sip_amount: number
  sip_date: number | null
  sum_assured: number | null
  premium_amount: number | null
  premium_frequency: string | null
  start_date: string | null
  maturity_date: string | null
  next_due_date: string | null
  last_updated_date: string | null
  folio_number: string | null
  policy_number: string | null
  account_number: string | null
  goal_id: string | null
  goal_name: string | null
  nominee_name: string | null
  nominee_relation: string | null
  notes: string | null
  gain_loss: number | null
  gain_loss_percent: number | null
  created_at: string
  updated_at: string
}

export interface ClientProductCreate {
  client_id: string
  product_id?: string | null
  product_name: string
  category: string
  sub_category?: string | null
  provider_name?: string | null
  investment_type?: string
  invested_amount?: number
  current_value?: number
  units?: number | null
  nav?: number | null
  sip_amount?: number
  sip_date?: number | null
  sum_assured?: number | null
  premium_amount?: number | null
  premium_frequency?: string | null
  start_date?: string | null
  maturity_date?: string | null
  next_due_date?: string | null
  folio_number?: string | null
  policy_number?: string | null
  account_number?: string | null
  goal_id?: string | null
  nominee_name?: string | null
  nominee_relation?: string | null
  notes?: string | null
}

export type ClientProductUpdate = Partial<ClientProductCreate> & { status?: string }

export interface ClientProductListResponse {
  products: ClientProduct[]
  total: number
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_sip: number
}

export interface PortfolioSummary {
  client_id: string
  client_name: string
  total_aum: number
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percent: number
  total_sip: number
  by_category: Record<string, number>
  by_investment_type: Record<string, number>
  by_provider: Record<string, number>
  products_count: number
  active_sips_count: number
}

export interface ProductTransaction {
  id: string
  user_id: string
  client_product_id: string
  transaction_type: string
  transaction_date: string
  amount: number
  units: number | null
  nav: number | null
  reference_number: string | null
  notes: string | null
  created_at: string
}

export interface ProductTransactionCreate {
  client_product_id: string
  transaction_type: string
  transaction_date: string
  amount: number
  units?: number | null
  nav?: number | null
  reference_number?: string | null
  notes?: string | null
}

// ============ NOTIFICATIONS ============
export interface Notification {
  id: string
  user_id: string
  title: string
  message: string
  notification_type: string
  related_entity_type: string | null
  related_entity_id: string | null
  is_read: boolean
  read_at: string | null
  created_at: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  unread_count: number
}

// ============ CAMPAIGNS ============
export interface Campaign {
  id: string
  user_id: string
  name: string
  description: string | null
  campaign_type: string | null
  message_template: string | null
  channel: string | null
  scheduled_date: string | null
  is_executed: boolean
  executed_at: string | null
  total_recipients: number
  successful_sends: number
  failed_sends: number
  created_at: string
  updated_at: string
}

export interface CampaignCreate {
  name: string
  description?: string | null
  campaign_type?: string | null
  message_template?: string | null
  channel?: string | null
  scheduled_date?: string | null
  client_ids?: string[]
  filters?: Record<string, unknown> | null
}

export type CampaignUpdate = Partial<CampaignCreate>

export interface CampaignListResponse {
  campaigns: Campaign[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// ============ TEMPLATES ============
export interface MessageTemplate {
  id: string
  user_id: string | null
  template_type: string
  channel: string
  name: string
  subject: string | null
  content: string
  is_active: boolean
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface MessageTemplateCreate {
  template_type: string
  channel: string
  name: string
  subject?: string | null
  content: string
}

export type MessageTemplateUpdate = Partial<MessageTemplateCreate> & { is_active?: boolean }

// ============ DOCUMENTS ============
export interface Document {
  id: string
  user_id: string
  client_id: string
  name: string
  document_type: string | null
  file_url: string
  file_size: number | null
  mime_type: string | null
  shared_with_client: boolean
  shared_at: string | null
  shared_via: string | null
  created_at: string
  updated_at: string
}

// ============ PROFILE ============
export interface Profile {
  id: string
  user_id: string
  name: string
  phone: string
  age: number | null
  gender: string | null
  area: string | null
  num_employees: number
  employee_names: string | null
  eod_time: string | null
  google_connected: boolean
  google_email: string | null
  notification_email: boolean
  notification_whatsapp: boolean
  notification_eod: boolean
  morning_schedule_time: string | null
  afternoon_schedule_time: string | null
  eod_schedule_time: string | null
  whatsapp_number: string | null
  email_daily_enabled: boolean
  whatsapp_daily_enabled: boolean
  whatsapp_greetings_enabled: boolean
  created_at: string
  updated_at: string
}

export interface ProfileCreate {
  name: string
  phone: string
  age?: number | null
  gender?: string | null
  area?: string | null
  num_employees?: number
  employee_names?: string | null
  eod_time?: string
}

export type ProfileUpdate = Partial<ProfileCreate> & {
  notification_email?: boolean
  notification_whatsapp?: boolean
  notification_eod?: boolean
  morning_schedule_time?: string | null
  afternoon_schedule_time?: string | null
  eod_schedule_time?: string | null
  whatsapp_number?: string | null
  email_daily_enabled?: boolean
  whatsapp_daily_enabled?: boolean
  whatsapp_greetings_enabled?: boolean
}

// ============ SEARCH ============
export interface SearchResults {
  query: string
  clients: SearchResultItem[]
  leads: SearchResultItem[]
  tasks: SearchResultItem[]
  touchpoints: SearchResultItem[]
  goals: SearchResultItem[]
  total: number
}

export interface SearchResultItem {
  id: string
  entity_type: string
  name: string
  subtitle?: string | null
  match_field: string
}

// ============ DASHBOARD ============
export interface DashboardStats {
  total_clients: number
  total_leads: number
  total_aum: number
  total_pipeline_value: number
  conversion_rate: number
  total_tasks_today: number
  completed_tasks_today: number
  upcoming_touchpoints: number
  [key: string]: unknown
}

export interface DailySchedule {
  date: string
  tasks: Task[]
  touchpoints: Touchpoint[]
  followups: Lead[]
  birthdays: Client[]
  stats: Record<string, unknown>
}

// ============ SCHEDULER ============
export interface ScheduledNotification {
  id: string
  user_id: string
  notification_type: string
  channel: string
  scheduled_time: string
  sent_at: string | null
  status: string
  content: Record<string, unknown> | null
  error_message: string | null
  created_at: string
}

// ============ SHEETS SYNC ============
export interface SyncStatus {
  is_syncing: boolean
  last_sync_at: string | null
  last_sync_status: string | null
  sheet_id: string | null
  sheet_url: string | null
}

export interface SyncHistory {
  id: string
  sync_type: string
  status: string
  records_synced: number
  error_message: string | null
  created_at: string
}
