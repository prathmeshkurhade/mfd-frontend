# WhatsApp Bot — Webhook API Documentation

## Overview

This document describes the webhook API endpoints your WhatsApp bot will call to create Leads, Tasks, Touchpoints (Meetings), and Business Opportunities in the Infinity MFD system.

**Base URL:** `{API_BASE_URL}/api/v1/whatsapp-forms`

---

## Authentication

Every request must include the API key in the header:

```
X-API-Key: {WEBHOOK_API_KEY}
```

If the key is missing or wrong, you'll get a `401 Unauthorized` response.

---

## User Identification

Every request body must include `mfd_phone` — the MFD's **10-digit mobile number** (without +91 or country code).

The backend uses this to identify which MFD (user) is submitting the form. If the phone number doesn't match any registered MFD, you'll get a `400 Bad Request` with message `"No MFD found with phone number XXXXXXXXXX"`.

---

## Response Format

### Success Response
```json
{
  "status": "success",
  "message": "Lead created successfully",
  "entity_id": "uuid-of-created-entity",
  "errors": null
}
```

### Error Response (Validation — 422)
When required fields are missing or values are invalid:
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "description of the error",
      "type": "error_type"
    }
  ]
}
```

### Error Response (Business Logic — 400)
```json
{
  "detail": "Either client_id or lead_id must be provided"
}
```

---

## Endpoints

### 1. Create Lead

**POST** `/api/v1/whatsapp-forms/create-lead`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mfd_phone` | string | YES | MFD's 10-digit phone number |
| `name` | string | no | Lead name (max 255 chars) |
| `phone` | string | no | Lead's 10-digit phone number (without +91) |
| `email` | string | no | Valid email address |
| `gender` | enum | no | See Gender enum below |
| `marital_status` | enum | no | See Marital Status enum below |
| `occupation` | enum | no | See Occupation enum below |
| `income_group` | enum | no | See Income Group enum below |
| `age_group` | enum | no | See Age Group enum below |
| `area` | string | no | Area / locality |
| `source` | enum | no | See Source enum below |
| `referred_by` | string | no | Name of person who referred |
| `dependants` | integer | no | Number of dependants |
| `source_description` | string | no | Additional source details |
| `status` | enum | no | Defaults to `follow_up`. See Lead Status enum |
| `scheduled_date` | date | no | Format: `YYYY-MM-DD` |
| `scheduled_time` | string | no | Format: `HH:MM` |
| `all_day` | boolean | no | `true` or `false` |
| `notes` | string | no | Free text notes |

**Example Request:**
```json
{
  "mfd_phone": "9876543210",
  "name": "Rahul Sharma",
  "phone": "9123456789",
  "source": "referral",
  "area": "Andheri West"
}
```

---

### 2. Create Task

**POST** `/api/v1/whatsapp-forms/create-task`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mfd_phone` | string | YES | MFD's 10-digit phone number |
| `title` | string | no | Task title (max 255 chars) |
| `description` | string | no | Task description |
| `client_id` | UUID | no | Client UUID (from search endpoint) |
| `lead_id` | UUID | no | Lead UUID (from search endpoint) |
| `priority` | enum | no | Defaults to `medium`. See Task Priority enum |
| `medium` | enum | no | See Task Medium enum |
| `due_date` | date | no | Format: `YYYY-MM-DD` |
| `due_time` | string | no | Format: `HH:MM` |
| `all_day` | boolean | no | `true` or `false` |
| `product_type` | string | no | Product type description |
| `is_business_opportunity` | boolean | no | `true` or `false` |

**Example Request:**
```json
{
  "mfd_phone": "9876543210",
  "title": "Follow up with Rahul about SIP",
  "due_date": "2026-03-28",
  "priority": "high",
  "medium": "call",
  "client_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### 3. Create Touchpoint (Meeting)

**POST** `/api/v1/whatsapp-forms/create-touchpoint`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mfd_phone` | string | YES | MFD's 10-digit phone number |
| `client_id` | UUID | no* | Client UUID (from search endpoint) |
| `lead_id` | UUID | no* | Lead UUID (from search endpoint) |
| `interaction_type` | enum | no | See Interaction Type enum |
| `scheduled_date` | date | no | Format: `YYYY-MM-DD` |
| `scheduled_time` | string | no | Format: `HH:MM` |
| `location` | string | no | Meeting location |
| `agenda` | string | no | Meeting purpose/agenda |
| `status` | enum | no | Defaults to `scheduled`. See Touchpoint Status enum |

*Note: Either `client_id` or `lead_id` must be provided. The backend will return an error if both are missing.*

**Example Request:**
```json
{
  "mfd_phone": "9876543210",
  "client_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "interaction_type": "meeting_office",
  "scheduled_date": "2026-03-28",
  "scheduled_time": "14:30",
  "agenda": "Discuss retirement planning"
}
```

---

### 4. Create Business Opportunity

**POST** `/api/v1/whatsapp-forms/create-business-opportunity`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mfd_phone` | string | YES | MFD's 10-digit phone number |
| `client_id` | UUID | no* | Client UUID (from search endpoint) |
| `lead_id` | UUID | no* | Lead UUID (from search endpoint) |
| `opportunity_type` | enum | no | See Opportunity Type enum |
| `opportunity_stage` | enum | no | Defaults to `identified`. See Opportunity Stage enum |
| `opportunity_source` | enum | no | Defaults to `client_servicing`. See Opportunity Source enum |
| `expected_amount` | float | no | Must be greater than 0 |
| `due_date` | date | no | Format: `YYYY-MM-DD`. Defaults to today |
| `notes` | string | no | Free text notes |

*Note: Either `client_id` or `lead_id` must be provided. The backend will return an error if both are missing.*

**Example Request:**
```json
{
  "mfd_phone": "9876543210",
  "client_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "opportunity_type": "sip",
  "expected_amount": 50000,
  "notes": "Client interested in monthly SIP for retirement"
}
```

---

### 5. Search Clients / Leads

Use this endpoint to find a client or lead by name, so you can get their UUID for linking in the other forms.

**POST** `/api/v1/whatsapp-forms/search`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mfd_phone` | string | YES | MFD's 10-digit phone number |
| `query` | string | YES | Search text (name or part of name) |
| `entity_type` | string | YES | `"client"` or `"lead"` |

**Example Request:**
```json
{
  "mfd_phone": "9876543210",
  "query": "rahul",
  "entity_type": "client"
}
```

**Success Response:**
```json
{
  "results": [
    { "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "name": "Rahul Sharma" },
    { "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901", "name": "Rahul Gupta" }
  ],
  "total": 2
}
```

**Suggested WhatsApp Flow:**
1. Bot asks: "Which client is this for?"
2. User types: "Rahul"
3. Bot calls search → gets results
4. Bot shows: "1. Rahul Sharma  2. Rahul Gupta"
5. User picks a number
6. Bot stores the selected `id` as `client_id` for the form

---

## Enum Reference

### Source (for leads)
| Value | Display Label |
|-------|--------------|
| `natural_market` | Natural Market |
| `referral` | Referral |
| `social_networking` | Social Networking |
| `business_group` | Business Group |
| `marketing_activity` | Marketing Activity |
| `iap` | IAP |
| `cold_call` | Cold Call |
| `social_media` | Social Media |

### Lead Status
| Value | Display Label |
|-------|--------------|
| `follow_up` | Follow Up (default) |
| `meeting_scheduled` | Meeting Scheduled |
| `cancelled` | Cancelled |
| `converted` | Converted |

### Gender
| Value | Display Label |
|-------|--------------|
| `male` | Male |
| `female` | Female |
| `other` | Other |

### Marital Status
| Value | Display Label |
|-------|--------------|
| `single` | Single |
| `married` | Married |
| `divorced` | Divorced |
| `widower` | Widower |
| `separated` | Separated |
| `dont_know` | Don't Know |

### Occupation
| Value | Display Label |
|-------|--------------|
| `service` | Service |
| `business` | Business |
| `retired` | Retired |
| `professional` | Professional |
| `student` | Student |
| `self_employed` | Self Employed |
| `housemaker` | Housemaker |
| `dont_know` | Don't Know |

### Income Group
| Value | Display Label |
|-------|--------------|
| `zero` | Zero |
| `1_to_2_5` | 1 - 2.5 Lakhs |
| `2_6_to_8_8` | 2.6 - 8.8 Lakhs |
| `8_9_to_12` | 8.9 - 12 Lakhs |
| `12_1_to_24` | 12.1 - 24 Lakhs |
| `24_1_to_48` | 24.1 - 48 Lakhs |
| `48_1_plus` | 48.1+ Lakhs |
| `dont_know` | Don't Know |

### Age Group
| Value | Display Label |
|-------|--------------|
| `below_18` | Below 18 |
| `18_to_24` | 18 - 24 |
| `25_to_35` | 25 - 35 |
| `36_to_45` | 36 - 45 |
| `46_to_55` | 46 - 55 |
| `56_plus` | 56+ |
| `dont_know` | Don't Know |

### Task Priority
| Value | Display Label |
|-------|--------------|
| `high` | High |
| `medium` | Medium (default) |
| `low` | Low |

### Task Medium
| Value | Display Label |
|-------|--------------|
| `call` | Call |
| `whatsapp` | WhatsApp |
| `email` | Email |
| `in_person` | In Person |
| `video_call` | Video Call |

### Interaction Type (for touchpoints)
| Value | Display Label |
|-------|--------------|
| `meeting_office` | Meeting (Office) |
| `meeting_home` | Meeting (Home) |
| `cafe` | Cafe |
| `restaurant` | Restaurant |
| `call` | Call |
| `video_call` | Video Call |

### Touchpoint Status
| Value | Display Label |
|-------|--------------|
| `scheduled` | Scheduled (default) |
| `completed` | Completed |
| `cancelled` | Cancelled |
| `rescheduled` | Rescheduled |

### Opportunity Type (for business opportunities)
| Value | Display Label |
|-------|--------------|
| `sip` | SIP |
| `lumpsum` | Lumpsum |
| `swp` | SWP |
| `ncd` | NCD |
| `fd` | FD |
| `life_insurance` | Life Insurance |
| `health_insurance` | Health Insurance |
| `las` | LAS |

### Opportunity Stage
| Value | Display Label |
|-------|--------------|
| `identified` | Identified (default) |
| `inbound` | Inbound |
| `proposed` | Proposed |

### Opportunity Source
| Value | Display Label |
|-------|--------------|
| `goal_planning` | Goal Planning |
| `portfolio_rebalancing` | Portfolio Rebalancing |
| `client_servicing` | Client Servicing (default) |
| `financial_activities` | Financial Activities |

---

## Important Notes

1. **Phone numbers** — Always send as 10 digits only (e.g., `9876543210`). Never include `+91` or country code. The backend handles the conversion.

2. **Dates** — Always use `YYYY-MM-DD` format (e.g., `2026-03-28`).

3. **Times** — Always use `HH:MM` 24-hour format (e.g., `14:30`).

4. **UUIDs** — Client and Lead IDs are UUIDs (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`). Get them from the search endpoint.

5. **Enum values** — Must be sent exactly as shown in the Value column (lowercase, underscores). Sending an invalid value will return a 422 error.

6. **Required fields** — Currently all form fields are optional (except `mfd_phone`). Required fields will be enforced later — your bot will get a `422` error listing which fields are missing when that happens, so no code changes needed on your side.

7. **Error handling** — Always check the HTTP status code:
   - `200` = Success
   - `400` = Business logic error (e.g., missing client_id for touchpoint)
   - `401` = Invalid API key
   - `422` = Validation error (invalid field values, missing required fields)
   - `500` = Server error

---

## Suggested WhatsApp Conversation Flow

### Example: Creating a Lead

```
Bot:  What would you like to create?
User: Lead

Bot:  What is the lead's name?
User: Rahul Sharma

Bot:  What is their phone number? (10 digits)
User: 9123456789

Bot:  How did you source this lead?
      1. Natural Market
      2. Referral
      3. Social Networking
      4. Business Group
      5. Marketing Activity
      6. IAP
      7. Cold Call
      8. Social Media
User: 2

Bot:  Any other details? (Type 'done' to finish)
      - Email
      - Gender
      - Area
      - Occupation
      ... (show remaining optional fields)
User: done

Bot:  Creating lead... Done! Lead "Rahul Sharma" created successfully.
```
