| table_name              | column_name                | data_type                | is_nullable | column_default                         |
| ----------------------- | -------------------------- | ------------------------ | ----------- | -------------------------------------- |
| app_config              | id                         | bigint                   | NO          | nextval('app_config_id_seq'::regclass) |
| app_config              | key                        | text                     | NO          | null                                   |
| app_config              | value                      | text                     | NO          | null                                   |
| app_config              | description                | text                     | YES         | null                                   |
| app_config              | created_at                 | timestamp with time zone | YES         | now()                                  |
| app_config              | updated_at                 | timestamp with time zone | YES         | now()                                  |
| business_opportunities  | id                         | uuid                     | NO          | gen_random_uuid()                      |
| business_opportunities  | user_id                    | uuid                     | NO          | null                                   |
| business_opportunities  | client_id                  | uuid                     | YES         | null                                   |
| business_opportunities  | lead_id                    | uuid                     | YES         | null                                   |
| business_opportunities  | expected_amount            | numeric                  | YES         | null                                   |
| business_opportunities  | opportunity_stage          | USER-DEFINED             | NO          | 'identified'::opportunity_stage_type   |
| business_opportunities  | opportunity_type           | USER-DEFINED             | NO          | null                                   |
| business_opportunities  | opportunity_source         | USER-DEFINED             | NO          | null                                   |
| business_opportunities  | additional_info            | text                     | YES         | null                                   |
| business_opportunities  | due_date                   | date                     | NO          | null                                   |
| business_opportunities  | due_time                   | time without time zone   | YES         | null                                   |
| business_opportunities  | outcome                    | USER-DEFINED             | YES         | 'open'::bo_outcome_type                |
| business_opportunities  | outcome_date               | date                     | YES         | null                                   |
| business_opportunities  | outcome_amount             | numeric                  | YES         | null                                   |
| business_opportunities  | tat_days                   | integer                  | YES         | null                                   |
| business_opportunities  | created_at                 | timestamp with time zone | YES         | now()                                  |
| business_opportunities  | updated_at                 | timestamp with time zone | YES         | now()                                  |
| business_opportunities  | google_event_id            | character varying        | YES         | null                                   |
| calculator_results      | id                         | uuid                     | NO          | gen_random_uuid()                      |
| calculator_results      | user_id                    | uuid                     | NO          | null                                   |
| calculator_results      | client_id                  | uuid                     | YES         | null                                   |
| calculator_results      | goal_id                    | uuid                     | YES         | null                                   |
| calculator_results      | calculator_type            | character varying        | NO          | null                                   |
| calculator_results      | inputs                     | jsonb                    | NO          | null                                   |
| calculator_results      | outputs                    | jsonb                    | NO          | null                                   |
| calculator_results      | pdf_url                    | character varying        | YES         | null                                   |
| calculator_results      | created_at                 | timestamp with time zone | YES         | now()                                  |
| calendar_event_queue    | id                         | uuid                     | NO          | gen_random_uuid()                      |
| calendar_event_queue    | user_id                    | uuid                     | NO          | null                                   |
| calendar_event_queue    | entity_type                | character varying        | NO          | null                                   |
| calendar_event_queue    | entity_id                  | uuid                     | NO          | null                                   |
| calendar_event_queue    | action                     | character varying        | NO          | null                                   |
| calendar_event_queue    | processed                  | boolean                  | YES         | false                                  |
| calendar_event_queue    | processed_at               | timestamp with time zone | YES         | null                                   |
| calendar_event_queue    | error_message              | text                     | YES         | null                                   |
| calendar_event_queue    | retry_count                | integer                  | YES         | 0                                      |
| calendar_event_queue    | created_at                 | timestamp with time zone | YES         | now()                                  |
| calendar_sync_logs      | id                         | uuid                     | NO          | gen_random_uuid()                      |
| calendar_sync_logs      | user_id                    | uuid                     | NO          | null                                   |
| calendar_sync_logs      | entity_type                | character varying        | NO          | null                                   |
| calendar_sync_logs      | entity_id                  | uuid                     | NO          | null                                   |
| calendar_sync_logs      | action                     | character varying        | NO          | null                                   |
| calendar_sync_logs      | google_event_id            | character varying        | YES         | null                                   |
| calendar_sync_logs      | status                     | character varying        | NO          | null                                   |
| calendar_sync_logs      | error_message              | text                     | YES         | null                                   |
| calendar_sync_logs      | created_at                 | timestamp with time zone | YES         | now()                                  |
| call_logs               | id                         | uuid                     | NO          | gen_random_uuid()                      |
| call_logs               | user_id                    | uuid                     | NO          | null                                   |
| call_logs               | client_id                  | uuid                     | YES         | null                                   |
| call_logs               | lead_id                    | uuid                     | YES         | null                                   |
| call_logs               | phone_number               | character varying        | NO          | null                                   |
| call_logs               | call_type                  | character varying        | NO          | null                                   |
| call_logs               | duration_seconds           | integer                  | YES         | 0                                      |
| call_logs               | call_time                  | timestamp with time zone | NO          | null                                   |
| call_logs               | notes                      | text                     | YES         | null                                   |
| call_logs               | created_at                 | timestamp with time zone | YES         | now()                                  |
| campaign_clients        | id                         | uuid                     | NO          | gen_random_uuid()                      |
| campaign_clients        | campaign_id                | uuid                     | NO          | null                                   |
| campaign_clients        | client_id                  | uuid                     | NO          | null                                   |
| campaign_clients        | contacted                  | boolean                  | YES         | false                                  |
| campaign_clients        | contacted_at               | timestamp with time zone | YES         | null                                   |
| campaign_clients        | contacted_via              | character varying        | YES         | null                                   |
| campaign_clients        | added_at                   | timestamp with time zone | YES         | now()                                  |
| campaigns               | id                         | uuid                     | NO          | gen_random_uuid()                      |
| campaigns               | user_id                    | uuid                     | NO          | null                                   |
| campaigns               | name                       | character varying        | NO          | null                                   |
| campaigns               | description                | text                     | YES         | null                                   |
| campaigns               | filter_criteria            | jsonb                    | YES         | null                                   |
| campaigns               | client_count               | integer                  | YES         | 0                                      |
| campaigns               | last_executed_at           | timestamp with time zone | YES         | null                                   |
| campaigns               | created_at                 | timestamp with time zone | YES         | now()                                  |
| campaigns               | updated_at                 | timestamp with time zone | YES         | now()                                  |
| client_cash_flow        | id                         | uuid                     | NO          | gen_random_uuid()                      |
| client_cash_flow        | user_id                    | uuid                     | NO          | null                                   |
| client_cash_flow        | client_id                  | uuid                     | NO          | null                                   |
| client_cash_flow        | insurance_premiums         | jsonb                    | YES         | '{}'::jsonb                            |
| client_cash_flow        | savings                    | jsonb                    | YES         | '{}'::jsonb                            |
| client_cash_flow        | loans                      | jsonb                    | YES         | '{}'::jsonb                            |
| client_cash_flow        | expenses                   | jsonb                    | YES         | '{}'::jsonb                            |
| client_cash_flow        | income                     | jsonb                    | YES         | '{}'::jsonb                            |
| client_cash_flow        | current_investments        | jsonb                    | YES         | '{}'::jsonb                            |
| client_cash_flow        | total_income_yearly        | numeric                  | YES         | 0                                      |
| client_cash_flow        | total_expenses_yearly      | numeric                  | YES         | 0                                      |
| client_cash_flow        | total_pending_loans        | numeric                  | YES         | 0                                      |
| client_cash_flow        | cash_surplus_yearly        | numeric                  | YES         | 0                                      |
| client_cash_flow        | cash_surplus_monthly       | numeric                  | YES         | 0                                      |
| client_cash_flow        | created_at                 | timestamp with time zone | YES         | now()                                  |
| client_cash_flow        | updated_at                 | timestamp with time zone | YES         | now()                                  |
| client_products         | id                         | uuid                     | NO          | gen_random_uuid()                      |
| client_products         | user_id                    | uuid                     | NO          | null                                   |
| client_products         | client_id                  | uuid                     | NO          | null                                   |
| client_products         | product_id                 | uuid                     | YES         | null                                   |
| client_products         | product_name               | character varying        | NO          | null                                   |
| client_products         | category                   | USER-DEFINED             | NO          | null                                   |
| client_products         | sub_category               | character varying        | YES         | null                                   |
| client_products         | provider_name              | character varying        | YES         | null                                   |
| client_products         | investment_type            | USER-DEFINED             | NO          | 'lumpsum'::investment_type             |
| client_products         | status                     | USER-DEFINED             | YES         | 'active'::product_status_type          |
| client_products         | invested_amount            | numeric                  | YES         | 0                                      |
| client_products         | current_value              | numeric                  | YES         | 0                                      |
| client_products         | units                      | numeric                  | YES         | null                                   |
| client_products         | nav                        | numeric                  | YES         | null                                   |
| client_products         | sip_amount                 | numeric                  | YES         | 0                                      |
| client_products         | sip_date                   | integer                  | YES         | null                                   |
| client_products         | sum_assured                | numeric                  | YES         | null                                   |
| client_products         | premium_amount             | numeric                  | YES         | null                                   |
| client_products         | premium_frequency          | USER-DEFINED             | YES         | null                                   |
| client_products         | start_date                 | date                     | YES         | null                                   |
| client_products         | maturity_date              | date                     | YES         | null                                   |
| client_products         | next_due_date              | date                     | YES         | null                                   |
| client_products         | last_updated_date          | date                     | YES         | null                                   |
| client_products         | folio_number               | character varying        | YES         | null                                   |
| client_products         | policy_number              | character varying        | YES         | null                                   |
| client_products         | account_number             | character varying        | YES         | null                                   |
| client_products         | goal_id                    | uuid                     | YES         | null                                   |
| client_products         | nominee_name               | character varying        | YES         | null                                   |
| client_products         | nominee_relation           | character varying        | YES         | null                                   |
| client_products         | notes                      | text                     | YES         | null                                   |
| client_products         | created_at                 | timestamp with time zone | YES         | now()                                  |
| client_products         | updated_at                 | timestamp with time zone | YES         | now()                                  |
| clients                 | id                         | uuid                     | NO          | gen_random_uuid()                      |
| clients                 | user_id                    | uuid                     | NO          | null                                   |
| clients                 | name                       | character varying        | NO          | null                                   |
| clients                 | phone                      | character varying        | NO          | null                                   |
| clients                 | email                      | character varying        | YES         | null                                   |
| clients                 | address                    | text                     | YES         | null                                   |
| clients                 | area                       | character varying        | YES         | null                                   |
| clients                 | birthdate                  | date                     | YES         | null                                   |
| clients                 | age                        | integer                  | YES         | null                                   |
| clients                 | age_group                  | USER-DEFINED             | YES         | null                                   |
| clients                 | gender                     | USER-DEFINED             | NO          | null                                   |
| clients                 | marital_status             | USER-DEFINED             | YES         | null                                   |
| clients                 | occupation                 | USER-DEFINED             | YES         | null                                   |
| clients                 | income_group               | USER-DEFINED             | YES         | null                                   |
| clients                 | dependants                 | integer                  | YES         | 0                                      |
| clients                 | risk_profile               | USER-DEFINED             | YES         | null                                   |
| clients                 | investment_age             | integer                  | YES         | 0                                      |
| clients                 | source                     | USER-DEFINED             | NO          | null                                   |
| clients                 | source_description         | character varying        | YES         | null                                   |
| clients                 | sourced_by                 | character varying        | YES         | null                                   |
| clients                 | total_aum                  | numeric                  | YES         | 0                                      |
| clients                 | sip                        | numeric                  | YES         | 0                                      |
| clients                 | term_insurance             | numeric                  | YES         | 0                                      |
| clients                 | health_insurance           | numeric                  | YES         | 0                                      |
| clients                 | pa_insurance               | numeric                  | YES         | 0                                      |
| clients                 | swp                        | numeric                  | YES         | 0                                      |
| clients                 | corpus                     | numeric                  | YES         | 0                                      |
| clients                 | pms                        | numeric                  | YES         | 0                                      |
| clients                 | aif                        | numeric                  | YES         | 0                                      |
| clients                 | las                        | numeric                  | YES         | 0                                      |
| clients                 | li_premium                 | numeric                  | YES         | 0                                      |
| clients                 | ulips                      | numeric                  | YES         | 0                                      |
| clients                 | aum_bracket                | USER-DEFINED             | YES         | null                                   |
| clients                 | sip_bracket                | USER-DEFINED             | YES         | null                                   |
| clients                 | client_tenure              | USER-DEFINED             | YES         | null                                   |
| clients                 | notes                      | text                     | YES         | null                                   |
| clients                 | touchpoints_this_year      | integer                  | YES         | 0                                      |
| clients                 | goals_count                | integer                  | YES         | 0                                      |
| clients                 | drive_folder_id            | character varying        | YES         | null                                   |
| clients                 | converted_from_lead_id     | uuid                     | YES         | null                                   |
| clients                 | conversion_date            | date                     | YES         | null                                   |
| clients                 | tat_days                   | integer                  | YES         | null                                   |
| clients                 | client_creation_year       | integer                  | YES         | null                                   |
| clients                 | client_creation_date       | date                     | YES         | CURRENT_DATE                           |
| clients                 | is_deleted                 | boolean                  | YES         | false                                  |
| clients                 | deleted_at                 | timestamp with time zone | YES         | null                                   |
| clients                 | created_at                 | timestamp with time zone | YES         | now()                                  |
| clients                 | updated_at                 | timestamp with time zone | YES         | now()                                  |
| communication_logs      | id                         | uuid                     | NO          | gen_random_uuid()                      |
| communication_logs      | user_id                    | uuid                     | NO          | null                                   |
| communication_logs      | client_id                  | uuid                     | YES         | null                                   |
| communication_logs      | lead_id                    | uuid                     | YES         | null                                   |
| communication_logs      | channel                    | character varying        | NO          | null                                   |
| communication_logs      | message_type               | character varying        | YES         | null                                   |
| communication_logs      | recipient_phone            | character varying        | YES         | null                                   |
| communication_logs      | recipient_email            | character varying        | YES         | null                                   |
| communication_logs      | subject                    | character varying        | YES         | null                                   |
| communication_logs      | body                       | text                     | YES         | null                                   |
| communication_logs      | attachment_url             | character varying        | YES         | null                                   |
| communication_logs      | status                     | character varying        | YES         | 'sent'::character varying              |
| communication_logs      | error_message              | text                     | YES         | null                                   |
| communication_logs      | sent_at                    | timestamp with time zone | YES         | now()                                  |
| communication_logs      | is_automated               | boolean                  | YES         | false                                  |
| communication_logs      | scheduled_notification_id  | uuid                     | YES         | null                                   |
| communication_logs      | external_message_id        | character varying        | YES         | null                                   |
| communication_logs      | delivery_status            | character varying        | YES         | 'pending'::character varying           |
| documents               | id                         | uuid                     | NO          | gen_random_uuid()                      |
| documents               | user_id                    | uuid                     | NO          | null                                   |
| documents               | client_id                  | uuid                     | NO          | null                                   |
| documents               | name                       | character varying        | NO          | null                                   |
| documents               | document_type              | character varying        | YES         | null                                   |
| documents               | file_url                   | character varying        | NO          | null                                   |
| documents               | drive_file_id              | character varying        | YES         | null                                   |
| documents               | file_size                  | integer                  | YES         | null                                   |
| documents               | mime_type                  | character varying        | YES         | null                                   |
| documents               | related_entity_type        | character varying        | YES         | null                                   |
| documents               | related_entity_id          | uuid                     | YES         | null                                   |
| documents               | shared_with_client         | boolean                  | YES         | false                                  |
| documents               | shared_at                  | timestamp with time zone | YES         | null                                   |
| documents               | shared_via                 | character varying        | YES         | null                                   |
| documents               | created_at                 | timestamp with time zone | YES         | now()                                  |
| documents               | updated_at                 | timestamp with time zone | YES         | now()                                  |
| email_logs              | id                         | uuid                     | NO          | gen_random_uuid()                      |
| email_logs              | user_id                    | uuid                     | NO          | null                                   |
| email_logs              | email_type                 | character varying        | NO          | null                                   |
| email_logs              | target_date                | date                     | NO          | null                                   |
| email_logs              | recipient_email            | character varying        | NO          | null                                   |
| email_logs              | subject                    | character varying        | YES         | null                                   |
| email_logs              | status                     | character varying        | NO          | null                                   |
| email_logs              | resend_message_id          | character varying        | YES         | null                                   |
| email_logs              | error_message              | text                     | YES         | null                                   |
| email_logs              | items_snapshot             | jsonb                    | YES         | null                                   |
| email_logs              | created_at                 | timestamp with time zone | YES         | now()                                  |
| email_logs              | updated_at                 | timestamp with time zone | YES         | now()                                  |
| excel_sync_logs         | id                         | uuid                     | NO          | gen_random_uuid()                      |
| excel_sync_logs         | user_id                    | uuid                     | NO          | null                                   |
| excel_sync_logs         | sync_type                  | character varying        | NO          | null                                   |
| excel_sync_logs         | sync_direction             | character varying        | NO          | null                                   |
| excel_sync_logs         | records_synced             | integer                  | YES         | 0                                      |
| excel_sync_logs         | records_created            | integer                  | YES         | 0                                      |
| excel_sync_logs         | records_updated            | integer                  | YES         | 0                                      |
| excel_sync_logs         | conflicts_resolved         | integer                  | YES         | 0                                      |
| excel_sync_logs         | status                     | character varying        | NO          | null                                   |
| excel_sync_logs         | error_message              | text                     | YES         | null                                   |
| excel_sync_logs         | started_at                 | timestamp with time zone | NO          | null                                   |
| excel_sync_logs         | completed_at               | timestamp with time zone | YES         | null                                   |
| goal_history            | id                         | uuid                     | NO          | gen_random_uuid()                      |
| goal_history            | goal_id                    | uuid                     | NO          | null                                   |
| goal_history            | previous_values            | jsonb                    | NO          | null                                   |
| goal_history            | change_reason              | character varying        | YES         | null                                   |
| goal_history            | changed_by                 | uuid                     | YES         | null                                   |
| goal_history            | created_at                 | timestamp with time zone | YES         | now()                                  |
| goals                   | id                         | uuid                     | NO          | gen_random_uuid()                      |
| goals                   | user_id                    | uuid                     | NO          | null                                   |
| goals                   | client_id                  | uuid                     | NO          | null                                   |
| goals                   | goal_type                  | USER-DEFINED             | NO          | null                                   |
| goals                   | goal_name                  | character varying        | NO          | null                                   |
| goals                   | target_amount              | numeric                  | NO          | null                                   |
| goals                   | target_date                | date                     | YES         | null                                   |
| goals                   | target_age                 | integer                  | YES         | null                                   |
| goals                   | current_investment         | numeric                  | YES         | 0                                      |
| goals                   | monthly_sip                | numeric                  | YES         | 0                                      |
| goals                   | lumpsum_investment         | numeric                  | YES         | 0                                      |
| goals                   | expected_return_rate       | numeric                  | YES         | null                                   |
| goals                   | products                   | jsonb                    | YES         | null                                   |
| goals                   | calculator_type            | character varying        | YES         | null                                   |
| goals                   | calculator_inputs          | jsonb                    | YES         | null                                   |
| goals                   | calculator_outputs         | jsonb                    | YES         | null                                   |
| goals                   | progress_percent           | numeric                  | YES         | 0                                      |
| goals                   | status                     | USER-DEFINED             | YES         | 'active'::goal_status_type             |
| goals                   | pdf_url                    | character varying        | YES         | null                                   |
| goals                   | pdf_generated_at           | timestamp with time zone | YES         | null                                   |
| goals                   | excel_link                 | character varying        | YES         | null                                   |
| goals                   | created_at                 | timestamp with time zone | YES         | now()                                  |
| goals                   | updated_at                 | timestamp with time zone | YES         | now()                                  |
| goals                   | parent_goal_id             | uuid                     | YES         | null                                   |
| goals                   | child_name                 | character varying        | YES         | null                                   |
| goals                   | child_current_age          | integer                  | YES         | null                                   |
| goals                   | lifestyle_subtype          | USER-DEFINED             | YES         | null                                   |
| goals                   | vehicle_type               | USER-DEFINED             | YES         | null                                   |
| investment_products     | id                         | uuid                     | NO          | gen_random_uuid()                      |
| investment_products     | name                       | character varying        | NO          | null                                   |
| investment_products     | code                       | character varying        | NO          | null                                   |
| investment_products     | default_return_rate        | numeric                  | NO          | null                                   |
| investment_products     | supports_sip               | boolean                  | YES         | true                                   |
| investment_products     | supports_lumpsum           | boolean                  | YES         | true                                   |
| investment_products     | display_order              | integer                  | YES         | 0                                      |
| investment_products     | is_active                  | boolean                  | YES         | true                                   |
| investment_products     | created_at                 | timestamp with time zone | YES         | now()                                  |
| leads                   | id                         | uuid                     | NO          | gen_random_uuid()                      |
| leads                   | user_id                    | uuid                     | NO          | null                                   |
| leads                   | name                       | character varying        | NO          | null                                   |
| leads                   | phone                      | character varying        | YES         | null                                   |
| leads                   | email                      | character varying        | YES         | null                                   |
| leads                   | age_group                  | USER-DEFINED             | YES         | null                                   |
| leads                   | gender                     | USER-DEFINED             | YES         | null                                   |
| leads                   | marital_status             | USER-DEFINED             | YES         | null                                   |
| leads                   | occupation                 | USER-DEFINED             | YES         | null                                   |
| leads                   | income_group               | USER-DEFINED             | YES         | null                                   |
| leads                   | dependants                 | integer                  | YES         | 0                                      |
| leads                   | area                       | character varying        | YES         | null                                   |
| leads                   | source                     | USER-DEFINED             | NO          | null                                   |
| leads                   | source_description         | character varying        | YES         | null                                   |
| leads                   | sourced_by                 | character varying        | YES         | null                                   |
| leads                   | status                     | USER-DEFINED             | YES         | 'follow_up'::lead_status_type          |
| leads                   | notes                      | text                     | YES         | null                                   |
| leads                   | scheduled_date             | date                     | YES         | null                                   |
| leads                   | scheduled_time             | time without time zone   | YES         | null                                   |
| leads                   | all_day                    | boolean                  | YES         | false                                  |
| leads                   | converted_to_client_id     | uuid                     | YES         | null                                   |
| leads                   | conversion_date            | timestamp with time zone | YES         | null                                   |
| leads                   | tat_days                   | integer                  | YES         | null                                   |
| leads                   | created_at                 | timestamp with time zone | YES         | now()                                  |
| leads                   | updated_at                 | timestamp with time zone | YES         | now()                                  |
| leads                   | google_event_id            | character varying        | YES         | null                                   |
| message_templates       | id                         | uuid                     | NO          | gen_random_uuid()                      |
| message_templates       | user_id                    | uuid                     | YES         | null                                   |
| message_templates       | template_type              | character varying        | NO          | null                                   |
| message_templates       | channel                    | character varying        | NO          | null                                   |
| message_templates       | name                       | character varying        | NO          | null                                   |
| message_templates       | subject                    | character varying        | YES         | null                                   |
| message_templates       | content                    | text                     | NO          | null                                   |
| message_templates       | is_active                  | boolean                  | YES         | true                                   |
| message_templates       | is_system                  | boolean                  | YES         | true                                   |
| message_templates       | created_at                 | timestamp with time zone | YES         | now()                                  |
| message_templates       | updated_at                 | timestamp with time zone | YES         | now()                                  |
| mfd_profiles            | id                         | uuid                     | NO          | gen_random_uuid()                      |
| mfd_profiles            | user_id                    | uuid                     | NO          | null                                   |
| mfd_profiles            | name                       | character varying        | NO          | null                                   |
| mfd_profiles            | phone                      | character varying        | NO          | null                                   |
| mfd_profiles            | age                        | integer                  | YES         | null                                   |
| mfd_profiles            | gender                     | USER-DEFINED             | YES         | null                                   |
| mfd_profiles            | area                       | character varying        | YES         | null                                   |
| mfd_profiles            | num_employees              | integer                  | YES         | 0                                      |
| mfd_profiles            | employee_names             | text                     | YES         | null                                   |
| mfd_profiles            | eod_time                   | time without time zone   | YES         | '18:00:00'::time without time zone     |
| mfd_profiles            | google_connected           | boolean                  | YES         | false                                  |
| mfd_profiles            | google_email               | character varying        | YES         | null                                   |
| mfd_profiles            | google_access_token        | text                     | YES         | null                                   |
| mfd_profiles            | google_refresh_token       | text                     | YES         | null                                   |
| mfd_profiles            | google_token_expiry        | timestamp with time zone | YES         | null                                   |
| mfd_profiles            | google_drive_folder_id     | character varying        | YES         | null                                   |
| mfd_profiles            | google_sheet_id            | character varying        | YES         | null                                   |
| mfd_profiles            | google_clients_folder_id   | character varying        | YES         | null                                   |
| mfd_profiles            | notification_email         | boolean                  | YES         | true                                   |
| mfd_profiles            | notification_whatsapp      | boolean                  | YES         | true                                   |
| mfd_profiles            | notification_push          | boolean                  | YES         | true                                   |
| mfd_profiles            | created_at                 | timestamp with time zone | YES         | now()                                  |
| mfd_profiles            | updated_at                 | timestamp with time zone | YES         | now()                                  |
| mfd_profiles            | morning_schedule_time      | time without time zone   | YES         | '07:00:00'::time without time zone     |
| mfd_profiles            | afternoon_schedule_time    | time without time zone   | YES         | '14:00:00'::time without time zone     |
| mfd_profiles            | eod_schedule_time          | time without time zone   | YES         | '19:00:00'::time without time zone     |
| mfd_profiles            | whatsapp_number            | character varying        | YES         | null                                   |
| mfd_profiles            | email_daily_enabled        | boolean                  | YES         | true                                   |
| mfd_profiles            | whatsapp_daily_enabled     | boolean                  | YES         | true                                   |
| mfd_profiles            | whatsapp_greetings_enabled | boolean                  | YES         | true                                   |
| mfd_profiles            | sync_needed                | boolean                  | YES         | false                                  |
| mfd_profiles            | last_synced_at             | timestamp with time zone | YES         | null                                   |
| notifications           | id                         | uuid                     | NO          | gen_random_uuid()                      |
| notifications           | user_id                    | uuid                     | NO          | null                                   |
| notifications           | title                      | character varying        | NO          | null                                   |
| notifications           | body                       | text                     | YES         | null                                   |
| notifications           | notification_type          | character varying        | NO          | null                                   |
| notifications           | related_entity_type        | character varying        | YES         | null                                   |
| notifications           | related_entity_id          | uuid                     | YES         | null                                   |
| notifications           | is_read                    | boolean                  | YES         | false                                  |
| notifications           | read_at                    | timestamp with time zone | YES         | null                                   |
| notifications           | created_at                 | timestamp with time zone | YES         | now()                                  |
| product_transactions    | id                         | uuid                     | NO          | gen_random_uuid()                      |
| product_transactions    | user_id                    | uuid                     | NO          | null                                   |
| product_transactions    | client_product_id          | uuid                     | NO          | null                                   |
| product_transactions    | transaction_type           | USER-DEFINED             | NO          | null                                   |
| product_transactions    | transaction_date           | date                     | NO          | null                                   |
| product_transactions    | amount                     | numeric                  | NO          | null                                   |
| product_transactions    | units                      | numeric                  | YES         | null                                   |
| product_transactions    | nav                        | numeric                  | YES         | null                                   |
| product_transactions    | reference_number           | character varying        | YES         | null                                   |
| product_transactions    | notes                      | text                     | YES         | null                                   |
| product_transactions    | created_at                 | timestamp with time zone | YES         | now()                                  |
| products                | id                         | uuid                     | NO          | gen_random_uuid()                      |
| products                | name                       | character varying        | NO          | null                                   |
| products                | code                       | character varying        | YES         | null                                   |
| products                | category                   | USER-DEFINED             | NO          | null                                   |
| products                | sub_category               | character varying        | YES         | null                                   |
| products                | provider_name              | character varying        | YES         | null                                   |
| products                | provider_code              | character varying        | YES         | null                                   |
| products                | fund_house                 | character varying        | YES         | null                                   |
| products                | fund_type                  | character varying        | YES         | null                                   |
| products                | fund_sub_type              | character varying        | YES         | null                                   |
| products                | policy_type                | character varying        | YES         | null                                   |
| products                | expected_return_rate       | numeric                  | YES         | null                                   |
| products                | supports_sip               | boolean                  | YES         | false                                  |
| products                | supports_lumpsum           | boolean                  | YES         | true                                   |
| products                | is_active                  | boolean                  | YES         | true                                   |
| products                | created_at                 | timestamp with time zone | YES         | now()                                  |
| products                | updated_at                 | timestamp with time zone | YES         | now()                                  |
| push_notification_logs  | id                         | uuid                     | NO          | gen_random_uuid()                      |
| push_notification_logs  | user_id                    | uuid                     | NO          | null                                   |
| push_notification_logs  | title                      | character varying        | NO          | null                                   |
| push_notification_logs  | body                       | text                     | YES         | null                                   |
| push_notification_logs  | data                       | jsonb                    | YES         | null                                   |
| push_notification_logs  | device_tokens_count        | integer                  | YES         | 0                                      |
| push_notification_logs  | success_count              | integer                  | YES         | 0                                      |
| push_notification_logs  | failure_count              | integer                  | YES         | 0                                      |
| push_notification_logs  | fcm_response               | jsonb                    | YES         | null                                   |
| push_notification_logs  | related_entity_type        | character varying        | YES         | null                                   |
| push_notification_logs  | related_entity_id          | uuid                     | YES         | null                                   |
| push_notification_logs  | created_at                 | timestamp with time zone | YES         | now()                                  |
| quick_notes             | id                         | uuid                     | NO          | gen_random_uuid()                      |
| quick_notes             | user_id                    | uuid                     | NO          | null                                   |
| quick_notes             | content                    | text                     | NO          | null                                   |
| quick_notes             | tags                       | ARRAY                    | YES         | null                                   |
| quick_notes             | created_at                 | timestamp with time zone | YES         | now()                                  |
| quick_notes             | updated_at                 | timestamp with time zone | YES         | now()                                  |
| scheduled_notifications | id                         | uuid                     | NO          | gen_random_uuid()                      |
| scheduled_notifications | user_id                    | uuid                     | NO          | null                                   |
| scheduled_notifications | notification_type          | character varying        | NO          | null                                   |
| scheduled_notifications | channel                    | character varying        | NO          | null                                   |
| scheduled_notifications | scheduled_time             | timestamp with time zone | NO          | null                                   |
| scheduled_notifications | sent_at                    | timestamp with time zone | YES         | null                                   |
| scheduled_notifications | status                     | character varying        | YES         | 'pending'::character varying           |
| scheduled_notifications | content                    | jsonb                    | YES         | null                                   |
| scheduled_notifications | external_message_id        | character varying        | YES         | null                                   |
| scheduled_notifications | error_message              | text                     | YES         | null                                   |
| scheduled_notifications | created_at                 | timestamp with time zone | YES         | now()                                  |
| tasks                   | id                         | uuid                     | NO          | gen_random_uuid()                      |
| tasks                   | user_id                    | uuid                     | NO          | null                                   |
| tasks                   | client_id                  | uuid                     | YES         | null                                   |
| tasks                   | lead_id                    | uuid                     | YES         | null                                   |
| tasks                   | description                | text                     | NO          | null                                   |
| tasks                   | medium                     | USER-DEFINED             | YES         | null                                   |
| tasks                   | product_type               | character varying        | YES         | null                                   |
| tasks                   | priority                   | USER-DEFINED             | YES         | 'medium'::task_priority_type           |
| tasks                   | due_date                   | date                     | NO          | null                                   |
| tasks                   | due_time                   | time without time zone   | YES         | null                                   |
| tasks                   | all_day                    | boolean                  | YES         | false                                  |
| tasks                   | status                     | USER-DEFINED             | YES         | 'pending'::task_status_type            |
| tasks                   | completed_at               | timestamp with time zone | YES         | null                                   |
| tasks                   | is_business_opportunity    | boolean                  | YES         | false                                  |
| tasks                   | original_date              | date                     | YES         | null                                   |
| tasks                   | carry_forward_count        | integer                  | YES         | 0                                      |
| tasks                   | created_at                 | timestamp with time zone | YES         | now()                                  |
| tasks                   | updated_at                 | timestamp with time zone | YES         | now()                                  |
| tasks                   | google_event_id            | character varying        | YES         | null                                   |
| touchpoints             | id                         | uuid                     | NO          | gen_random_uuid()                      |
| touchpoints             | user_id                    | uuid                     | NO          | null                                   |
| touchpoints             | client_id                  | uuid                     | YES         | null                                   |
| touchpoints             | lead_id                    | uuid                     | YES         | null                                   |
| touchpoints             | interaction_type           | USER-DEFINED             | NO          | null                                   |
| touchpoints             | location                   | character varying        | YES         | null                                   |
| touchpoints             | purpose                    | text                     | YES         | null                                   |
| touchpoints             | scheduled_date             | date                     | NO          | null                                   |
| touchpoints             | scheduled_time             | time without time zone   | YES         | null                                   |
| touchpoints             | status                     | USER-DEFINED             | YES         | 'scheduled'::touchpoint_status_type    |
| touchpoints             | completed_at               | timestamp with time zone | YES         | null                                   |
| touchpoints             | mom_text                   | text                     | YES         | null                                   |
| touchpoints             | mom_audio_url              | character varying        | YES         | null                                   |
| touchpoints             | mom_pdf_url                | character varying        | YES         | null                                   |
| touchpoints             | mom_sent_to_client         | boolean                  | YES         | false                                  |
| touchpoints             | mom_sent_at                | timestamp with time zone | YES         | null                                   |
| touchpoints             | created_at                 | timestamp with time zone | YES         | now()                                  |
| touchpoints             | updated_at                 | timestamp with time zone | YES         | now()                                  |
| touchpoints             | google_event_id            | character varying        | YES         | null                                   |
| user_devices            | id                         | uuid                     | NO          | gen_random_uuid()                      |
| user_devices            | user_id                    | uuid                     | NO          | null                                   |
| user_devices            | device_token               | text                     | NO          | null                                   |
| user_devices            | device_type                | USER-DEFINED             | NO          | null                                   |
| user_devices            | device_name                | character varying        | YES         | null                                   |
| user_devices            | device_model               | character varying        | YES         | null                                   |
| user_devices            | os_version                 | character varying        | YES         | null                                   |
| user_devices            | app_version                | character varying        | YES         | null                                   |
| user_devices            | is_active                  | boolean                  | YES         | true                                   |
| user_devices            | last_used_at               | timestamp with time zone | YES         | now()                                  |
| user_devices            | created_at                 | timestamp with time zone | YES         | now()                                  |
| user_devices            | updated_at                 | timestamp with time zone | YES         | now()                                  |
| webhook_logs            | id                         | uuid                     | NO          | gen_random_uuid()                      |
| webhook_logs            | source                     | character varying        | NO          | null                                   |
| webhook_logs            | event_type                 | character varying        | NO          | null                                   |
| webhook_logs            | payload                    | jsonb                    | NO          | null                                   |
| webhook_logs            | processed                  | boolean                  | YES         | false                                  |
| webhook_logs            | processed_at               | timestamp with time zone | YES         | null                                   |
| webhook_logs            | processing_result          | jsonb                    | YES         | null                                   |
| webhook_logs            | related_user_id            | uuid                     | YES         | null                                   |
| webhook_logs            | related_entity_type        | character varying        | YES         | null                                   |
| webhook_logs            | related_entity_id          | uuid                     | YES         | null                                   |
| webhook_logs            | created_at                 | timestamp with time zone | YES         | now()                                  |
| whatsapp_data_inputs    | id                         | uuid                     | NO          | gen_random_uuid()                      |
| whatsapp_data_inputs    | user_id                    | uuid                     | NO          | null                                   |
| whatsapp_data_inputs    | input_type                 | character varying        | NO          | null                                   |
| whatsapp_data_inputs    | raw_message                | text                     | YES         | null                                   |
| whatsapp_data_inputs    | parsed_data                | jsonb                    | YES         | null                                   |
| whatsapp_data_inputs    | voice_note_url             | text                     | YES         | null                                   |
| whatsapp_data_inputs    | transcription              | text                     | YES         | null                                   |
| whatsapp_data_inputs    | status                     | character varying        | YES         | 'pending'::character varying           |
| whatsapp_data_inputs    | processed_at               | timestamp with time zone | YES         | null                                   |
| whatsapp_data_inputs    | created_entity_type        | character varying        | YES         | null                                   |
| whatsapp_data_inputs    | created_entity_id          | uuid                     | YES         | null                                   |
| whatsapp_data_inputs    | error_message              | text                     | YES         | null                                   |
| whatsapp_data_inputs    | created_at                 | timestamp with time zone | YES         | now()                                  |