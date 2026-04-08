# MFD Digital Diary - Database Schema

## Overview

This document contains the complete PostgreSQL database schema for Supabase.

**Database:** PostgreSQL (via Supabase)
**Auth:** Supabase Auth (auth.users table - managed by Supabase)
**Application Tables:** All in `public` schema

---

## Table of Contents

1. [Enums (Dropdown Values)](#1-enums-dropdown-values)
2. [Tables](#2-tables)
3. [Relationships Diagram](#3-relationships-diagram)
4. [Indexes](#4-indexes)
5. [Row Level Security (RLS)](#5-row-level-security-rls)
6. [Complete SQL Migration](#6-complete-sql-migration)

---

## 1. Enums (Dropdown Values)

### 1.1 Gender
```sql
CREATE TYPE gender_type AS ENUM (
    'male',
    'female',
    'other'
);
```

### 1.2 Marital Status
```sql
CREATE TYPE marital_status_type AS ENUM (
    'single',
    'married',
    'divorced',
    'widower',
    'separated',
    'dont_know'
);
```

### 1.3 Occupation
```sql
CREATE TYPE occupation_type AS ENUM (
    'service',
    'business',
    'retired',
    'professional',
    'student',
    'self_employed',
    'housemaker',
    'dont_know'
);
```

### 1.4 Income Group (Lakhs per annum)
```sql
CREATE TYPE income_group_type AS ENUM (
    'zero',
    '1_to_2_5',
    '2_6_to_8_8',
    '8_9_to_12',
    '12_1_to_24',
    '24_1_to_48',
    '48_1_plus',
    'dont_know'
);
```

### 1.5 Age Group
```sql
CREATE TYPE age_group_type AS ENUM (
    'below_18',
    '18_to_24',
    '25_to_35',
    '36_to_45',
    '46_to_55',
    '56_plus',
    'dont_know'
);
```

### 1.6 Risk Profile
```sql
CREATE TYPE risk_profile_type AS ENUM (
    'conservative',
    'moderately_conservative',
    'moderate',
    'moderately_aggressive',
    'aggressive'
);
```

### 1.7 Source (Lead/Client)
```sql
CREATE TYPE source_type AS ENUM (
    'natural_market',
    'referral',
    'social_networking',
    'business_group',
    'marketing_activity',
    'iap',
    'cold_call',
    'social_media'
);
```

### 1.8 Lead Status
```sql
CREATE TYPE lead_status_type AS ENUM (
    'follow_up',
    'meeting_scheduled',
    'cancelled',
    'converted'
);
```

### 1.9 Task Priority
```sql
CREATE TYPE task_priority_type AS ENUM (
    'high',
    'medium',
    'low'
);
```

### 1.10 Task Medium
```sql
CREATE TYPE task_medium_type AS ENUM (
    'call',
    'whatsapp',
    'email',
    'in_person',
    'video_call'
);
```

### 1.11 Interaction Type (Touchpoint)
```sql
CREATE TYPE interaction_type AS ENUM (
    'meeting_office',
    'meeting_home',
    'cafe',
    'restaurant',
    'call',
    'video_call'
);
```

### 1.12 Touchpoint Status
```sql
CREATE TYPE touchpoint_status_type AS ENUM (
    'scheduled',
    'completed',
    'cancelled',
    'rescheduled'
);
```

### 1.13 Opportunity Stage
```sql
CREATE TYPE opportunity_stage_type AS ENUM (
    'identified',
    'inbound',
    'proposed'
);
```

### 1.14 Opportunity Type
```sql
CREATE TYPE opportunity_type AS ENUM (
    'sip',
    'lumpsum',
    'swp',
    'ncd',
    'fd',
    'life_insurance',
    'health_insurance',
    'las'
);
```

### 1.15 Opportunity Source
```sql
CREATE TYPE opportunity_source_type AS ENUM (
    'goal_planning',
    'portfolio_rebalancing',
    'client_servicing',
    'financial_activities'
);
```

### 1.16 BO Outcome (for Client BOs)
```sql
CREATE TYPE bo_outcome_type AS ENUM (
    'open',
    'won',
    'lost'
);
```

### 1.17 Goal Type
```sql
CREATE TYPE goal_type AS ENUM (
    'retirement',
    'child_education',
    'cash_surplus',
    'lifestyle',
    'car_purchase',
    'bike_purchase',
    'vacation',
    'wedding',
    'home_renovation',
    'emergency_fund',
    'wealth_creation',
    'other'
);
```

### 1.17a Lifestyle Subtype
```sql
CREATE TYPE lifestyle_subtype AS ENUM (
    'vacation_domestic',
    'vacation_international',
    'wedding',
    'home_renovation',
    'jewellery',
    'gadgets',
    'emergency_fund',
    'car',
    'bike',
    'other'
);
```

### 1.17b Vehicle Type
```sql
CREATE TYPE vehicle_type AS ENUM (
    'car',
    'bike'
);
```

### 1.18 Goal Status
```sql
CREATE TYPE goal_status_type AS ENUM (
    'active',
    'on_track',
    'behind',
    'achieved',
    'paused'
);
```

### 1.19 AUM Bracket
```sql
CREATE TYPE aum_bracket_type AS ENUM (
    'less_than_10_lakhs',
    '10_to_25_lakhs',
    '25_to_50_lakhs',
    '50_lakhs_to_1_cr',
    '1_cr_plus'
);
```

### 1.20 SIP Bracket
```sql
CREATE TYPE sip_bracket_type AS ENUM (
    'zero',
    'upto_5k',
    '5_1k_to_10k',
    '10_1k_to_25k',
    '25_1k_to_50k',
    '50_1k_to_1_lakh',
    '1_lakh_plus'
);
```

### 1.21 Client Tenure
```sql
CREATE TYPE client_tenure_type AS ENUM (
    'upto_1_year',
    '1_to_3_years',
    '3_to_8_years',
    '8_to_12_years',
    '12_plus_years'
);
```

### 1.22 Task Status
```sql
CREATE TYPE task_status_type AS ENUM (
    'pending',
    'completed',
    'cancelled',
    'carried_forward'
);
```

### 1.23 Diary Entry Type
```sql
CREATE TYPE diary_entry_type AS ENUM (
    'task',
    'touchpoint',
    'business_opportunity',
    'lead'
);
```

---

## 2. Tables

### 2.1 MFD Profiles

Stores MFD (user) profile information. Links to Supabase auth.users.

```sql
CREATE TABLE mfd_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    age INTEGER,
    gender gender_type,
    area VARCHAR(255),
    
    -- Work Info
    num_employees INTEGER DEFAULT 0,
    employee_names TEXT,
    eod_time TIME DEFAULT '18:00',
    
    -- Google Integration
    google_connected BOOLEAN DEFAULT FALSE,
    google_email VARCHAR(255),
    google_access_token TEXT,
    google_refresh_token TEXT,
    google_token_expiry TIMESTAMP WITH TIME ZONE,
    google_drive_folder_id VARCHAR(255),
    google_sheet_id VARCHAR(255),
    google_clients_folder_id VARCHAR(255),
    
    -- Settings
    notification_email BOOLEAN DEFAULT TRUE,
    notification_whatsapp BOOLEAN DEFAULT TRUE,
    notification_push BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.2 Leads

Potential clients who have not yet invested.

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    
    -- Demographics
    age_group age_group_type,
    gender gender_type,
    marital_status marital_status_type,
    occupation occupation_type,
    income_group income_group_type,
    dependants INTEGER DEFAULT 0,
    area VARCHAR(255),
    
    -- Source Info
    source source_type NOT NULL,
    source_description VARCHAR(500),
    sourced_by VARCHAR(255),
    
    -- Status & Tracking
    status lead_status_type DEFAULT 'follow_up',
    notes TEXT,
    
    -- Scheduling
    scheduled_date DATE,
    scheduled_time TIME,
    all_day BOOLEAN DEFAULT FALSE,
    
    -- Conversion
    converted_to_client_id UUID,
    conversion_date TIMESTAMP WITH TIME ZONE,
    tat_days INTEGER,  -- Turn Around Time (calculated on conversion)
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.3 Clients

Clients who have invested with the MFD.

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    area VARCHAR(255),
    
    -- Demographics
    birthdate DATE,
    age INTEGER,  -- Calculated from birthdate
    age_group age_group_type,  -- Auto-calculated
    gender gender_type NOT NULL,
    marital_status marital_status_type,
    occupation occupation_type,
    income_group income_group_type,
    dependants INTEGER DEFAULT 0,
    
    -- Investment Profile
    risk_profile risk_profile_type,
    investment_age INTEGER DEFAULT 0,  -- Years as investor
    
    -- Source Info
    source source_type NOT NULL,
    source_description VARCHAR(500),
    sourced_by VARCHAR(255),
    
    -- Product Profile (Investments)
    total_aum DECIMAL(15, 2) DEFAULT 0,
    sip DECIMAL(15, 2) DEFAULT 0,
    term_insurance DECIMAL(15, 2) DEFAULT 0,
    health_insurance DECIMAL(15, 2) DEFAULT 0,
    pa_insurance DECIMAL(15, 2) DEFAULT 0,
    swp DECIMAL(15, 2) DEFAULT 0,
    corpus DECIMAL(15, 2) DEFAULT 0,
    pms DECIMAL(15, 2) DEFAULT 0,
    aif DECIMAL(15, 2) DEFAULT 0,
    las DECIMAL(15, 2) DEFAULT 0,
    li_premium DECIMAL(15, 2) DEFAULT 0,
    ulips DECIMAL(15, 2) DEFAULT 0,
    
    -- Calculated Brackets (Auto-updated)
    aum_bracket aum_bracket_type,
    sip_bracket sip_bracket_type,
    client_tenure client_tenure_type,
    
    -- Tracking
    notes TEXT,
    touchpoints_this_year INTEGER DEFAULT 0,  -- Pre-calculated for performance
    goals_count INTEGER DEFAULT 0,  -- Pre-calculated
    
    -- Google Drive
    drive_folder_id VARCHAR(255),
    
    -- Conversion Tracking (if converted from lead)
    converted_from_lead_id UUID REFERENCES leads(id),
    conversion_date DATE,
    tat_days INTEGER,
    
    -- Client Creation
    client_creation_year INTEGER,
    client_creation_date DATE DEFAULT CURRENT_DATE,
    
    -- Soft Delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.4 Tasks

To-do items, optionally linked to client or lead.

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Linking (optional)
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Task Details
    description TEXT NOT NULL,
    medium task_medium_type,
    product_type VARCHAR(100),
    priority task_priority_type DEFAULT 'medium',
    
    -- Scheduling
    due_date DATE NOT NULL,
    due_time TIME,
    all_day BOOLEAN DEFAULT FALSE,
    
    -- Status
    status task_status_type DEFAULT 'pending',
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Flags
    is_business_opportunity BOOLEAN DEFAULT FALSE,
    
    -- Carry Forward Tracking
    original_date DATE,
    carry_forward_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.5 Touchpoints

Client/Lead interactions for relationship building.

```sql
CREATE TABLE touchpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Linking (one required)
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    
    -- Touchpoint Details
    interaction_type interaction_type NOT NULL,
    location VARCHAR(255),
    purpose TEXT,
    
    -- Scheduling
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    
    -- Status
    status touchpoint_status_type DEFAULT 'scheduled',
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Minutes of Meeting
    mom_text TEXT,
    mom_audio_url VARCHAR(500),
    mom_pdf_url VARCHAR(500),
    mom_sent_to_client BOOLEAN DEFAULT FALSE,
    mom_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint: Must have either client_id or lead_id
    CONSTRAINT touchpoint_must_have_link CHECK (
        client_id IS NOT NULL OR lead_id IS NOT NULL
    )
);
```

### 2.6 Business Opportunities

Revenue opportunities linked to client or lead.

```sql
CREATE TABLE business_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Linking (one required)
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    
    -- Opportunity Details
    expected_amount DECIMAL(15, 2),
    opportunity_stage opportunity_stage_type NOT NULL DEFAULT 'identified',
    opportunity_type opportunity_type NOT NULL,
    opportunity_source opportunity_source_type NOT NULL,
    additional_info TEXT,
    
    -- Scheduling
    due_date DATE NOT NULL,
    due_time TIME,
    
    -- Outcome (for Client BOs or manual tracking)
    outcome bo_outcome_type DEFAULT 'open',
    outcome_date DATE,
    outcome_amount DECIMAL(15, 2),  -- Actual amount (may differ from expected)
    
    -- TAT
    tat_days INTEGER,  -- Calculated on outcome
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint: Must have either client_id or lead_id
    CONSTRAINT bo_must_have_link CHECK (
        client_id IS NOT NULL OR lead_id IS NOT NULL
    )
);
```

### 2.7 Goals

Financial goals for clients.

```sql
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Goal Info
    goal_type goal_type NOT NULL,
    goal_name VARCHAR(255) NOT NULL,
    
    -- For sub-goals (education with multiple children/milestones)
    parent_goal_id UUID REFERENCES goals(id) ON DELETE CASCADE,
    child_name VARCHAR(255),  -- For education goals (child's name)
    child_current_age INTEGER,  -- For education goals
    
    -- For lifestyle goals
    lifestyle_subtype lifestyle_subtype,
    
    -- For car/bike goals
    vehicle_type vehicle_type,
    
    -- Target
    target_amount DECIMAL(15, 2) NOT NULL,
    target_date DATE,
    target_age INTEGER,
    
    -- Investment Plan
    current_investment DECIMAL(15, 2) DEFAULT 0,
    monthly_sip DECIMAL(15, 2) DEFAULT 0,
    lumpsum_investment DECIMAL(15, 2) DEFAULT 0,
    expected_return_rate DECIMAL(5, 2),
    
    -- Products (JSON array of selected products)
    products JSONB,
    
    -- Calculator Data (for recalculation)
    calculator_type VARCHAR(50),
    calculator_inputs JSONB,
    calculator_outputs JSONB,
    
    -- Progress
    progress_percent DECIMAL(5, 2) DEFAULT 0,
    status goal_status_type DEFAULT 'active',
    
    -- PDF
    pdf_url VARCHAR(500),
    pdf_generated_at TIMESTAMP WITH TIME ZONE,
    
    -- Excel Link
    excel_link VARCHAR(500),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.8 Goal History

Track changes to goals.

```sql
CREATE TABLE goal_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    
    -- Previous Values (full snapshot)
    previous_values JSONB NOT NULL,
    
    -- Change Info
    change_reason VARCHAR(255),
    changed_by UUID REFERENCES auth.users(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.9 Calculator Results

Saved calculator outputs (not necessarily linked to a goal).

```sql
CREATE TABLE calculator_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
    
    -- Calculator Info
    calculator_type VARCHAR(50) NOT NULL,
    inputs JSONB NOT NULL,
    outputs JSONB NOT NULL,
    
    -- PDF
    pdf_url VARCHAR(500),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.9a Investment Products (Master Table)

Static list of investment products with default returns. MFD can override returns when using calculators.

```sql
CREATE TABLE investment_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    default_return_rate DECIMAL(5,2) NOT NULL,
    supports_sip BOOLEAN DEFAULT TRUE,
    supports_lumpsum BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed data (run once after table creation)
INSERT INTO investment_products (name, code, default_return_rate, display_order) VALUES
('Mutual Funds', 'mutual_funds', 12.0, 1),
('Stocks', 'stocks', 12.0, 2),
('Fixed Deposit', 'fd', 7.0, 3),
('Recurring Deposit', 'rd', 7.5, 4),
('NCD / Bonds', 'ncd', 9.0, 5),
('Savings Account', 'savings', 4.0, 6),
('Provident Fund', 'pf', 8.1, 7),
('PPF', 'ppf', 7.1, 8),
('NPS', 'nps', 10.0, 9),
('Gold', 'gold', 8.0, 10);
```

### 2.9b Client Cash Flow

Stores detailed cash flow data for Cash Surplus Calculator.

```sql
CREATE TABLE client_cash_flow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- All stored as JSONB for flexibility
    insurance_premiums JSONB DEFAULT '{}',  -- {life: 5000, health: 10000, motor: 3000, other: 0}
    savings JSONB DEFAULT '{}',             -- {mutual_funds: 10000, stocks: 5000, fd: 0, ...}
    loans JSONB DEFAULT '{}',               -- {home_loan: {emi: 25000, pending: 2500000}, ...}
    expenses JSONB DEFAULT '{}',            -- {rent: 15000, grocery: 8000, transport: 5000, ...}
    income JSONB DEFAULT '{}',              -- {salary: 100000, rent_income: 0, dividend: 0, ...}
    current_investments JSONB DEFAULT '{}', -- {mutual_funds: 500000, stocks: 200000, ...}
    
    -- Calculated totals (updated when data changes)
    total_income_yearly DECIMAL(15,2) DEFAULT 0,
    total_expenses_yearly DECIMAL(15,2) DEFAULT 0,
    total_pending_loans DECIMAL(15,2) DEFAULT 0,
    cash_surplus_yearly DECIMAL(15,2) DEFAULT 0,
    cash_surplus_monthly DECIMAL(15,2) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(client_id)  -- One cash flow record per client
);
```

### 2.10 Documents

PDFs and files stored for clients.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Document Info
    name VARCHAR(255) NOT NULL,
    document_type VARCHAR(100),  -- 'goal_pdf', 'mom_pdf', 'pan', 'aadhar', etc.
    
    -- Storage
    file_url VARCHAR(500) NOT NULL,
    drive_file_id VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Related Entity
    related_entity_type VARCHAR(50),  -- 'goal', 'touchpoint', 'calculator'
    related_entity_id UUID,
    
    -- Sharing
    shared_with_client BOOLEAN DEFAULT FALSE,
    shared_at TIMESTAMP WITH TIME ZONE,
    shared_via VARCHAR(50),  -- 'whatsapp', 'email'
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.11 Call Logs

Phone call records.

```sql
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Call Info
    phone_number VARCHAR(20) NOT NULL,
    call_type VARCHAR(20) NOT NULL,  -- 'incoming', 'outgoing', 'missed'
    duration_seconds INTEGER DEFAULT 0,
    
    -- Timing
    call_time TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Notes
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.12 Quick Notes

Free-form notes not tied to any client/task.

```sql
CREATE TABLE quick_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Note Content
    content TEXT NOT NULL,
    
    -- Optional Tags
    tags TEXT[],
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.13 Campaigns

Filtered client lists for bulk actions.

```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Campaign Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Filter Criteria (stored for reference)
    filter_criteria JSONB,
    
    -- Stats
    client_count INTEGER DEFAULT 0,
    
    -- Execution
    last_executed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.14 Campaign Clients

Junction table for campaigns and clients.

```sql
CREATE TABLE campaign_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Status
    contacted BOOLEAN DEFAULT FALSE,
    contacted_at TIMESTAMP WITH TIME ZONE,
    contacted_via VARCHAR(50),
    
    -- Metadata
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint
    UNIQUE(campaign_id, client_id)
);
```

### 2.15 Notifications

User notifications.

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Notification Content
    title VARCHAR(255) NOT NULL,
    body TEXT,
    notification_type VARCHAR(50) NOT NULL,  -- 'birthday', 'task_reminder', 'followup', etc.
    
    -- Related Entity
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.16 Communication Log

Track all messages sent to clients.

```sql
CREATE TABLE communication_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Communication Details
    channel VARCHAR(50) NOT NULL,  -- 'whatsapp', 'email', 'sms'
    message_type VARCHAR(100),  -- 'birthday_greeting', 'mom_summary', 'goal_pdf', etc.
    recipient_phone VARCHAR(20),
    recipient_email VARCHAR(255),
    
    -- Content
    subject VARCHAR(255),
    body TEXT,
    attachment_url VARCHAR(500),
    
    -- Status
    status VARCHAR(50) DEFAULT 'sent',  -- 'sent', 'delivered', 'failed'
    error_message TEXT,
    
    -- Metadata
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.17 Excel Sync Log

Track sync operations with Google Sheets.

```sql
CREATE TABLE excel_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Sync Info
    sync_type VARCHAR(50) NOT NULL,  -- 'full', 'incremental', 'manual'
    sync_direction VARCHAR(50) NOT NULL,  -- 'app_to_excel', 'excel_to_app', 'bidirectional'
    
    -- Stats
    records_synced INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) NOT NULL,  -- 'success', 'partial', 'failed'
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

---

## 3. Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   auth.users (Supabase managed)                                 │
│       │                                                         │
│       │ 1:1                                                     │
│       ▼                                                         │
│   mfd_profiles                                                  │
│       │                                                         │
│       │ 1:N                                                     │
│       ▼                                                         │
│   ┌───────────────────────────────────────────────────────┐     │
│   │                                                       │     │
│   │  ┌─────────┐        ┌─────────┐                       │     │
│   │  │  leads  │───────▶│ clients │ (conversion)          │     │
│   │  └────┬────┘        └────┬────┘                       │     │
│   │       │                  │                            │     │
│   │       │ 1:N              │ 1:N                        │     │
│   │       ▼                  ▼                            │     │
│   │  ┌─────────────────────────────────────────────┐      │     │
│   │  │                                             │      │     │
│   │  │  tasks        touchpoints        goals      │      │     │
│   │  │  business_opportunities          documents  │      │     │
│   │  │  call_logs    calculator_results            │      │     │
│   │  │                                             │      │     │
│   │  └─────────────────────────────────────────────┘      │     │
│   │                                                       │     │
│   │  ┌──────────────┐    ┌──────────────┐                 │     │
│   │  │ quick_notes  │    │  campaigns   │                 │     │
│   │  └──────────────┘    └──────┬───────┘                 │     │
│   │                             │ N:M                     │     │
│   │                             ▼                         │     │
│   │                      campaign_clients                 │     │
│   │                                                       │     │
│   │  ┌──────────────┐    ┌──────────────┐                 │     │
│   │  │notifications │    │ comm_logs    │                 │     │
│   │  └──────────────┘    └──────────────┘                 │     │
│   │                                                       │     │
│   └───────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Indexes

```sql
-- ===== MFD Profiles =====
CREATE INDEX idx_mfd_profiles_user_id ON mfd_profiles(user_id);

-- ===== Leads =====
CREATE INDEX idx_leads_user_id ON leads(user_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_scheduled_date ON leads(scheduled_date);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_user_status ON leads(user_id, status);

-- ===== Clients =====
CREATE INDEX idx_clients_user_id ON clients(user_id);
CREATE INDEX idx_clients_phone ON clients(phone);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_birthdate ON clients(birthdate);
CREATE INDEX idx_clients_area ON clients(area);
CREATE INDEX idx_clients_risk_profile ON clients(risk_profile);
CREATE INDEX idx_clients_aum_bracket ON clients(aum_bracket);
CREATE INDEX idx_clients_sip_bracket ON clients(sip_bracket);
CREATE INDEX idx_clients_is_deleted ON clients(is_deleted);
CREATE INDEX idx_clients_user_deleted ON clients(user_id, is_deleted);

-- Composite indexes for opportunity queries
CREATE INDEX idx_clients_user_age ON clients(user_id, age);
CREATE INDEX idx_clients_user_marital ON clients(user_id, marital_status);
CREATE INDEX idx_clients_user_term ON clients(user_id, term_insurance);
CREATE INDEX idx_clients_user_health ON clients(user_id, health_insurance);

-- ===== Tasks =====
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_client_id ON tasks(client_id);
CREATE INDEX idx_tasks_lead_id ON tasks(lead_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_user_date ON tasks(user_id, due_date);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);

-- ===== Touchpoints =====
CREATE INDEX idx_touchpoints_user_id ON touchpoints(user_id);
CREATE INDEX idx_touchpoints_client_id ON touchpoints(client_id);
CREATE INDEX idx_touchpoints_lead_id ON touchpoints(lead_id);
CREATE INDEX idx_touchpoints_scheduled_date ON touchpoints(scheduled_date);
CREATE INDEX idx_touchpoints_status ON touchpoints(status);
CREATE INDEX idx_touchpoints_user_date ON touchpoints(user_id, scheduled_date);
CREATE INDEX idx_touchpoints_client_year ON touchpoints(client_id, scheduled_date);

-- ===== Business Opportunities =====
CREATE INDEX idx_bo_user_id ON business_opportunities(user_id);
CREATE INDEX idx_bo_client_id ON business_opportunities(client_id);
CREATE INDEX idx_bo_lead_id ON business_opportunities(lead_id);
CREATE INDEX idx_bo_due_date ON business_opportunities(due_date);
CREATE INDEX idx_bo_outcome ON business_opportunities(outcome);
CREATE INDEX idx_bo_stage ON business_opportunities(opportunity_stage);
CREATE INDEX idx_bo_user_outcome ON business_opportunities(user_id, outcome);

-- ===== Goals =====
CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_client_id ON goals(client_id);
CREATE INDEX idx_goals_type ON goals(goal_type);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_user_client ON goals(user_id, client_id);
CREATE INDEX idx_goals_parent_id ON goals(parent_goal_id);

-- ===== Investment Products =====
CREATE INDEX idx_investment_products_code ON investment_products(code);
CREATE INDEX idx_investment_products_active ON investment_products(is_active);

-- ===== Client Cash Flow =====
CREATE INDEX idx_client_cash_flow_user_id ON client_cash_flow(user_id);
CREATE INDEX idx_client_cash_flow_client_id ON client_cash_flow(client_id);

-- ===== Documents =====
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_client_id ON documents(client_id);
CREATE INDEX idx_documents_type ON documents(document_type);

-- ===== Call Logs =====
CREATE INDEX idx_call_logs_user_id ON call_logs(user_id);
CREATE INDEX idx_call_logs_client_id ON call_logs(client_id);
CREATE INDEX idx_call_logs_call_time ON call_logs(call_time);

-- ===== Quick Notes =====
CREATE INDEX idx_quick_notes_user_id ON quick_notes(user_id);
CREATE INDEX idx_quick_notes_created_at ON quick_notes(created_at);

-- ===== Campaigns =====
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);

-- ===== Notifications =====
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);

-- ===== Communication Logs =====
CREATE INDEX idx_comm_logs_user_id ON communication_logs(user_id);
CREATE INDEX idx_comm_logs_client_id ON communication_logs(client_id);
CREATE INDEX idx_comm_logs_sent_at ON communication_logs(sent_at);
```

---

## 5. Row Level Security (RLS)

All tables use RLS to ensure users can only access their own data.

```sql
-- Enable RLS on all tables
ALTER TABLE mfd_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE touchpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE calculator_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE investment_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_cash_flow ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quick_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_sync_logs ENABLE ROW LEVEL SECURITY;

-- ===== MFD Profiles Policies =====
CREATE POLICY "Users can view own profile"
    ON mfd_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
    ON mfd_profiles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
    ON mfd_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ===== Generic Policy for all other tables =====
-- (Apply this pattern to all tables with user_id)

-- LEADS
CREATE POLICY "Users can view own leads"
    ON leads FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own leads"
    ON leads FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own leads"
    ON leads FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own leads"
    ON leads FOR DELETE USING (auth.uid() = user_id);

-- CLIENTS
CREATE POLICY "Users can view own clients"
    ON clients FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own clients"
    ON clients FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own clients"
    ON clients FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own clients"
    ON clients FOR DELETE USING (auth.uid() = user_id);

-- TASKS
CREATE POLICY "Users can view own tasks"
    ON tasks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own tasks"
    ON tasks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own tasks"
    ON tasks FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own tasks"
    ON tasks FOR DELETE USING (auth.uid() = user_id);

-- TOUCHPOINTS
CREATE POLICY "Users can view own touchpoints"
    ON touchpoints FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own touchpoints"
    ON touchpoints FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own touchpoints"
    ON touchpoints FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own touchpoints"
    ON touchpoints FOR DELETE USING (auth.uid() = user_id);

-- BUSINESS OPPORTUNITIES
CREATE POLICY "Users can view own bos"
    ON business_opportunities FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own bos"
    ON business_opportunities FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own bos"
    ON business_opportunities FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own bos"
    ON business_opportunities FOR DELETE USING (auth.uid() = user_id);

-- GOALS
CREATE POLICY "Users can view own goals"
    ON goals FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own goals"
    ON goals FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own goals"
    ON goals FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own goals"
    ON goals FOR DELETE USING (auth.uid() = user_id);

-- GOAL HISTORY
CREATE POLICY "Users can view own goal history"
    ON goal_history FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM goals WHERE goals.id = goal_history.goal_id AND goals.user_id = auth.uid()
    ));
CREATE POLICY "Users can insert own goal history"
    ON goal_history FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM goals WHERE goals.id = goal_history.goal_id AND goals.user_id = auth.uid()
    ));

-- CALCULATOR RESULTS
CREATE POLICY "Users can view own calculator results"
    ON calculator_results FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own calculator results"
    ON calculator_results FOR INSERT WITH CHECK (auth.uid() = user_id);

-- INVESTMENT PRODUCTS (read-only for all authenticated users)
CREATE POLICY "Anyone can view investment products"
    ON investment_products FOR SELECT
    USING (true);

-- CLIENT CASH FLOW
CREATE POLICY "Users can view own client cash flow"
    ON client_cash_flow FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own client cash flow"
    ON client_cash_flow FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own client cash flow"
    ON client_cash_flow FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own client cash flow"
    ON client_cash_flow FOR DELETE USING (auth.uid() = user_id);

-- DOCUMENTS
CREATE POLICY "Users can view own documents"
    ON documents FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own documents"
    ON documents FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own documents"
    ON documents FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own documents"
    ON documents FOR DELETE USING (auth.uid() = user_id);

-- CALL LOGS
CREATE POLICY "Users can view own call logs"
    ON call_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own call logs"
    ON call_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- QUICK NOTES
CREATE POLICY "Users can view own quick notes"
    ON quick_notes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own quick notes"
    ON quick_notes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own quick notes"
    ON quick_notes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own quick notes"
    ON quick_notes FOR DELETE USING (auth.uid() = user_id);

-- CAMPAIGNS
CREATE POLICY "Users can view own campaigns"
    ON campaigns FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own campaigns"
    ON campaigns FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own campaigns"
    ON campaigns FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own campaigns"
    ON campaigns FOR DELETE USING (auth.uid() = user_id);

-- CAMPAIGN CLIENTS
CREATE POLICY "Users can view own campaign clients"
    ON campaign_clients FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM campaigns WHERE campaigns.id = campaign_clients.campaign_id AND campaigns.user_id = auth.uid()
    ));
CREATE POLICY "Users can insert own campaign clients"
    ON campaign_clients FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM campaigns WHERE campaigns.id = campaign_clients.campaign_id AND campaigns.user_id = auth.uid()
    ));
CREATE POLICY "Users can delete own campaign clients"
    ON campaign_clients FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM campaigns WHERE campaigns.id = campaign_clients.campaign_id AND campaigns.user_id = auth.uid()
    ));

-- NOTIFICATIONS
CREATE POLICY "Users can view own notifications"
    ON notifications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own notifications"
    ON notifications FOR UPDATE USING (auth.uid() = user_id);

-- COMMUNICATION LOGS
CREATE POLICY "Users can view own comm logs"
    ON communication_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own comm logs"
    ON communication_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- EXCEL SYNC LOGS
CREATE POLICY "Users can view own sync logs"
    ON excel_sync_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own sync logs"
    ON excel_sync_logs FOR INSERT WITH CHECK (auth.uid() = user_id);
```

---

## 6. Complete SQL Migration

This is the complete SQL to run in Supabase SQL Editor.

```sql
-- ============================================================
-- MFD DIGITAL DIARY - COMPLETE DATABASE MIGRATION
-- ============================================================
-- Run this in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- PART 1: ENUMS
-- ============================================================

CREATE TYPE gender_type AS ENUM ('male', 'female', 'other');

CREATE TYPE marital_status_type AS ENUM (
    'single', 'married', 'divorced', 'widower', 'separated', 'dont_know'
);

CREATE TYPE occupation_type AS ENUM (
    'service', 'business', 'retired', 'professional', 
    'student', 'self_employed', 'housemaker', 'dont_know'
);

CREATE TYPE income_group_type AS ENUM (
    'zero', '1_to_2_5', '2_6_to_8_8', '8_9_to_12',
    '12_1_to_24', '24_1_to_48', '48_1_plus', 'dont_know'
);

CREATE TYPE age_group_type AS ENUM (
    'below_18', '18_to_24', '25_to_35', '36_to_45', '46_to_55', '56_plus', 'dont_know'
);

CREATE TYPE risk_profile_type AS ENUM (
    'conservative', 'moderately_conservative', 'moderate', 
    'moderately_aggressive', 'aggressive'
);

CREATE TYPE source_type AS ENUM (
    'natural_market', 'referral', 'social_networking', 'business_group',
    'marketing_activity', 'iap', 'cold_call', 'social_media'
);

CREATE TYPE lead_status_type AS ENUM (
    'follow_up', 'meeting_scheduled', 'cancelled', 'converted'
);

CREATE TYPE task_priority_type AS ENUM ('high', 'medium', 'low');

CREATE TYPE task_status_type AS ENUM (
    'pending', 'completed', 'cancelled', 'carried_forward'
);

CREATE TYPE task_medium_type AS ENUM (
    'call', 'whatsapp', 'email', 'in_person', 'video_call'
);

CREATE TYPE interaction_type AS ENUM (
    'meeting_office', 'meeting_home', 'cafe', 'restaurant', 'call', 'video_call'
);

CREATE TYPE touchpoint_status_type AS ENUM (
    'scheduled', 'completed', 'cancelled', 'rescheduled'
);

CREATE TYPE opportunity_stage_type AS ENUM ('identified', 'inbound', 'proposed');

CREATE TYPE opportunity_type AS ENUM (
    'sip', 'lumpsum', 'swp', 'ncd', 'fd', 'life_insurance', 'health_insurance', 'las'
);

CREATE TYPE opportunity_source_type AS ENUM (
    'goal_planning', 'portfolio_rebalancing', 'client_servicing', 'financial_activities'
);

CREATE TYPE bo_outcome_type AS ENUM ('open', 'won', 'lost');

CREATE TYPE goal_type AS ENUM (
    'retirement', 'child_education', 'cash_surplus', 'lifestyle', 'other'
);

CREATE TYPE goal_status_type AS ENUM (
    'active', 'on_track', 'behind', 'achieved', 'paused'
);

CREATE TYPE aum_bracket_type AS ENUM (
    'less_than_10_lakhs', '10_to_25_lakhs', '25_to_50_lakhs', 
    '50_lakhs_to_1_cr', '1_cr_plus'
);

CREATE TYPE sip_bracket_type AS ENUM (
    'zero', 'upto_5k', '5_1k_to_10k', '10_1k_to_25k',
    '25_1k_to_50k', '50_1k_to_1_lakh', '1_lakh_plus'
);

CREATE TYPE client_tenure_type AS ENUM (
    'upto_1_year', '1_to_3_years', '3_to_8_years', '8_to_12_years', '12_plus_years'
);

-- ============================================================
-- PART 2: TABLES
-- ============================================================

-- MFD Profiles
CREATE TABLE mfd_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    age INTEGER,
    gender gender_type,
    area VARCHAR(255),
    num_employees INTEGER DEFAULT 0,
    employee_names TEXT,
    eod_time TIME DEFAULT '18:00',
    google_connected BOOLEAN DEFAULT FALSE,
    google_email VARCHAR(255),
    google_access_token TEXT,
    google_refresh_token TEXT,
    google_token_expiry TIMESTAMP WITH TIME ZONE,
    google_drive_folder_id VARCHAR(255),
    google_sheet_id VARCHAR(255),
    google_clients_folder_id VARCHAR(255),
    notification_email BOOLEAN DEFAULT TRUE,
    notification_whatsapp BOOLEAN DEFAULT TRUE,
    notification_push BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Leads
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    age_group age_group_type,
    gender gender_type,
    marital_status marital_status_type,
    occupation occupation_type,
    income_group income_group_type,
    dependants INTEGER DEFAULT 0,
    area VARCHAR(255),
    source source_type NOT NULL,
    source_description VARCHAR(500),
    sourced_by VARCHAR(255),
    status lead_status_type DEFAULT 'follow_up',
    notes TEXT,
    scheduled_date DATE,
    scheduled_time TIME,
    all_day BOOLEAN DEFAULT FALSE,
    converted_to_client_id UUID,
    conversion_date TIMESTAMP WITH TIME ZONE,
    tat_days INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Clients
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    area VARCHAR(255),
    birthdate DATE,
    age INTEGER,
    age_group age_group_type,
    gender gender_type NOT NULL,
    marital_status marital_status_type,
    occupation occupation_type,
    income_group income_group_type,
    dependants INTEGER DEFAULT 0,
    risk_profile risk_profile_type,
    investment_age INTEGER DEFAULT 0,
    source source_type NOT NULL,
    source_description VARCHAR(500),
    sourced_by VARCHAR(255),
    total_aum DECIMAL(15, 2) DEFAULT 0,
    sip DECIMAL(15, 2) DEFAULT 0,
    term_insurance DECIMAL(15, 2) DEFAULT 0,
    health_insurance DECIMAL(15, 2) DEFAULT 0,
    pa_insurance DECIMAL(15, 2) DEFAULT 0,
    swp DECIMAL(15, 2) DEFAULT 0,
    corpus DECIMAL(15, 2) DEFAULT 0,
    pms DECIMAL(15, 2) DEFAULT 0,
    aif DECIMAL(15, 2) DEFAULT 0,
    las DECIMAL(15, 2) DEFAULT 0,
    li_premium DECIMAL(15, 2) DEFAULT 0,
    ulips DECIMAL(15, 2) DEFAULT 0,
    aum_bracket aum_bracket_type,
    sip_bracket sip_bracket_type,
    client_tenure client_tenure_type,
    notes TEXT,
    touchpoints_this_year INTEGER DEFAULT 0,
    goals_count INTEGER DEFAULT 0,
    drive_folder_id VARCHAR(255),
    converted_from_lead_id UUID REFERENCES leads(id),
    conversion_date DATE,
    tat_days INTEGER,
    client_creation_year INTEGER,
    client_creation_date DATE DEFAULT CURRENT_DATE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    medium task_medium_type,
    product_type VARCHAR(100),
    priority task_priority_type DEFAULT 'medium',
    due_date DATE NOT NULL,
    due_time TIME,
    all_day BOOLEAN DEFAULT FALSE,
    status task_status_type DEFAULT 'pending',
    completed_at TIMESTAMP WITH TIME ZONE,
    is_business_opportunity BOOLEAN DEFAULT FALSE,
    original_date DATE,
    carry_forward_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Touchpoints
CREATE TABLE touchpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    interaction_type interaction_type NOT NULL,
    location VARCHAR(255),
    purpose TEXT,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    status touchpoint_status_type DEFAULT 'scheduled',
    completed_at TIMESTAMP WITH TIME ZONE,
    mom_text TEXT,
    mom_audio_url VARCHAR(500),
    mom_pdf_url VARCHAR(500),
    mom_sent_to_client BOOLEAN DEFAULT FALSE,
    mom_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT touchpoint_must_have_link CHECK (client_id IS NOT NULL OR lead_id IS NOT NULL)
);

-- Business Opportunities
CREATE TABLE business_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    expected_amount DECIMAL(15, 2),
    opportunity_stage opportunity_stage_type NOT NULL DEFAULT 'identified',
    opportunity_type opportunity_type NOT NULL,
    opportunity_source opportunity_source_type NOT NULL,
    additional_info TEXT,
    due_date DATE NOT NULL,
    due_time TIME,
    outcome bo_outcome_type DEFAULT 'open',
    outcome_date DATE,
    outcome_amount DECIMAL(15, 2),
    tat_days INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT bo_must_have_link CHECK (client_id IS NOT NULL OR lead_id IS NOT NULL)
);

-- Goals
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    goal_type goal_type NOT NULL,
    goal_name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL,
    target_date DATE,
    target_age INTEGER,
    current_investment DECIMAL(15, 2) DEFAULT 0,
    monthly_sip DECIMAL(15, 2) DEFAULT 0,
    lumpsum_investment DECIMAL(15, 2) DEFAULT 0,
    expected_return_rate DECIMAL(5, 2),
    products JSONB,
    calculator_type VARCHAR(50),
    calculator_inputs JSONB,
    calculator_outputs JSONB,
    progress_percent DECIMAL(5, 2) DEFAULT 0,
    status goal_status_type DEFAULT 'active',
    pdf_url VARCHAR(500),
    pdf_generated_at TIMESTAMP WITH TIME ZONE,
    excel_link VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Goal History
CREATE TABLE goal_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    previous_values JSONB NOT NULL,
    change_reason VARCHAR(255),
    changed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calculator Results
CREATE TABLE calculator_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
    calculator_type VARCHAR(50) NOT NULL,
    inputs JSONB NOT NULL,
    outputs JSONB NOT NULL,
    pdf_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    document_type VARCHAR(100),
    file_url VARCHAR(500) NOT NULL,
    drive_file_id VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    shared_with_client BOOLEAN DEFAULT FALSE,
    shared_at TIMESTAMP WITH TIME ZONE,
    shared_via VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Call Logs
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    phone_number VARCHAR(20) NOT NULL,
    call_type VARCHAR(20) NOT NULL,
    duration_seconds INTEGER DEFAULT 0,
    call_time TIMESTAMP WITH TIME ZONE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quick Notes
CREATE TABLE quick_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    filter_criteria JSONB,
    client_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaign Clients
CREATE TABLE campaign_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    contacted BOOLEAN DEFAULT FALSE,
    contacted_at TIMESTAMP WITH TIME ZONE,
    contacted_via VARCHAR(50),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(campaign_id, client_id)
);

-- Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    notification_type VARCHAR(50) NOT NULL,
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Communication Logs
CREATE TABLE communication_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    channel VARCHAR(50) NOT NULL,
    message_type VARCHAR(100),
    recipient_phone VARCHAR(20),
    recipient_email VARCHAR(255),
    subject VARCHAR(255),
    body TEXT,
    attachment_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'sent',
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Excel Sync Logs
CREATE TABLE excel_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL,
    sync_direction VARCHAR(50) NOT NULL,
    records_synced INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================
-- PART 3: INDEXES
-- ============================================================

-- MFD Profiles
CREATE INDEX idx_mfd_profiles_user_id ON mfd_profiles(user_id);

-- Leads
CREATE INDEX idx_leads_user_id ON leads(user_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_scheduled_date ON leads(scheduled_date);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_user_status ON leads(user_id, status);

-- Clients
CREATE INDEX idx_clients_user_id ON clients(user_id);
CREATE INDEX idx_clients_phone ON clients(phone);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_birthdate ON clients(birthdate);
CREATE INDEX idx_clients_area ON clients(area);
CREATE INDEX idx_clients_is_deleted ON clients(is_deleted);
CREATE INDEX idx_clients_user_deleted ON clients(user_id, is_deleted);
CREATE INDEX idx_clients_user_age ON clients(user_id, age);
CREATE INDEX idx_clients_user_marital ON clients(user_id, marital_status);
CREATE INDEX idx_clients_user_term ON clients(user_id, term_insurance);
CREATE INDEX idx_clients_user_health ON clients(user_id, health_insurance);

-- Tasks
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_client_id ON tasks(client_id);
CREATE INDEX idx_tasks_lead_id ON tasks(lead_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_user_date ON tasks(user_id, due_date);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);

-- Touchpoints
CREATE INDEX idx_touchpoints_user_id ON touchpoints(user_id);
CREATE INDEX idx_touchpoints_client_id ON touchpoints(client_id);
CREATE INDEX idx_touchpoints_lead_id ON touchpoints(lead_id);
CREATE INDEX idx_touchpoints_scheduled_date ON touchpoints(scheduled_date);
CREATE INDEX idx_touchpoints_status ON touchpoints(status);
CREATE INDEX idx_touchpoints_user_date ON touchpoints(user_id, scheduled_date);
CREATE INDEX idx_touchpoints_client_year ON touchpoints(client_id, scheduled_date);

-- Business Opportunities
CREATE INDEX idx_bo_user_id ON business_opportunities(user_id);
CREATE INDEX idx_bo_client_id ON business_opportunities(client_id);
CREATE INDEX idx_bo_lead_id ON business_opportunities(lead_id);
CREATE INDEX idx_bo_due_date ON business_opportunities(due_date);
CREATE INDEX idx_bo_outcome ON business_opportunities(outcome);
CREATE INDEX idx_bo_user_outcome ON business_opportunities(user_id, outcome);

-- Goals
CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_client_id ON goals(client_id);
CREATE INDEX idx_goals_type ON goals(goal_type);
CREATE INDEX idx_goals_status ON goals(status);

-- Documents
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_client_id ON documents(client_id);

-- Call Logs
CREATE INDEX idx_call_logs_user_id ON call_logs(user_id);
CREATE INDEX idx_call_logs_client_id ON call_logs(client_id);
CREATE INDEX idx_call_logs_call_time ON call_logs(call_time);

-- Quick Notes
CREATE INDEX idx_quick_notes_user_id ON quick_notes(user_id);

-- Campaigns
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);

-- Notifications
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);

-- Communication Logs
CREATE INDEX idx_comm_logs_user_id ON communication_logs(user_id);
CREATE INDEX idx_comm_logs_client_id ON communication_logs(client_id);

-- ============================================================
-- PART 4: ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS
ALTER TABLE mfd_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE touchpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE calculator_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quick_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_sync_logs ENABLE ROW LEVEL SECURITY;

-- MFD Profiles Policies
CREATE POLICY "mfd_profiles_select" ON mfd_profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "mfd_profiles_insert" ON mfd_profiles FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "mfd_profiles_update" ON mfd_profiles FOR UPDATE USING (auth.uid() = user_id);

-- Leads Policies
CREATE POLICY "leads_select" ON leads FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "leads_insert" ON leads FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "leads_update" ON leads FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "leads_delete" ON leads FOR DELETE USING (auth.uid() = user_id);

-- Clients Policies
CREATE POLICY "clients_select" ON clients FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "clients_insert" ON clients FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "clients_update" ON clients FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "clients_delete" ON clients FOR DELETE USING (auth.uid() = user_id);

-- Tasks Policies
CREATE POLICY "tasks_select" ON tasks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "tasks_insert" ON tasks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "tasks_update" ON tasks FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "tasks_delete" ON tasks FOR DELETE USING (auth.uid() = user_id);

-- Touchpoints Policies
CREATE POLICY "touchpoints_select" ON touchpoints FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "touchpoints_insert" ON touchpoints FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "touchpoints_update" ON touchpoints FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "touchpoints_delete" ON touchpoints FOR DELETE USING (auth.uid() = user_id);

-- Business Opportunities Policies
CREATE POLICY "bo_select" ON business_opportunities FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "bo_insert" ON business_opportunities FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "bo_update" ON business_opportunities FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "bo_delete" ON business_opportunities FOR DELETE USING (auth.uid() = user_id);

-- Goals Policies
CREATE POLICY "goals_select" ON goals FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "goals_insert" ON goals FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "goals_update" ON goals FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "goals_delete" ON goals FOR DELETE USING (auth.uid() = user_id);

-- Goal History Policies
CREATE POLICY "goal_history_select" ON goal_history FOR SELECT
    USING (EXISTS (SELECT 1 FROM goals WHERE goals.id = goal_history.goal_id AND goals.user_id = auth.uid()));
CREATE POLICY "goal_history_insert" ON goal_history FOR INSERT
    WITH CHECK (EXISTS (SELECT 1 FROM goals WHERE goals.id = goal_history.goal_id AND goals.user_id = auth.uid()));

-- Calculator Results Policies
CREATE POLICY "calc_results_select" ON calculator_results FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "calc_results_insert" ON calculator_results FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Documents Policies
CREATE POLICY "documents_select" ON documents FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "documents_insert" ON documents FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "documents_update" ON documents FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "documents_delete" ON documents FOR DELETE USING (auth.uid() = user_id);

-- Call Logs Policies
CREATE POLICY "call_logs_select" ON call_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "call_logs_insert" ON call_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Quick Notes Policies
CREATE POLICY "quick_notes_select" ON quick_notes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "quick_notes_insert" ON quick_notes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "quick_notes_update" ON quick_notes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "quick_notes_delete" ON quick_notes FOR DELETE USING (auth.uid() = user_id);

-- Campaigns Policies
CREATE POLICY "campaigns_select" ON campaigns FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "campaigns_insert" ON campaigns FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "campaigns_update" ON campaigns FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "campaigns_delete" ON campaigns FOR DELETE USING (auth.uid() = user_id);

-- Campaign Clients Policies
CREATE POLICY "campaign_clients_select" ON campaign_clients FOR SELECT
    USING (EXISTS (SELECT 1 FROM campaigns WHERE campaigns.id = campaign_clients.campaign_id AND campaigns.user_id = auth.uid()));
CREATE POLICY "campaign_clients_insert" ON campaign_clients FOR INSERT
    WITH CHECK (EXISTS (SELECT 1 FROM campaigns WHERE campaigns.id = campaign_clients.campaign_id AND campaigns.user_id = auth.uid()));
CREATE POLICY "campaign_clients_delete" ON campaign_clients FOR DELETE
    USING (EXISTS (SELECT 1 FROM campaigns WHERE campaigns.id = campaign_clients.campaign_id AND campaigns.user_id = auth.uid()));

-- Notifications Policies
CREATE POLICY "notifications_select" ON notifications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "notifications_update" ON notifications FOR UPDATE USING (auth.uid() = user_id);

-- Communication Logs Policies
CREATE POLICY "comm_logs_select" ON communication_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "comm_logs_insert" ON communication_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Excel Sync Logs Policies
CREATE POLICY "sync_logs_select" ON excel_sync_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "sync_logs_insert" ON excel_sync_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- PART 5: HELPER FUNCTIONS
-- ============================================================

-- Function to calculate age from birthdate
CREATE OR REPLACE FUNCTION calculate_age(birthdate DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM age(CURRENT_DATE, birthdate));
END;
$$ LANGUAGE plpgsql;

-- Function to determine age group
CREATE OR REPLACE FUNCTION get_age_group(age INTEGER)
RETURNS age_group_type AS $$
BEGIN
    IF age < 18 THEN RETURN 'below_18';
    ELSIF age <= 24 THEN RETURN '18_to_24';
    ELSIF age <= 35 THEN RETURN '25_to_35';
    ELSIF age <= 45 THEN RETURN '36_to_45';
    ELSIF age <= 55 THEN RETURN '46_to_55';
    ELSE RETURN '56_plus';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to determine AUM bracket
CREATE OR REPLACE FUNCTION get_aum_bracket(aum DECIMAL)
RETURNS aum_bracket_type AS $$
BEGIN
    IF aum < 1000000 THEN RETURN 'less_than_10_lakhs';
    ELSIF aum < 2500000 THEN RETURN '10_to_25_lakhs';
    ELSIF aum < 5000000 THEN RETURN '25_to_50_lakhs';
    ELSIF aum < 10000000 THEN RETURN '50_lakhs_to_1_cr';
    ELSE RETURN '1_cr_plus';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to determine SIP bracket
CREATE OR REPLACE FUNCTION get_sip_bracket(sip DECIMAL)
RETURNS sip_bracket_type AS $$
BEGIN
    IF sip = 0 THEN RETURN 'zero';
    ELSIF sip <= 5000 THEN RETURN 'upto_5k';
    ELSIF sip <= 10000 THEN RETURN '5_1k_to_10k';
    ELSIF sip <= 25000 THEN RETURN '10_1k_to_25k';
    ELSIF sip <= 50000 THEN RETURN '25_1k_to_50k';
    ELSIF sip <= 100000 THEN RETURN '50_1k_to_1_lakh';
    ELSE RETURN '1_lakh_plus';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to determine client tenure
CREATE OR REPLACE FUNCTION get_client_tenure(creation_date DATE)
RETURNS client_tenure_type AS $$
DECLARE
    years INTEGER;
BEGIN
    years := EXTRACT(YEAR FROM age(CURRENT_DATE, creation_date));
    IF years < 1 THEN RETURN 'upto_1_year';
    ELSIF years < 3 THEN RETURN '1_to_3_years';
    ELSIF years < 8 THEN RETURN '3_to_8_years';
    ELSIF years < 12 THEN RETURN '8_to_12_years';
    ELSE RETURN '12_plus_years';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update client calculated fields
CREATE OR REPLACE FUNCTION update_client_calculated_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate age from birthdate
    IF NEW.birthdate IS NOT NULL THEN
        NEW.age := calculate_age(NEW.birthdate);
        NEW.age_group := get_age_group(NEW.age);
    END IF;
    
    -- Calculate brackets
    NEW.aum_bracket := get_aum_bracket(NEW.total_aum);
    NEW.sip_bracket := get_sip_bracket(NEW.sip);
    NEW.client_tenure := get_client_tenure(COALESCE(NEW.client_creation_date, NEW.created_at::DATE));
    
    -- Set client creation year
    IF NEW.client_creation_year IS NULL THEN
        NEW.client_creation_year := EXTRACT(YEAR FROM COALESCE(NEW.client_creation_date, NEW.created_at));
    END IF;
    
    -- Update timestamp
    NEW.updated_at := NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_client_fields
    BEFORE INSERT OR UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_client_calculated_fields();

-- Trigger to update updated_at on all tables
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_touchpoints_updated_at BEFORE UPDATE ON touchpoints FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_bo_updated_at BEFORE UPDATE ON business_opportunities FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_goals_updated_at BEFORE UPDATE ON goals FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_quick_notes_updated_at BEFORE UPDATE ON quick_notes FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_campaigns_updated_at BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_mfd_profiles_updated_at BEFORE UPDATE ON mfd_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
```

---

## Summary

### Tables Created: 17
1. mfd_profiles
2. leads
3. clients
4. tasks
5. touchpoints
6. business_opportunities
7. goals
8. goal_history
9. calculator_results
10. documents
11. call_logs
12. quick_notes
13. campaigns
14. campaign_clients
15. notifications
16. communication_logs
17. excel_sync_logs

### Enums Created: 23
All dropdown values as PostgreSQL enums for type safety.

### Features
- ✅ All indexes for fast queries
- ✅ Row Level Security (RLS) for data isolation
- ✅ Auto-calculated fields (age, brackets, tenure)
- ✅ Triggers for updated_at timestamps
- ✅ Helper functions for calculations
- ✅ Foreign key relationships
- ✅ Constraints for data integrity

---

## How to Use

1. Go to Supabase Dashboard
2. Click "SQL Editor"
3. Create new query
4. Copy-paste the complete SQL from Section 6
5. Click "Run"
6. All tables, indexes, and policies will be created

---
