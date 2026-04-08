# MFD Digital Diary - Project Structure

## Overview

| Item | Value |
|------|-------|
| Framework | FastAPI |
| Python | 3.11+ |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth + JWT validation |

---

## 1. Folder Structure

```
mfd-diary/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── config.py                   # Environment settings
│   │   ├── database.py                 # Supabase client
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── dependencies.py         # JWT validation, get_current_user
│   │   │
│   │   ├── models/                     # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py               # Pagination, errors
│   │   │   ├── profile.py
│   │   │   ├── client.py
│   │   │   ├── lead.py
│   │   │   ├── task.py
│   │   │   ├── touchpoint.py
│   │   │   ├── business_opportunity.py
│   │   │   ├── goal.py
│   │   │   ├── calculator.py
│   │   │   ├── document.py
│   │   │   ├── campaign.py
│   │   │   ├── notification.py
│   │   │   └── communication.py
│   │   │
│   │   ├── routers/                    # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── profile.py
│   │   │   ├── dashboard.py
│   │   │   ├── clients.py
│   │   │   ├── leads.py
│   │   │   ├── tasks.py
│   │   │   ├── touchpoints.py
│   │   │   ├── business_opportunities.py
│   │   │   ├── goals.py
│   │   │   ├── calculators.py
│   │   │   ├── documents.py
│   │   │   ├── google_drive.py
│   │   │   ├── google_sheets.py
│   │   │   ├── notifications.py
│   │   │   ├── whatsapp.py             # [TEAM]
│   │   │   ├── email.py                # [TEAM]
│   │   │   ├── ocr_voice.py            # [COLLABORATIVE]
│   │   │   ├── campaigns.py
│   │   │   ├── analytics.py            # [COLLABORATIVE]
│   │   │   ├── market.py               # [COLLABORATIVE]
│   │   │   ├── quick_notes.py
│   │   │   ├── call_logs.py
│   │   │   ├── search.py
│   │   │   ├── diary.py
│   │   │   └── data_import.py
│   │   │
│   │   ├── services/                   # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── profile_service.py
│   │   │   ├── client_service.py
│   │   │   ├── lead_service.py
│   │   │   ├── task_service.py
│   │   │   ├── touchpoint_service.py
│   │   │   ├── bo_service.py
│   │   │   ├── goal_service.py
│   │   │   ├── calculator_service.py
│   │   │   ├── document_service.py
│   │   │   ├── google_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── whatsapp_service.py     # [TEAM]
│   │   │   ├── email_service.py        # [TEAM]
│   │   │   ├── ocr_service.py          # [COLLABORATIVE]
│   │   │   ├── voice_service.py        # [COLLABORATIVE]
│   │   │   ├── ai_service.py           # [COLLABORATIVE]
│   │   │   ├── pdf_service.py
│   │   │   ├── campaign_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── import_service.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── helpers.py              # General helpers
│   │   │   ├── validators.py           # Custom validators
│   │   │   ├── formatters.py           # Date, currency formatting
│   │   │   ├── calculators.py          # Financial formulas
│   │   │   └── exceptions.py           # Custom exceptions
│   │   │
│   │   └── constants/
│   │       ├── __init__.py
│   │       ├── enums.py                # Python enums (match DB)
│   │       ├── messages.py             # Response messages
│   │       └── defaults.py             # Default values
│   │
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
│
├── docs/
│   ├── DATABASE_SCHEMA.md
│   ├── API_ENDPOINTS.md
│   ├── PROJECT_STRUCTURE.md
│   ├── PYDANTIC_MODELS.md
│   └── MIGRATION_V2_CALCULATORS.sql
│
└── .gitignore
```

---

## 2. File Descriptions

### Core Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, CORS, router includes |
| `config.py` | Settings class, env variables |
| `database.py` | Supabase client (anon + admin) |

### Auth

| File | Purpose |
|------|---------|
| `dependencies.py` | `get_current_user()`, `get_current_user_id()` - JWT validation |

### Models (Pydantic Schemas)

| File | Contains |
|------|----------|
| `common.py` | `PaginatedResponse`, `ErrorResponse`, `SuccessMessage` |
| `profile.py` | `ProfileCreate`, `ProfileUpdate`, `ProfileResponse` |
| `client.py` | `ClientCreate`, `ClientUpdate`, `ClientResponse`, `ClientListResponse`, `ClientOverview`, `ClientCashFlow` |
| `lead.py` | `LeadCreate`, `LeadUpdate`, `LeadResponse`, `LeadListResponse` |
| `task.py` | `TaskCreate`, `TaskUpdate`, `TaskResponse`, `TaskListResponse` |
| `touchpoint.py` | `TouchpointCreate`, `TouchpointUpdate`, `TouchpointResponse` |
| `business_opportunity.py` | `BOCreate`, `BOUpdate`, `BOResponse`, `BOPipeline` |
| `goal.py` | `GoalCreate`, `GoalUpdate`, `GoalResponse`, `GoalWithSubgoals` |
| `calculator.py` | All calculator request/response schemas |
| `document.py` | `DocumentUpload`, `DocumentResponse` |
| `campaign.py` | `CampaignCreate`, `CampaignResponse` |
| `notification.py` | `NotificationResponse` |
| `communication.py` | `WhatsAppRequest`, `EmailRequest` |

### Routers (Endpoints)

| File | Prefix | Endpoints |
|------|--------|-----------|
| `health.py` | `/health` | 1 |
| `profile.py` | `/profile` | 8 |
| `dashboard.py` | `/dashboard` | 5 |
| `clients.py` | `/clients` | 17 |
| `leads.py` | `/leads` | 11 |
| `tasks.py` | `/tasks` | 12 |
| `touchpoints.py` | `/touchpoints` | 13 |
| `business_opportunities.py` | `/business-opportunities` | 10 |
| `goals.py` | `/goals` | 12 |
| `calculators.py` | `/calculators` | 14 |
| `documents.py` | `/documents` | 6 |
| `google_drive.py` | `/drive` | 6 |
| `google_sheets.py` | `/sheets` | 6 |
| `notifications.py` | `/notifications` | 5 |
| `whatsapp.py` | `/whatsapp` | 5 [TEAM] |
| `email.py` | `/email` | 3 [TEAM] |
| `ocr_voice.py` | `/ocr-voice` | 6 [COLLABORATIVE] |
| `campaigns.py` | `/campaigns` | 7 |
| `analytics.py` | `/analytics` | 5 [COLLABORATIVE] |
| `market.py` | `/market` | 4 [COLLABORATIVE] |
| `quick_notes.py` | `/quick-notes` | 4 |
| `call_logs.py` | `/call-logs` | 3 |
| `search.py` | `/search` | 3 |
| `diary.py` | `/diary` | 6 |
| `data_import.py` | `/import` | 5 |

### Services (Business Logic)

| File | Purpose |
|------|---------|
| `profile_service.py` | Profile CRUD, Google OAuth |
| `client_service.py` | Client CRUD, convert from lead, cash flow |
| `lead_service.py` | Lead CRUD, status management |
| `task_service.py` | Task CRUD, carry forward |
| `touchpoint_service.py` | Touchpoint CRUD, MoM storage |
| `bo_service.py` | BO CRUD, pipeline, TAT |
| `goal_service.py` | Goal CRUD, sub-goals |
| `calculator_service.py` | All financial calculations |
| `document_service.py` | Upload, download, storage |
| `google_service.py` | Drive/Sheets API calls |
| `notification_service.py` | In-app notifications |
| `whatsapp_service.py` | WhatsApp API [TEAM] |
| `email_service.py` | Email sending [TEAM] |
| `ocr_service.py` | OCR processing [COLLABORATIVE] |
| `voice_service.py` | Voice transcription [COLLABORATIVE] |
| `ai_service.py` | AI/LLM calls [COLLABORATIVE] |
| `pdf_service.py` | PDF generation |
| `campaign_service.py` | Campaign execution |
| `analytics_service.py` | Analytics queries |
| `import_service.py` | Excel/CAMS import |

### Utils

| File | Purpose |
|------|---------|
| `helpers.py` | `calculate_age()`, `generate_id()`, etc. |
| `validators.py` | Phone, email, PAN validators |
| `formatters.py` | Date, currency, number formatting |
| `calculators.py` | SIP, CAGR, PMT formulas |
| `exceptions.py` | `NotFoundError`, `DuplicateError`, etc. |

### Constants

| File | Purpose |
|------|---------|
| `enums.py` | Python enums matching DB enums |
| `messages.py` | Success/error message strings |
| `defaults.py` | Default return rates, limits, etc. |

---

## 3. Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | `snake_case.py` | `client_service.py` |
| Classes | `PascalCase` | `ClientService`, `ClientCreate` |
| Functions | `snake_case` | `get_client`, `create_lead` |
| Variables | `snake_case` | `client_data`, `user_id` |
| Constants | `UPPER_SNAKE` | `MAX_PAGE_SIZE`, `DEFAULT_RETURN` |
| Routers | Plural nouns | `clients.py`, `tasks.py` |
| Models | Singular noun | `client.py`, `task.py` |

---

## 4. Import Order

```python
# 1. Standard library
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

# 3. Local - config
from app.config import settings
from app.database import supabase

# 4. Local - auth
from app.auth.dependencies import get_current_user_id

# 5. Local - models
from app.models.client import ClientCreate, ClientResponse

# 6. Local - services
from app.services.client_service import ClientService

# 7. Local - utils
from app.utils.helpers import calculate_age
```

**Rule:** Always use absolute imports (`from app.xxx`), never relative (`from ..xxx`).

---

## 5. Implementation Ownership

### Cursor Implements (Full)

| Module | Priority |
|--------|----------|
| Auth (JWT) | P0 |
| Profile | P0 |
| Clients | P0 |
| Leads | P0 |
| Tasks | P0 |
| Touchpoints | P0 |
| Business Opportunities | P0 |
| Goals | P0 |
| Calculators | P1 |
| Documents | P1 |
| Google Drive | P1 |
| Google Sheets | P1 |
| Notifications | P1 |
| PDF Generation | P1 |
| Campaigns (CRUD) | P2 |
| Quick Notes | P2 |
| Call Logs | P2 |
| Search | P2 |
| Diary Views | P2 |
| Data Import | P3 |

### Team Handles (Placeholder Only)

| Module | Owner |
|--------|-------|
| WhatsApp Service | Other intern |
| Email Service | Other intern |
| Frontend (Flutter) | Other intern |

### Collaborative Decision Needed

| Module | Options to Discuss |
|--------|-------------------|
| AI Service | OpenAI vs Gemini vs Claude |
| Voice Transcription | Whisper API vs Google STT |
| OCR | Google Vision vs Tesseract |
| Analytics AI | Which LLM for insights? |

---

## 6. Environment Variables

```env
# Required
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=
SUPABASE_JWT_SECRET=

# Google (for Drive/Sheets)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

# [COLLABORATIVE] AI - Team decides
OPENAI_API_KEY=
GEMINI_API_KEY=

# [TEAM] Communication - Other intern
WHATSAPP_API_KEY=
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
```

---

## 7. Dependencies

```txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
supabase==2.3.4

# Auth
python-jose[cryptography]==3.3.0

# HTTP
httpx==0.26.0

# Google
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.116.0

# PDF
reportlab==4.0.8

# Excel
openpyxl==3.1.2
pandas==2.1.4

# Dev
python-dotenv==1.0.0
```

---

## Summary

| Category | Files |
|----------|-------|
| Core | 4 |
| Auth | 1 |
| Models | 13 |
| Routers | 25 |
| Services | 20 |
| Utils | 5 |
| Constants | 3 |
| **Total** | **~71** |

---

**Next Document:** PYDANTIC_MODELS.md (all request/response schemas)
