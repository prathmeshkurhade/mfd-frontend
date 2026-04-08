# MFD Digital Diary - API Endpoints

## Overview

**Base URL:** `https://api.yourapp.com/api/v1`
**Auth:** JWT Bearer Token (from Supabase Auth)
**Format:** JSON

All endpoints (except health check) require authentication via Bearer token in header:
```
Authorization: Bearer <supabase_jwt_token>
```

---

## Authentication Note

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   AUTH IS HANDLED BY SUPABASE DIRECTLY                          │
│                                                                 │
│   Flutter calls Supabase SDK for:                               │
│   • Register (supabase.auth.signUp)                             │
│   • Login (supabase.auth.signInWithPassword)                    │
│   • OTP (supabase.auth.signInWithOtp)                           │
│   • Logout (supabase.auth.signOut)                              │
│   • Password Reset (supabase.auth.resetPasswordForEmail)        │
│                                                                 │
│   NO FastAPI endpoints needed for auth!                         │
│                                                                 │
│   FastAPI only VALIDATES the JWT token from Supabase.           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Table of Contents

1. [Health Check](#1-health-check-1-endpoint)
2. [Profile](#2-profile-8-endpoints)
3. [Dashboard](#3-dashboard-5-endpoints)
4. [Clients](#4-clients-17-endpoints)
5. [Leads](#5-leads-11-endpoints)
6. [Tasks](#6-tasks-12-endpoints)
7. [Touchpoints](#7-touchpoints-13-endpoints)
8. [Business Opportunities](#8-business-opportunities-10-endpoints)
9. [Goals](#9-goals-12-endpoints)
10. [Calculators](#10-calculators-14-endpoints)
11. [Documents](#11-documents-6-endpoints)
12. [Google Drive](#12-google-drive-6-endpoints)
13. [Google Sheets Sync](#13-google-sheets-sync-6-endpoints)
14. [Notifications](#14-notifications-5-endpoints)
15. [WhatsApp](#15-whatsapp-5-endpoints)
16. [Email](#16-email-3-endpoints)
17. [OCR & Voice](#17-ocr--voice-6-endpoints)
18. [Campaigns](#18-campaigns-7-endpoints)
19. [Analytics & Opportunities](#19-analytics--opportunities-5-endpoints)
20. [Market Analysis](#20-market-analysis-4-endpoints)
21. [Quick Notes](#21-quick-notes-4-endpoints)
22. [Call Logs](#22-call-logs-3-endpoints)
23. [Search](#23-search-3-endpoints)
24. [Diary Views](#24-diary-views-6-endpoints)
25. [Data Import](#25-data-import-5-endpoints)

**Total: ~171 Endpoints**

---

## 1. Health Check (1 Endpoint)

### 1.1 Health Check
```
GET /health
```
**Auth:** No

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2026-01-26T10:00:00Z",
    "version": "1.0.0"
}
```

---

## 2. Profile (8 Endpoints)

### 2.1 Get Profile
```
GET /profile
```
**Auth:** Yes

**Response:**
```json
{
    "id": "uuid",
    "user_id": "uuid",
    "name": "Rajesh Kumar",
    "phone": "+919876543210",
    "age": 38,
    "gender": "male",
    "area": "Thane",
    "num_employees": 2,
    "employee_names": "Amit, Priya",
    "eod_time": "18:00",
    "google_connected": true,
    "google_email": "rajesh@gmail.com",
    "notification_email": true,
    "notification_whatsapp": true,
    "notification_push": true,
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-20T10:00:00Z"
}
```

---

### 2.2 Complete Registration
```
POST /profile/complete
```
**Auth:** Yes

**Request:**
```json
{
    "name": "Rajesh Kumar",
    "phone": "+919876543210",
    "age": 38,
    "gender": "male",
    "area": "Thane",
    "num_employees": 2,
    "employee_names": "Amit, Priya",
    "eod_time": "18:00"
}
```

**Response:**
```json
{
    "id": "uuid",
    "user_id": "uuid",
    "name": "Rajesh Kumar",
    "message": "Profile created successfully"
}
```

---

### 2.3 Update Profile
```
PUT /profile
```
**Auth:** Yes

**Request:** (partial update allowed)
```json
{
    "name": "Rajesh Kumar",
    "area": "Thane West",
    "eod_time": "19:00"
}
```

**Response:**
```json
{
    "id": "uuid",
    "message": "Profile updated successfully"
}
```

---

### 2.4 Update Notification Settings
```
PUT /profile/notifications
```
**Auth:** Yes

**Request:**
```json
{
    "notification_email": true,
    "notification_whatsapp": true,
    "notification_push": false
}
```

**Response:**
```json
{
    "message": "Notification settings updated"
}
```

---

### 2.5 Start Google OAuth
```
GET /profile/google/connect
```
**Auth:** Yes

**Response:**
```json
{
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&scope=..."
}
```

---

### 2.6 Google OAuth Callback
```
GET /profile/google/callback?code={code}&state={state}
```
**Auth:** No (state contains user_id)

**Response:** Redirects to app with success/failure status

---

### 2.7 Disconnect Google
```
DELETE /profile/google/disconnect
```
**Auth:** Yes

**Response:**
```json
{
    "message": "Google account disconnected"
}
```

---

### 2.8 Get Google Connection Status
```
GET /profile/google/status
```
**Auth:** Yes

**Response:**
```json
{
    "connected": true,
    "email": "rajesh@gmail.com",
    "drive_folder_id": "1ABC...",
    "sheet_id": "1XYZ..."
}
```

---

## 3. Dashboard (5 Endpoints)

### 3.1 Get Dashboard Summary
```
GET /dashboard
```
**Auth:** Yes

**Response:**
```json
{
    "summary": {
        "total_aum": 15000000,
        "total_sip": 250000,
        "total_clients": 150,
        "total_leads": 45,
        "aum_change_percent": 5.2,
        "sip_change_percent": 3.1
    },
    "today": {
        "tasks": 5,
        "touchpoints": 3,
        "business_opportunities": 2,
        "leads_followup": 4,
        "birthdays": 2
    },
    "sync_status": {
        "status": "healthy",
        "last_sync": "2026-01-26T09:00:00Z"
    }
}
```

---

### 3.2 Get Today's Birthdays
```
GET /dashboard/birthdays?date={date}
```
**Auth:** Yes

**Response:**
```json
{
    "date": "2026-01-26",
    "birthdays": [
        {
            "id": "uuid",
            "name": "Amit Sharma",
            "type": "client",
            "phone": "+919123456789",
            "age_turning": 41,
            "greeting_sent": false
        }
    ]
}
```

---

### 3.3 Get Dashboard Stats
```
GET /dashboard/stats?period={period}
```
**Auth:** Yes

**Query Params:**
- `period`: "week" | "month" | "quarter" | "year"

**Response:**
```json
{
    "period": "month",
    "stats": {
        "new_clients": 5,
        "leads_converted": 3,
        "tasks_completed": 45,
        "touchpoints_completed": 20,
        "bo_won": 8,
        "bo_lost": 2,
        "aum_added": 500000,
        "sip_added": 25000
    }
}
```

---

### 3.4 Get Today's Schedule
```
GET /dashboard/schedule?date={date}
```
**Auth:** Yes

**Response:**
```json
{
    "date": "2026-01-26",
    "schedule": [
        {
            "id": "uuid",
            "type": "task",
            "time": "09:00",
            "description": "Call Amit about SIP",
            "client_name": "Amit Sharma",
            "priority": "high",
            "status": "pending"
        },
        {
            "id": "uuid",
            "type": "touchpoint",
            "time": "14:00",
            "description": "Portfolio Review",
            "client_name": "Priya Patel",
            "interaction_type": "meeting_office",
            "status": "scheduled"
        }
    ]
}
```

---

### 3.5 Get 80-20 Summary
```
GET /dashboard/80-20
```
**Auth:** Yes

**Response:**
```json
{
    "aum": {
        "top_20_percent_clients": 30,
        "top_20_percent_aum": 12000000,
        "top_20_percent_share": 80
    },
    "sip": {
        "top_20_percent_clients": 30,
        "top_20_percent_sip": 200000,
        "top_20_percent_share": 80
    }
}
```

---

## 4. Clients (17 Endpoints)

### 4.1 List Clients
```
GET /clients
```
**Auth:** Yes

**Query Params:**
- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `search`: Search by name, phone, email
- `area`: Filter by area
- `age_group`: Filter by age group
- `aum_bracket`: Filter by AUM bracket
- `sip_bracket`: Filter by SIP bracket
- `risk_profile`: Filter by risk profile
- `sort_by`: "name" | "created_at" | "total_aum" | "sip"
- `sort_order`: "asc" | "desc"

**Response:**
```json
{
    "clients": [
        {
            "id": "uuid",
            "name": "Amit Sharma",
            "phone": "+919123456789",
            "email": "amit@example.com",
            "area": "Thane",
            "age": 40,
            "total_aum": 500000,
            "sip": 15000,
            "aum_bracket": "less_than_10_lakhs",
            "sip_bracket": "10_1k_to_25k",
            "risk_profile": "moderate",
            "touchpoints_this_year": 3,
            "goals_count": 2
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 150,
        "total_pages": 8
    }
}
```

---

### 4.2 Get Client by ID
```
GET /clients/{client_id}
```
**Auth:** Yes

**Response:**
```json
{
    "id": "uuid",
    "name": "Amit Sharma",
    "phone": "+919123456789",
    "email": "amit@example.com",
    "address": "123 Main St, Thane",
    "area": "Thane",
    "birthdate": "1985-03-15",
    "age": 40,
    "age_group": "36_to_45",
    "gender": "male",
    "marital_status": "married",
    "occupation": "service",
    "income_group": "12_1_to_24",
    "dependants": 2,
    "risk_profile": "moderate",
    "investment_age": 5,
    "source": "referral",
    "source_description": "Referred by Priya",
    "sourced_by": "Self",
    "total_aum": 500000,
    "sip": 15000,
    "term_insurance": 10000000,
    "health_insurance": 500000,
    "pa_insurance": 0,
    "swp": 0,
    "corpus": 0,
    "pms": 0,
    "aif": 0,
    "las": 0,
    "li_premium": 0,
    "ulips": 0,
    "aum_bracket": "less_than_10_lakhs",
    "sip_bracket": "10_1k_to_25k",
    "client_tenure": "1_to_3_years",
    "notes": "Interested in retirement planning",
    "touchpoints_this_year": 3,
    "goals_count": 2,
    "drive_folder_id": "1ABC...",
    "converted_from_lead_id": "uuid",
    "conversion_date": "2024-03-15",
    "tat_days": 15,
    "client_creation_year": 2024,
    "client_creation_date": "2024-03-15",
    "created_at": "2024-03-15T10:00:00Z",
    "updated_at": "2026-01-20T10:00:00Z"
}
```

---

### 4.3 Create Client
```
POST /clients
```
**Auth:** Yes

**Request:**
```json
{
    "name": "Amit Sharma",
    "phone": "+919123456789",
    "email": "amit@example.com",
    "address": "123 Main St, Thane",
    "area": "Thane",
    "birthdate": "1985-03-15",
    "gender": "male",
    "marital_status": "married",
    "occupation": "service",
    "income_group": "12_1_to_24",
    "dependants": 2,
    "risk_profile": "moderate",
    "source": "referral",
    "source_description": "Referred by Priya",
    "total_aum": 500000,
    "sip": 15000,
    "term_insurance": 10000000,
    "health_insurance": 500000,
    "notes": "Interested in retirement planning"
}
```

**Response:**
```json
{
    "id": "uuid",
    "name": "Amit Sharma",
    "message": "Client created successfully"
}
```

---

### 4.4 Update Client
```
PUT /clients/{client_id}
```
**Auth:** Yes

**Request:** (partial update allowed)
```json
{
    "total_aum": 600000,
    "sip": 20000,
    "notes": "Increased SIP after promotion"
}
```

**Response:**
```json
{
    "id": "uuid",
    "message": "Client updated successfully"
}
```

---

### 4.5 Delete Client (Soft Delete)
```
DELETE /clients/{client_id}
```
**Auth:** Yes

**Response:**
```json
{
    "id": "uuid",
    "message": "Client deleted successfully"
}
```

---

### 4.6 Restore Client
```
POST /clients/{client_id}/restore
```
**Auth:** Yes

**Response:**
```json
{
    "id": "uuid",
    "message": "Client restored successfully"
}
```

---

### 4.7 Get Client Overview
```
GET /clients/{client_id}/overview
```
**Auth:** Yes

**Response:**
```json
{
    "client": { /* basic info */ },
    "product_summary": {
        "total_aum": 500000,
        "sip": 15000,
        "insurance_total": 10500000
    },
    "quick_stats": {
        "tenure_years": 2,
        "touchpoints_this_year": 3,
        "goals_count": 2,
        "last_contact": "2026-01-15"
    },
    "recent_documents": [ /* array */ ]
}
```

---

### 4.8 Get Client Goals
```
GET /clients/{client_id}/goals
```
**Auth:** Yes

**Response:**
```json
{
    "lifecycle": {
        "birth_year": 1985,
        "current_age": 40,
        "retirement_age": 55,
        "life_expectancy": 85
    },
    "goals": [ /* array of goals */ ]
}
```

---

### 4.9 Get Client Touchpoints
```
GET /clients/{client_id}/touchpoints
```
**Auth:** Yes

**Query Params:**
- `status`: "all" | "scheduled" | "completed" | "cancelled"
- `year`: Filter by year

**Response:**
```json
{
    "touchpoints_this_year": 3,
    "total_touchpoints": 15,
    "touchpoints": [ /* array */ ]
}
```

---

### 4.10 Get Client Business Opportunities
```
GET /clients/{client_id}/opportunities
```
**Auth:** Yes

**Response:**
```json
{
    "opportunities": [ /* array */ ]
}
```

---

### 4.11 Get Client Call Logs
```
GET /clients/{client_id}/calls
```
**Auth:** Yes

**Response:**
```json
{
    "calls": [ /* array */ ]
}
```

---

### 4.12 Get Client Documents
```
GET /clients/{client_id}/documents
```
**Auth:** Yes

**Response:**
```json
{
    "documents": [ /* array */ ]
}
```

---

### 4.13 Convert Lead to Client
```
POST /clients/convert-from-lead
```
**Auth:** Yes

**Request:**
```json
{
    "lead_id": "uuid",
    "birthdate": "1985-03-15",
    "email": "amit@example.com",
    "address": "123 Main St, Thane",
    "risk_profile": "moderate",
    "total_aum": 500000,
    "sip": 0
}
```

**Response:**
```json
{
    "client_id": "uuid",
    "lead_id": "uuid",
    "tat_days": 15,
    "message": "Lead converted to client successfully"
}
```

---

### 4.14 Export Clients
```
GET /clients/export?format={format}
```
**Auth:** Yes

**Response:**
```json
{
    "download_url": "https://...",
    "expires_at": "2026-01-26T11:00:00Z"
}
```

---

### 4.15 Check Duplicate Client
```
POST /clients/check-duplicate
```
**Auth:** Yes

**Request:**
```json
{
    "phone": "+919123456789"
}
```

**Response:**
```json
{
    "is_duplicate": true,
    "existing_client": {
        "id": "uuid",
        "name": "Amit Sharma"
    }
}
```

---

### 4.16 Get Client Cash Flow
```
GET /clients/{client_id}/cash-flow
```
**Auth:** Yes

**Description:** Get stored cash flow data for Cash Surplus Calculator.

**Response:**
```json
{
    "client_id": "uuid",
    "insurance_premiums": {"life": 5000, "health": 10000, "motor": 3000, "other": 0},
    "savings": {"mutual_funds": 10000, "stocks": 5000, "fd": 0},
    "loans": {"home_loan": {"emi": 25000, "pending": 2500000}},
    "expenses": {"rent": 15000, "grocery": 8000, "transport": 5000},
    "income": {"salary": 100000, "rent_income": 0},
    "current_investments": {"mutual_funds": 500000, "stocks": 200000},
    "total_income_yearly": 1200000,
    "total_expenses_yearly": 840000,
    "cash_surplus_yearly": 360000,
    "cash_surplus_monthly": 30000,
    "updated_at": "2026-01-20T10:00:00Z"
}
```

---

### 4.17 Update Client Cash Flow
```
PUT /clients/{client_id}/cash-flow
```
**Auth:** Yes

**Request:**
```json
{
    "insurance_premiums": {"life": 5000, "health": 10000, "motor": 3000, "other": 0},
    "savings": {"mutual_funds": 10000, "stocks": 5000, "fd": 0},
    "loans": {"home_loan": {"emi": 25000, "pending": 2500000}},
    "expenses": {"rent": 15000, "grocery": 8000, "transport": 5000},
    "income": {"salary": 100000, "rent_income": 0},
    "current_investments": {"mutual_funds": 500000, "stocks": 200000}
}
```

**Response:**
```json
{
    "message": "Cash flow updated successfully",
    "cash_surplus_monthly": 30000,
    "cash_surplus_yearly": 360000
}
```

---

## 5. Leads (11 Endpoints)

### 5.1 List Leads
```
GET /leads
```
**Auth:** Yes

**Query Params:**
- `page`, `limit`
- `status`: "follow_up" | "meeting_scheduled" | "cancelled" | "converted"
- `search`: Search by name, phone
- `source`: Filter by source
- `sort_by`, `sort_order`

**Response:**
```json
{
    "leads": [ /* array */ ],
    "pagination": { /* ... */ }
}
```

---

### 5.2 Get Lead by ID
```
GET /leads/{lead_id}
```
**Auth:** Yes

---

### 5.3 Create Lead
```
POST /leads
```
**Auth:** Yes

**Request:**
```json
{
    "name": "Rahul Verma",
    "phone": "+919234567890",
    "source": "social_media",
    "source_description": "LinkedIn",
    "age_group": "25_to_35",
    "gender": "male",
    "marital_status": "single",
    "occupation": "service",
    "income_group": "8_9_to_12",
    "area": "Andheri",
    "notes": "Interested in SIP",
    "scheduled_date": "2026-01-28",
    "scheduled_time": "15:00"
}
```

**Response:**
```json
{
    "id": "uuid",
    "name": "Rahul Verma",
    "message": "Lead created successfully"
}
```

---

### 5.4 Update Lead
```
PUT /leads/{lead_id}
```
**Auth:** Yes

---

### 5.5 Delete Lead
```
DELETE /leads/{lead_id}
```
**Auth:** Yes

---

### 5.6 Update Lead Status
```
PUT /leads/{lead_id}/status
```
**Auth:** Yes

**Request:**
```json
{
    "status": "meeting_scheduled"
}
```

---

### 5.7 Get Leads by Status
```
GET /leads/by-status
```
**Auth:** Yes

**Response:**
```json
{
    "follow_up": { "count": 20, "leads": [] },
    "meeting_scheduled": { "count": 15, "leads": [] },
    "cancelled": { "count": 5, "leads": [] },
    "converted": { "count": 10, "leads": [] }
}
```

---

### 5.8 Get Lead Touchpoints
```
GET /leads/{lead_id}/touchpoints
```
**Auth:** Yes

---

### 5.9 Get Lead Business Opportunities
```
GET /leads/{lead_id}/opportunities
```
**Auth:** Yes

---

### 5.10 Check Duplicate Lead
```
POST /leads/check-duplicate
```
**Auth:** Yes

**Request:**
```json
{
    "phone": "+919234567890"
}
```

---

### 5.11 Get Lead Summary Stats
```
GET /leads/stats
```
**Auth:** Yes

**Response:**
```json
{
    "total": 55,
    "by_status": {
        "follow_up": 25,
        "meeting_scheduled": 10,
        "cancelled": 5,
        "converted": 15
    },
    "conversion_rate": 27.3,
    "avg_tat_days": 12
}
```

---

## 6. Tasks (12 Endpoints)

### 6.1 List Tasks
```
GET /tasks
```
**Auth:** Yes

**Query Params:**
- `page`, `limit`
- `status`: "pending" | "completed" | "cancelled" | "carried_forward"
- `priority`: "high" | "medium" | "low"
- `due_date`, `due_date_from`, `due_date_to`
- `client_id`, `lead_id`

---

### 6.2 Get Task by ID
```
GET /tasks/{task_id}
```
**Auth:** Yes

---

### 6.3 Create Task
```
POST /tasks
```
**Auth:** Yes

**Request:**
```json
{
    "description": "Call Amit about SIP increase",
    "client_id": "uuid",
    "medium": "call",
    "product_type": "SIP",
    "priority": "high",
    "due_date": "2026-01-26",
    "due_time": "10:00",
    "is_business_opportunity": true
}
```

---

### 6.4 Update Task
```
PUT /tasks/{task_id}
```
**Auth:** Yes

---

### 6.5 Delete Task
```
DELETE /tasks/{task_id}
```
**Auth:** Yes

---

### 6.6 Complete Task
```
POST /tasks/{task_id}/complete
```
**Auth:** Yes

**Response:**
```json
{
    "id": "uuid",
    "status": "completed",
    "completed_at": "2026-01-26T10:30:00Z"
}
```

---

### 6.7 Cancel Task
```
POST /tasks/{task_id}/cancel
```
**Auth:** Yes

---

### 6.8 Carry Forward Task
```
POST /tasks/{task_id}/carry-forward
```
**Auth:** Yes

**Request:**
```json
{
    "new_date": "2026-01-27"
}
```

---

### 6.9 Reschedule Task
```
POST /tasks/{task_id}/reschedule
```
**Auth:** Yes

**Request:**
```json
{
    "due_date": "2026-01-28",
    "due_time": "14:00"
}
```

---

### 6.10 Get Today's Tasks
```
GET /tasks/today
```
**Auth:** Yes

---

### 6.11 Get Overdue Tasks
```
GET /tasks/overdue
```
**Auth:** Yes

---

### 6.12 Bulk Update Tasks
```
POST /tasks/bulk-status
```
**Auth:** Yes

**Request:**
```json
{
    "task_ids": ["uuid1", "uuid2"],
    "status": "completed"
}
```

---

## 7. Touchpoints (13 Endpoints)

### 7.1 List Touchpoints
```
GET /touchpoints
```
**Auth:** Yes

**Query Params:**
- `page`, `limit`
- `status`: "scheduled" | "completed" | "cancelled" | "rescheduled"
- `client_id`, `lead_id`
- `date_from`, `date_to`
- `interaction_type`

---

### 7.2 Get Touchpoint by ID
```
GET /touchpoints/{touchpoint_id}
```
**Auth:** Yes

---

### 7.3 Create Touchpoint
```
POST /touchpoints
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "interaction_type": "meeting_office",
    "location": "Office - Thane",
    "purpose": "Portfolio Review",
    "scheduled_date": "2026-01-26",
    "scheduled_time": "14:00"
}
```

---

### 7.4 Update Touchpoint
```
PUT /touchpoints/{touchpoint_id}
```
**Auth:** Yes

---

### 7.5 Delete Touchpoint
```
DELETE /touchpoints/{touchpoint_id}
```
**Auth:** Yes

---

### 7.6 Complete Touchpoint
```
POST /touchpoints/{touchpoint_id}/complete
```
**Auth:** Yes

**Response:**
```json
{
    "id": "uuid",
    "status": "completed",
    "completed_at": "2026-01-26T15:30:00Z",
    "prompt_mom": true
}
```

---

### 7.7 Cancel Touchpoint
```
POST /touchpoints/{touchpoint_id}/cancel
```
**Auth:** Yes

---

### 7.8 Reschedule Touchpoint
```
POST /touchpoints/{touchpoint_id}/reschedule
```
**Auth:** Yes

**Request:**
```json
{
    "scheduled_date": "2026-01-28",
    "scheduled_time": "14:00"
}
```

---

### 7.9 Add MoM (Text)
```
POST /touchpoints/{touchpoint_id}/mom
```
**Auth:** Yes

**Request:**
```json
{
    "mom_text": "Discussed portfolio performance. Client happy..."
}
```

---

### 7.10 Add MoM (Voice)
```
POST /touchpoints/{touchpoint_id}/mom/voice
```
**Auth:** Yes

**Request:** multipart/form-data with audio file

**Response:**
```json
{
    "id": "uuid",
    "transcription": "...",
    "structured_mom": "Key Points:\n- ..."
}
```

---

### 7.11 Generate MoM PDF
```
POST /touchpoints/{touchpoint_id}/mom/pdf
```
**Auth:** Yes

**Response:**
```json
{
    "pdf_url": "https://..."
}
```

---

### 7.12 Send MoM to Client
```
POST /touchpoints/{touchpoint_id}/mom/send
```
**Auth:** Yes

**Request:**
```json
{
    "channels": ["whatsapp", "email"],
    "include_pdf": true
}
```

---

### 7.13 Get Today's Touchpoints
```
GET /touchpoints/today
```
**Auth:** Yes

---

## 8. Business Opportunities (10 Endpoints)

### 8.1 List Business Opportunities
```
GET /business-opportunities
```
**Auth:** Yes

**Query Params:**
- `page`, `limit`
- `outcome`: "open" | "won" | "lost"
- `opportunity_stage`: "identified" | "inbound" | "proposed"
- `opportunity_type`
- `client_id`, `lead_id`
- `due_date_from`, `due_date_to`

---

### 8.2 Get BO by ID
```
GET /business-opportunities/{bo_id}
```
**Auth:** Yes

---

### 8.3 Create BO
```
POST /business-opportunities
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "expected_amount": 15000,
    "opportunity_stage": "identified",
    "opportunity_type": "sip",
    "opportunity_source": "goal_planning",
    "additional_info": "Monthly SIP for retirement",
    "due_date": "2026-02-01",
    "due_time": "14:00"
}
```

---

### 8.4 Update BO
```
PUT /business-opportunities/{bo_id}
```
**Auth:** Yes

---

### 8.5 Delete BO
```
DELETE /business-opportunities/{bo_id}
```
**Auth:** Yes

---

### 8.6 Mark BO Won
```
POST /business-opportunities/{bo_id}/won
```
**Auth:** Yes

**Request:**
```json
{
    "outcome_amount": 15000,
    "notes": "Client started SIP"
}
```

**Response:**
```json
{
    "id": "uuid",
    "outcome": "won",
    "outcome_date": "2026-01-26",
    "tat_days": 6
}
```

---

### 8.7 Mark BO Lost
```
POST /business-opportunities/{bo_id}/lost
```
**Auth:** Yes

**Request:**
```json
{
    "notes": "Client decided to wait"
}
```

---

### 8.8 Update BO Stage
```
PUT /business-opportunities/{bo_id}/stage
```
**Auth:** Yes

**Request:**
```json
{
    "opportunity_stage": "proposed"
}
```

---

### 8.9 Get BO Pipeline
```
GET /business-opportunities/pipeline
```
**Auth:** Yes

**Response:**
```json
{
    "identified": { "count": 10, "total_amount": 500000, "opportunities": [] },
    "inbound": { "count": 5, "total_amount": 300000, "opportunities": [] },
    "proposed": { "count": 3, "total_amount": 200000, "opportunities": [] }
}
```

---

### 8.10 Get BO Summary
```
GET /business-opportunities/summary?period={period}
```
**Auth:** Yes

---

## 9. Goals (12 Endpoints)

### 9.1 List Goals
```
GET /goals
```
**Auth:** Yes

**Query Params:**
- `page`, `limit`
- `client_id`
- `goal_type`
- `status`

---

### 9.2 Get Goal by ID
```
GET /goals/{goal_id}
```
**Auth:** Yes

---

### 9.3 Create Goal
```
POST /goals
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "goal_type": "retirement",
    "goal_name": "Retirement at 55",
    "target_amount": 32000000,
    "target_date": "2041-01-01",
    "target_age": 55,
    "monthly_sip": 52000,
    "expected_return_rate": 12,
    "products": [
        {"name": "HDFC Flexi Cap", "amount": 20000, "type": "sip"}
    ],
    "calculator_type": "retirement",
    "calculator_inputs": {},
    "calculator_outputs": {}
}
```

---

### 9.4 Update Goal
```
PUT /goals/{goal_id}
```
**Auth:** Yes

---

### 9.5 Delete Goal
```
DELETE /goals/{goal_id}
```
**Auth:** Yes

---

### 9.6 Update Goal Status
```
PUT /goals/{goal_id}/status
```
**Auth:** Yes

**Request:**
```json
{
    "status": "achieved"
}
```

---

### 9.7 Recalculate Goal
```
POST /goals/{goal_id}/recalculate
```
**Auth:** Yes

**Request:**
```json
{
    "calculator_inputs": {},
    "action": "update_existing"
}
```

---

### 9.8 Generate Goal PDF
```
POST /goals/{goal_id}/pdf
```
**Auth:** Yes

---

### 9.9 Send Goal to Client
```
POST /goals/{goal_id}/send
```
**Auth:** Yes

**Request:**
```json
{
    "channels": ["whatsapp", "email"],
    "include_pdf": true
}
```

---

### 9.10 Get Goal History
```
GET /goals/{goal_id}/history
```
**Auth:** Yes

---

### 9.11 Get Client Lifecycle
```
GET /goals/lifecycle/{client_id}
```
**Auth:** Yes

**Response:**
```json
{
    "client_id": "uuid",
    "birth_year": 1985,
    "current_age": 40,
    "retirement_age": 55,
    "life_expectancy": 85,
    "goals": []
}
```

---

### 9.12 Check Existing Goal
```
POST /goals/check-existing
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "goal_type": "retirement"
}
```

---

## 10. Calculators (14 Endpoints)

### 10.1 Get Calculator Types
```
GET /calculators/types
```
**Auth:** Yes

**Response:**
```json
{
    "calculators": [
        {"type": "sip", "name": "SIP Calculator", "creates_goal": false},
        {"type": "lumpsum", "name": "Lumpsum Calculator", "creates_goal": false},
        {"type": "retirement", "name": "Retirement Planner", "creates_goal": true},
        {"type": "education", "name": "Education Planner", "creates_goal": true},
        {"type": "cash_surplus", "name": "Cash Surplus Analyzer", "creates_goal": true},
        {"type": "insurance", "name": "Insurance Calculator (HLV)", "creates_goal": false},
        {"type": "car_bike", "name": "Car/Bike Planner", "creates_goal": true},
        {"type": "lifestyle", "name": "Lifestyle Goal Planner", "creates_goal": true},
        {"type": "risk_appetite", "name": "Risk Appetite Quiz", "creates_goal": false}
    ]
}
```

---

### 10.2 Get Investment Products
```
GET /calculators/investment-products
```
**Auth:** Yes

**Description:** Get master list of investment products with default returns.

**Response:**
```json
{
    "products": [
        {"code": "mutual_funds", "name": "Mutual Funds", "default_return": 12.0, "supports_sip": true},
        {"code": "stocks", "name": "Stocks", "default_return": 12.0, "supports_sip": true},
        {"code": "fd", "name": "Fixed Deposit", "default_return": 7.0, "supports_sip": false},
        {"code": "rd", "name": "Recurring Deposit", "default_return": 7.5, "supports_sip": true},
        {"code": "ncd", "name": "NCD / Bonds", "default_return": 9.0, "supports_sip": false},
        {"code": "pf", "name": "Provident Fund", "default_return": 8.1, "supports_sip": true},
        {"code": "ppf", "name": "PPF", "default_return": 7.1, "supports_sip": true},
        {"code": "nps", "name": "NPS", "default_return": 10.0, "supports_sip": true},
        {"code": "gold", "name": "Gold", "default_return": 8.0, "supports_sip": true},
        {"code": "savings", "name": "Savings Account", "default_return": 4.0, "supports_sip": false}
    ]
}
```

---

### 10.3 Run SIP Calculator
```
POST /calculators/sip
```
**Auth:** Yes

**Request:**
```json
{
    "monthly_sip": 10000,
    "tenure_years": 15,
    "expected_return": 12,
    "step_up_type": "none",
    "step_up_value": 0
}
```

**Response:**
```json
{
    "total_investment": 1800000,
    "total_gains": 3571000,
    "final_value": 5371000,
    "returns_percent": 198.4,
    "tax_calculation": {
        "stcg": 1710,
        "ltcg": 430000,
        "total_tax": 431710
    },
    "net_returns_after_tax": 4940000
}
```

---

### 10.4 Run Lumpsum Calculator
```
POST /calculators/lumpsum
```
**Auth:** Yes

**Request:**
```json
{
    "lumpsum_amount": 500000,
    "tenure_years": 10,
    "expected_return": 12
}
```

---

### 10.5 Run Retirement Calculator
```
POST /calculators/retirement
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "current_age": 35,
    "retirement_age": 55,
    "life_expectancy": 85,
    "current_monthly_expense": 50000,
    "pre_retirement_inflation": 6,
    "post_retirement_inflation": 6,
    "expected_return": 12,
    "post_retirement_return": 7,
    "current_investments": {
        "mutual_funds": 500000,
        "stocks": 200000,
        "pf": 300000
    },
    "irregular_cash_flows": [],
    "expected_lumpsums": []
}
```

**Response:**
```json
{
    "years_to_retirement": 20,
    "retirement_duration": 30,
    "monthly_expense_at_retirement": 160000,
    "corpus_needed": 59000000,
    "current_investments_fv": 3200000,
    "shortfall": 55800000,
    "investment_options": {
        "monthly_sip": 45000,
        "yearly_investment": 540000,
        "one_time_lumpsum": 5600000
    },
    "step_up_options": {
        "step_up_amount": {"amount": 2500, "starting_sip": 35000},
        "step_up_percent": {"percent": 10, "starting_sip": 28000}
    }
}
```

---

### 10.6 Run Education Calculator
```
POST /calculators/education
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "children": [
        {
            "name": "Aarav",
            "current_age": 5,
            "goals": [
                {"name": "8th-10th STD", "target_age": 13, "current_cost": 300000},
                {"name": "11th-12th STD", "target_age": 16, "current_cost": 500000},
                {"name": "Under Graduation", "target_age": 18, "current_cost": 1600000},
                {"name": "Post Graduation", "target_age": 22, "current_cost": 2000000}
            ]
        }
    ],
    "investment_product": "mutual_funds",
    "expected_return": 12,
    "education_inflation": 10
}
```

**Response:**
```json
{
    "children": [
        {
            "name": "Aarav",
            "goals": [
                {
                    "name": "8th-10th STD",
                    "years_to_goal": 8,
                    "future_value": 643000,
                    "monthly_sip": 3981,
                    "yearly_investment": 46682,
                    "one_time_lumpsum": 260000
                }
            ],
            "total_future_value": 17700000,
            "total_monthly_sip": 39004
        }
    ],
    "summary": {
        "total_children": 1,
        "total_goals": 4,
        "total_future_corpus": 17700000,
        "total_monthly_sip": 39004,
        "total_yearly": 468000,
        "total_one_time": 3408000
    }
}
```

---

### 10.7 Run Cash Surplus Calculator
```
POST /calculators/cash-surplus
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "insurance_premiums": {
        "life": 5000,
        "health": 10000,
        "motor": 3000,
        "other": 0
    },
    "savings": {
        "mutual_funds": {"amount": 10000, "frequency": "monthly"},
        "stocks": {"amount": 5000, "frequency": "monthly"},
        "rd": {"amount": 2000, "frequency": "monthly"},
        "ppf": {"amount": 150000, "frequency": "yearly"}
    },
    "loans": {
        "home_loan": {"emi": 25000, "pending": 2500000},
        "personal_loan": {"emi": 0, "pending": 0},
        "vehicle_loan": {"emi": 8000, "pending": 200000}
    },
    "expenses": {
        "rent": 0,
        "electricity": 2000,
        "grocery": 8000,
        "transport": 5000,
        "education": 10000,
        "entertainment": 5000,
        "other": 10000
    },
    "income": {
        "salary": 150000,
        "rent_income": 0,
        "dividend": 5000,
        "interest": 2000
    },
    "current_investments": {
        "mutual_funds": 500000,
        "stocks": 200000,
        "fd": 300000,
        "pf": 800000
    }
}
```

**Response:**
```json
{
    "total_income_yearly": 1884000,
    "total_expenses_yearly": 1200000,
    "expense_breakdown": {
        "insurance": 216000,
        "savings": 354000,
        "loan_emi": 396000,
        "lifestyle": 480000,
        "education": 120000
    },
    "total_pending_loans": 2700000,
    "cash_surplus_yearly": 684000,
    "cash_surplus_monthly": 57000,
    "total_portfolio": 1800000
}
```

---

### 10.8 Run Insurance Calculator (HLV)
```
POST /calculators/insurance
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "annual_income": 1200000,
    "current_age": 35,
    "retirement_age": 60,
    "existing_life_cover": 5000000,
    "existing_liabilities": 2500000,
    "annual_expenses": 600000,
    "dependants": 3
}
```

**Response:**
```json
{
    "hlv_calculated": 25000000,
    "existing_cover": 5000000,
    "cover_gap": 20000000,
    "recommended_term_cover": 20000000,
    "health_cover_recommended": 1500000
}
```

---

### 10.9 Run Car/Bike Calculator
```
POST /calculators/car-bike
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "vehicle_type": "car",
    "target_amount": 1000000,
    "target_years": 3,
    "down_payment_available": 200000,
    "expected_return": 12,
    "include_loan_option": true
}
```

**Response:**
```json
{
    "target_amount": 1000000,
    "down_payment": 200000,
    "amount_to_accumulate": 800000,
    "investment_options": {
        "monthly_sip": 18500,
        "yearly_investment": 222000,
        "one_time_lumpsum": 570000
    },
    "loan_option": {
        "loan_amount": 800000,
        "tenure_years": 5,
        "interest_rate": 9.5,
        "emi": 16800
    }
}
```

---

### 10.10 Run Lifestyle Calculator
```
POST /calculators/lifestyle
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "lifestyle_subtype": "vacation_international",
    "goal_name": "Europe Trip",
    "target_amount": 500000,
    "target_years": 2,
    "current_savings": 50000,
    "expected_return": 12,
    "inflation_rate": 6
}
```

**Response:**
```json
{
    "goal_name": "Europe Trip",
    "future_value": 561800,
    "current_savings_fv": 62720,
    "gap": 499080,
    "investment_options": {
        "monthly_sip": 18800,
        "yearly_investment": 225600,
        "one_time_lumpsum": 398000
    }
}
```

---

### 10.11 Run Risk Appetite Quiz
```
POST /calculators/risk-appetite
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "answers": {
        "q1": "c",
        "q2": "b",
        "q3": "a",
        "q4": "c",
        "q5": "b"
    }
}
```

**Response:**
```json
{
    "score": 65,
    "risk_profile": "moderate",
    "recommended_allocation": {
        "equity": 60,
        "debt": 30,
        "gold": 10
    }
}
```

---

### 10.12 Save Calculator & Create Goal
```
POST /calculators/save-as-goal
```
**Auth:** Yes

**Request:**
```json
{
    "calculator_type": "retirement",
    "client_id": "uuid",
    "inputs": {},
    "outputs": {},
    "save_as_goal": true,
    "goal_name": "Retirement at 55",
    "products": [
        {"name": "HDFC Flexi Cap", "amount": 20000, "type": "sip"},
        {"name": "ICICI Prudential Value", "amount": 15000, "type": "sip"}
    ]
}
```

**Response:**
```json
{
    "calculator_result_id": "uuid",
    "goal_id": "uuid",
    "pdf_url": "https://...",
    "message": "Goal created successfully"
}
```

---

### 10.13 Get Calculator Result
```
GET /calculators/results/{result_id}
```
**Auth:** Yes

---

### 10.14 Get Client Calculator History
```
GET /calculators/history/{client_id}
```
**Auth:** Yes

**Response:**
```json
{
    "results": [
        {
            "id": "uuid",
            "calculator_type": "retirement",
            "created_at": "2026-01-20T10:00:00Z",
            "linked_goal_id": "uuid"
        }
    ]
}
```

---

## 11. Documents (6 Endpoints)

### 11.1 List Documents
```
GET /documents?client_id={client_id}&document_type={type}
```
**Auth:** Yes

---

### 11.2 Upload Document
```
POST /documents
```
**Auth:** Yes

**Request:** multipart/form-data
- `file`: File
- `client_id`: UUID
- `name`: String
- `document_type`: String

---

### 11.3 Get Document
```
GET /documents/{document_id}
```
**Auth:** Yes

---

### 11.4 Delete Document
```
DELETE /documents/{document_id}
```
**Auth:** Yes

---

### 11.5 Send Document to Client
```
POST /documents/{document_id}/send
```
**Auth:** Yes

**Request:**
```json
{
    "channels": ["whatsapp", "email"]
}
```

---

### 11.6 Download Document
```
GET /documents/{document_id}/download
```
**Auth:** Yes

**Response:** File stream

---

## 12. Google Drive (6 Endpoints)

### 12.1 Setup Drive Structure
```
POST /drive/setup
```
**Auth:** Yes

**Response:**
```json
{
    "drive_folder_id": "1ABC...",
    "sheet_id": "1XYZ...",
    "clients_folder_id": "1DEF...",
    "message": "Drive structure created"
}
```

---

### 12.2 Create Client Folder
```
POST /drive/client-folder
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "client_name": "Amit Sharma"
}
```

---

### 12.3 Upload to Drive
```
POST /drive/upload
```
**Auth:** Yes

**Request:** multipart/form-data

---

### 12.4 Delete from Drive
```
DELETE /drive/file/{file_id}
```
**Auth:** Yes

---

### 12.5 List Drive Files
```
GET /drive/files?folder_id={folder_id}
```
**Auth:** Yes

---

### 12.6 Get Drive Status
```
GET /drive/status
```
**Auth:** Yes

---

## 13. Google Sheets Sync (6 Endpoints)

### 13.1 Get Sync Status
```
GET /sheets/status
```
**Auth:** Yes

---

### 13.2 Trigger Manual Sync
```
POST /sheets/sync
```
**Auth:** Yes

**Request:**
```json
{
    "direction": "bidirectional",
    "tables": ["clients", "leads", "business_opportunities"]
}
```

---

### 13.3 Get Sync History
```
GET /sheets/history
```
**Auth:** Yes

---

### 13.4 Resolve Conflict
```
POST /sheets/resolve-conflict
```
**Auth:** Yes

---

### 13.5 Setup Sheet Structure
```
POST /sheets/setup
```
**Auth:** Yes

---

### 13.6 Import from Existing Sheet
```
POST /sheets/import
```
**Auth:** Yes

**Request:**
```json
{
    "sheet_id": "1XYZ..."
}
```

---

## 14. Notifications (5 Endpoints)

### 14.1 List Notifications
```
GET /notifications?is_read={bool}&type={type}
```
**Auth:** Yes

---

### 14.2 Mark as Read
```
PUT /notifications/{notification_id}/read
```
**Auth:** Yes

---

### 14.3 Mark All as Read
```
PUT /notifications/read-all
```
**Auth:** Yes

---

### 14.4 Delete Notification
```
DELETE /notifications/{notification_id}
```
**Auth:** Yes

---

### 14.5 Get Unread Count
```
GET /notifications/unread-count
```
**Auth:** Yes

---

## 15. WhatsApp (5 Endpoints)

### 15.1 Send Text Message
```
POST /whatsapp/send
```
**Auth:** Yes

**Request:**
```json
{
    "phone": "+919123456789",
    "message": "Hello!",
    "client_id": "uuid"
}
```

---

### 15.2 Send Document
```
POST /whatsapp/send-document
```
**Auth:** Yes

**Request:**
```json
{
    "phone": "+919123456789",
    "document_url": "https://...",
    "filename": "Plan.pdf",
    "caption": "Please find attached.",
    "client_id": "uuid"
}
```

---

### 15.3 Send Birthday Greeting
```
POST /whatsapp/birthday-greeting
```
**Auth:** Yes

**Request:**
```json
{
    "client_id": "uuid",
    "template": "birthday_wishes_1"
}
```

---

### 15.4 Get Message History
```
GET /whatsapp/history?client_id={client_id}
```
**Auth:** Yes

---

### 15.5 Get Templates
```
GET /whatsapp/templates
```
**Auth:** Yes

---

## 16. Email (3 Endpoints)

### 16.1 Send Email
```
POST /email/send
```
**Auth:** Yes

**Request:**
```json
{
    "to": "amit@example.com",
    "subject": "Your Retirement Plan",
    "body": "Please find attached...",
    "attachments": ["https://..."],
    "client_id": "uuid"
}
```

---

### 16.2 Send Birthday Email
```
POST /email/birthday
```
**Auth:** Yes

---

### 16.3 Get Email History
```
GET /email/history?client_id={client_id}
```
**Auth:** Yes

---

## 17. OCR & Voice (6 Endpoints)

### 17.1 Scan Diary Page
```
POST /ocr/scan-diary
```
**Auth:** Yes

**Request:** multipart/form-data with image

**Response:**
```json
{
    "raw_text": "26 Jan - Meet Sharma ji 3pm...",
    "extracted_entries": [
        {
            "type": "touchpoint",
            "data": { "client_name_guess": "Sharma", "date": "2026-01-26" },
            "confidence": 0.85
        }
    ]
}
```

---

### 17.2 Scan Document (OCR)
```
POST /ocr/scan-document
```
**Auth:** Yes

---

### 17.3 Transcribe Voice
```
POST /voice/transcribe
```
**Auth:** Yes

**Request:** multipart/form-data with audio

**Response:**
```json
{
    "transcription": "Add lead Amit Sharma...",
    "duration_seconds": 15
}
```

---

### 17.4 Extract Intent from Voice
```
POST /voice/extract-intent
```
**Auth:** Yes

**Request:**
```json
{
    "transcription": "Add lead Amit Sharma met at wedding..."
}
```

**Response:**
```json
{
    "intent": "create_lead",
    "entities": {
        "name": "Amit Sharma",
        "source": "natural_market"
    }
}
```

---

### 17.5 Create Entry from Voice
```
POST /voice/create-entry
```
**Auth:** Yes

**Request:** multipart/form-data with audio

---

### 17.6 Structure MoM
```
POST /voice/structure-mom
```
**Auth:** Yes

**Request:**
```json
{
    "raw_text": "Discussed portfolio performance..."
}
```

**Response:**
```json
{
    "structured": {
        "key_points": ["Portfolio up 12%"],
        "action_items": [{"task": "Follow up", "due": "next week"}],
        "summary": "..."
    }
}
```

---

## 18. Campaigns (7 Endpoints)

### 18.1 List Campaigns
```
GET /campaigns
```
**Auth:** Yes

---

### 18.2 Create Campaign
```
POST /campaigns
```
**Auth:** Yes

**Request:**
```json
{
    "name": "Term Insurance Feb 2026",
    "description": "Clients without term",
    "filter_criteria": { "marital_status": "married", "term_insurance": 0 },
    "client_ids": ["uuid1", "uuid2"]
}
```

---

### 18.3 Get Campaign
```
GET /campaigns/{campaign_id}
```
**Auth:** Yes

---

### 18.4 Add Clients to Campaign
```
POST /campaigns/{campaign_id}/clients
```
**Auth:** Yes

---

### 18.5 Remove Client from Campaign
```
DELETE /campaigns/{campaign_id}/clients/{client_id}
```
**Auth:** Yes

---

### 18.6 Execute Campaign
```
POST /campaigns/{campaign_id}/execute
```
**Auth:** Yes

**Request:**
```json
{
    "channel": "whatsapp",
    "template": "term_insurance_pitch"
}
```

---

### 18.7 Delete Campaign
```
DELETE /campaigns/{campaign_id}
```
**Auth:** Yes

---

## 19. Analytics & Opportunities (5 Endpoints)

### 19.1 Get AI Opportunities
```
GET /analytics/opportunities
```
**Auth:** Yes

**Response:**
```json
{
    "opportunities": [
        { "type": "no_touchpoints_this_year", "title": "No Touchpoints", "count": 12, "priority": "critical" },
        { "type": "married_no_term", "title": "Married Without Term", "count": 15, "priority": "critical" }
    ],
    "total_opportunities": 53
}
```

---

### 19.2 Get Opportunity Clients
```
GET /analytics/opportunities/{type}/clients
```
**Auth:** Yes

---

### 19.3 Get 80-20 Analysis
```
GET /analytics/80-20?type={aum|sip}
```
**Auth:** Yes

---

### 19.4 Get Conversion Analytics
```
GET /analytics/conversions?period={period}
```
**Auth:** Yes

---

### 19.5 Get Trends
```
GET /analytics/trends?metric={metric}&period={period}
```
**Auth:** Yes

---

## 20. Market Analysis (4 Endpoints)

### 20.1 Get Market News
```
GET /market/news
```
**Auth:** Yes

---

### 20.2 Get Market Highlights
```
GET /market/highlights
```
**Auth:** Yes

---

### 20.3 Ask Market Question (AI)
```
POST /market/ask
```
**Auth:** Yes

**Request:**
```json
{
    "question": "What sectors are performing well?"
}
```

---

### 20.4 Refresh Market Data
```
POST /market/refresh
```
**Auth:** Yes

---

## 21. Quick Notes (4 Endpoints)

### 21.1 List Quick Notes
```
GET /quick-notes?search={query}
```
**Auth:** Yes

---

### 21.2 Create Quick Note
```
POST /quick-notes
```
**Auth:** Yes

**Request:**
```json
{
    "content": "Remember to call RTA...",
    "tags": ["rta", "urgent"]
}
```

---

### 21.3 Update Quick Note
```
PUT /quick-notes/{note_id}
```
**Auth:** Yes

---

### 21.4 Delete Quick Note
```
DELETE /quick-notes/{note_id}
```
**Auth:** Yes

---

## 22. Call Logs (3 Endpoints)

### 22.1 List Call Logs
```
GET /call-logs?client_id={id}&call_type={type}
```
**Auth:** Yes

---

### 22.2 Add Call Log
```
POST /call-logs
```
**Auth:** Yes

**Request:**
```json
{
    "phone_number": "+919123456789",
    "client_id": "uuid",
    "call_type": "outgoing",
    "duration_seconds": 180,
    "call_time": "2026-01-25T10:30:00Z",
    "notes": "Discussed SIP"
}
```

---

### 22.3 Sync Call Logs from Phone
```
POST /call-logs/sync
```
**Auth:** Yes

---

## 23. Search (3 Endpoints)

### 23.1 Global Search
```
GET /search?q={query}&type={type}
```
**Auth:** Yes

**Response:**
```json
{
    "query": "amit",
    "results": {
        "clients": [],
        "leads": [],
        "tasks": []
    }
}
```

---

### 23.2 Search Clients
```
GET /search/clients?q={query}
```
**Auth:** Yes

---

### 23.3 Search Suggestions
```
GET /search/suggestions?q={query}
```
**Auth:** Yes

---

## 24. Diary Views (6 Endpoints)

### 24.1 Get Today's Diary
```
GET /diary/today
```
**Auth:** Yes

**Response:**
```json
{
    "date": "2026-01-26",
    "summary": { "tasks": 5, "touchpoints": 3 },
    "tasks": [],
    "touchpoints": [],
    "business_opportunities": [],
    "leads": [],
    "birthdays": []
}
```

---

### 24.2 Get Diary by Date
```
GET /diary/{date}
```
**Auth:** Yes

---

### 24.3 Get Week View
```
GET /diary/week?start_date={date}
```
**Auth:** Yes

---

### 24.4 Get Month View
```
GET /diary/month?year={year}&month={month}
```
**Auth:** Yes

---

### 24.5 Get Priority Tasks View
```
GET /diary/priority-tasks
```
**Auth:** Yes

---

### 24.6 Get Hourly Planner
```
GET /diary/planner/{date}
```
**Auth:** Yes

---

## 25. Data Import (5 Endpoints)

### 25.1 Import from Excel
```
POST /import/excel
```
**Auth:** Yes

**Request:** multipart/form-data with file

---

### 25.2 Import from CAMS
```
POST /import/cams
```
**Auth:** Yes

---

### 25.3 Import from Fintech
```
POST /import/fintech
```
**Auth:** Yes

---

### 25.4 Get Import Templates
```
GET /import/templates
```
**Auth:** Yes

---

### 25.5 Get Import History
```
GET /import/history
```
**Auth:** Yes

---

## Summary

| Category | Endpoints |
|----------|-----------|
| Health | 1 |
| Profile | 8 |
| Dashboard | 5 |
| Clients | 15 |
| Leads | 11 |
| Tasks | 12 |
| Touchpoints | 13 |
| Business Opportunities | 10 |
| Goals | 12 |
| Calculators | 6 |
| Documents | 6 |
| Google Drive | 6 |
| Google Sheets | 6 |
| Notifications | 5 |
| WhatsApp | 5 |
| Email | 3 |
| OCR & Voice | 6 |
| Campaigns | 7 |
| Analytics | 5 |
| Market | 4 |
| Quick Notes | 4 |
| Call Logs | 3 |
| Search | 3 |
| Diary Views | 6 |
| Data Import | 5 |
| **TOTAL** | **~161** |

---

## Error Response Format

All errors follow this format:
```json
{
    "error": true,
    "message": "Error description",
    "code": "ERROR_CODE",
    "details": {}
}
```

Common error codes:
- `UNAUTHORIZED`: Invalid or missing token
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid request data
- `DUPLICATE_ENTRY`: Resource already exists
- `INTERNAL_ERROR`: Server error
