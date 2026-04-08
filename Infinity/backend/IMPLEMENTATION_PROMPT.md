# INFINITY SYNC - COMPLETE IMPLEMENTATION PROMPT

## PROJECT OBJECTIVE
Implement a bidirectional sync system between Google Sheets and PostgreSQL database for the Infinity CRM application, enabling automatic data synchronization across three main sheets: Leads, Client Profile, and Business Opportunities.

---

## SYSTEM ARCHITECTURE

### Components
1. **OAuth Flow**: Google authentication for user provisioning
2. **Template Sheet**: Pre-configured Google Sheet with Apps Script code
3. **Supabase Edge Functions**: Webhook handlers for data sync
4. **PostgreSQL Database**: Stores synced data with strict enum validation

### Key Features
- ✅ Automatic sheet copying on OAuth completion
- ✅ Real-time sync via cell edit triggers
- ✅ Enum value normalization and validation
- ✅ Automatic data deletion on sync (ensures consistency)
- ✅ 3-second debounce to prevent rapid-fire syncs

---

## DATA MAPPING SPECIFICATIONS

### LEADS SHEET - Complete Enum Mapping

**Sheet Tab Name**: `Leads`

| Column Name | Type | Required | Valid Values | Database Enum | Auto-Mapping |
|---|---|---|---|---|---|
| **Prospect Name** | Text | ✅ YES | Any text | - | None |
| Contact No | Phone | No | Any format | - | None |
| Email | Email | No | Valid email | - | None |
| Age Group | Enum | No | 18-24, 25-35, 36-45, 46-55, 56+, below 18, don't know | 18_to_24, 25_to_35, 36_to_45, 46_to_55, 56_plus, below_18, dont_know | Yes (hyphen→underscore, case-insensitive) |
| Gender | Enum | No | Male, Female, Others | male, female, other | Yes (case-insensitive) |
| Marital Status | Enum | No | Single, Married, Divorced, Widower, Separated, Don't know | single, married, divorced, widower, separated, dont_know | Yes (case-insensitive) |
| Occupation | Enum | No | Service, Business, Retired, Professional, Student, Self Employed, Housemaker, Don't know | service, business, retired, professional, student, self_employed, housemaker, dont_know | Yes (space→underscore, case-insensitive) |
| Income Group | Enum | No | 1-2.5, 2.6-8.8, 8.9-12, 12.1-24, 24.1-48, 48.1+, don't know | l1_to_2_5, l2_6_to_8_8, l8_9_to_12, l12_1_to_24, l24_1_to_48, l48_1_plus, dont_know | Yes (number prefix 'l', case-insensitive) |
| Dependants | Number | No | Any number | - | None |
| Area | Text | No | Any text | - | None |
| Source of Data | Enum | No | natural market, referral, social networking, business group, marketing activity, iap, cold call, social media | natural_market, referral, social_networking, business_group, marketing_activity, iap, cold_call, social_media | Yes (space→underscore, case-insensitive, defaults to natural_market) |
| Source Description | Text | No | Any text | - | None |
| Sourced By | Text | No | Any text | - | None |
| Status | Enum | No | follow up, meeting scheduled, cancelled, converted | follow_up, meeting_scheduled, cancelled, converted | Yes (space→underscore, case-insensitive, defaults to follow_up) |
| Remarks / Notes | Text | No | Any text | - | None |
| Date | Date | No | DD/MM/YYYY | YYYY-MM-DD | Yes (date format conversion) |
| Turn Around Time (TAT) | Number | No | Any number | - | None |

**Row Sync Rule**: Leads row is synced to database **only if Prospect Name column is not empty**

---

### CLIENT PROFILE SHEET - Complete Enum Mapping

**Sheet Tab Name**: `Client Profile`

| Column Name | Type | Required | Valid Values | Database Enum | Auto-Mapping |
|---|---|---|---|---|---|
| **Client Name** | Text | ✅ YES | Any text | - | None |
| Contact no. | Phone | No | Any format | - | None |
| Email ID | Email | No | Valid email | - | None |
| Address | Text | No | Any text | - | None |
| Area | Text | No | Any text | - | None |
| Birthdate | Date | No | DD/MM/YYYY | YYYY-MM-DD | Yes (date format conversion) |
| Gender | Enum | No | Male, Female, Others | male, female, other | Yes (case-insensitive) |
| Marital Status | Enum | No | Single, Married, Divorced, Widower, Separated, Don't know | single, married, divorced, widower, separated, dont_know | Yes (case-insensitive) |
| Occupation | Enum | No | Service, Business, Retired, Professional, Student, Self Employed, Housemaker, Don't know | service, business, retired, professional, student, self_employed, housemaker, dont_know | Yes (space→underscore, case-insensitive) |
| Income Group | Enum | No | 1-2.5, 2.6-8.8, 8.9-12, 12.1-24, 24.1-48, 48.1+, don't know | l1_to_2_5, l2_6_to_8_8, l8_9_to_12, l12_1_to_24, l24_1_to_48, l48_1_plus, dont_know | Yes (number prefix 'l', case-insensitive) |
| Dependants | Number | No | Any number | - | None |
| Client Risk Profile | Text | No | Any text | - | None |
| Source | Enum | No | natural market, referral, social networking, business group, marketing activity, iap, cold call, social media | natural_market, referral, social_networking, business_group, marketing_activity, iap, cold_call, social_media | Yes (space→underscore, case-insensitive) |
| Source Description | Text | No | Any text | - | None |
| Sourced By | Text | No | Any text | - | None |
| Total AUM | Decimal | No | Any number | - | None |
| SIP | Decimal | No | Any number | - | None |
| Term Insurance | Decimal | No | Any number | - | None |
| Health Insurance | Decimal | No | Any number | - | None |
| PA Insurance | Decimal | No | Any number | - | None |
| SWP | Decimal | No | Any number | - | None |
| Corpus | Decimal | No | Any number | - | None |
| PMS | Decimal | No | Any number | - | None |
| AIF | Decimal | No | Any number | - | None |
| LAS | Decimal | No | Any number | - | None |
| LI Premium | Decimal | No | Any number | - | None |
| ULIPs | Decimal | No | Any number | - | None |
| Notes | Text | No | Any text | - | None |

**Row Sync Rule**: Client row is synced to database **only if Client Name column is not empty**

---

### BUSINESS OPPORTUNITIES SHEET - Complete Enum Mapping

**Sheet Tab Name**: `Business Opportunities`

| Column Name | Type | Required | Valid Values | Database Enum | Auto-Mapping |
|---|---|---|---|---|---|
| Sr No. | Number | No | Any number | - | None |
| Client Name/Lead | Text | No | Any text | - | None (reference only) |
| **Expected Amount** | Decimal | ✅ YES | Any number | - | None |
| **Opportunity Stage** | Enum | ✅ YES | identified, inbound, proposed | identified, inbound, proposed | No (use exact values) |
| **Opportunity Type** | Enum | ✅ YES | sip, lumpsum, swp, ncd, fd, life_insurance, health_insurance, las | sip, lumpsum, swp, ncd, fd, life_insurance, health_insurance, las | No (use exact values) |
| **Opportunity Identified From** | Enum | ✅ YES | goal_planning, portfolio_rebalancing, client_servicing, financial_activities | goal_planning, portfolio_rebalancing, client_servicing, financial_activities | No (use exact values) |
| Additional Info | Text | No | Any text | - | None |
| Due Date | Date | No | DD/MM/YYYY | YYYY-MM-DD | Yes (date format conversion) |
| Time | Time | No | HH:MM | - | None |
| TAT | Number | No | Any number | - | None |

**Row Sync Rule**: Business Opportunity row is synced to database **only if Expected Amount column has a numeric value**

---

## ENUM NORMALIZATION RULES

### For Leads and Client Profile Sheets

1. **Age Group Mapping**
   - Input: `18-24` → Output: `18_to_24`
   - Input: `25-35` → Output: `25_to_35`
   - Input: `36-45` → Output: `36_to_45`
   - Input: `46-55` → Output: `46_to_55`
   - Input: `56+` → Output: `56_plus`
   - Input: `below 18` → Output: `below_18`
   - Input: `don't know` (any case) → Output: `dont_know`

2. **Gender Mapping**
   - Input: `Male` (case-insensitive) → Output: `male`
   - Input: `Female` (case-insensitive) → Output: `female`
   - Input: `Others` (case-insensitive) → Output: `other`

3. **Marital Status Mapping**
   - Input: Values normalized to lowercase with underscores
   - Input: `don't know` (any case) → Output: `dont_know`

4. **Occupation Mapping**
   - Input: `Self Employed` → Output: `self_employed`
   - Input: `don't know` (any case) → Output: `dont_know`
   - Other values: space→underscore, case-insensitive

5. **Income Group Mapping**
   - Input: `1-2.5` → Output: `l1_to_2_5`
   - Input: `2.6-8.8` → Output: `l2_6_to_8_8`
   - Input: `8.9-12` → Output: `l8_9_to_12`
   - Input: `12.1-24` → Output: `l12_1_to_24`
   - Input: `24.1-48` → Output: `l24_1_to_48`
   - Input: `48.1+` → Output: `l48_1_plus`
   - Input: `don't know` (any case) → Output: `dont_know`

6. **Source Mapping** (Leads/Clients)
   - Input: `natural market` → Output: `natural_market`
   - Input: `social networking` → Output: `social_networking`
   - Input: `business group` → Output: `business_group`
   - Input: `marketing activity` → Output: `marketing_activity`
   - Input: `cold call` → Output: `cold_call`
   - Input: `social media` → Output: `social_media`
   - Default: `natural_market`

7. **Lead Status Mapping**
   - Input: `follow up` → Output: `follow_up`
   - Input: `meeting scheduled` → Output: `meeting_scheduled`
   - Input: All other values: space→underscore, case-insensitive
   - Default: `follow_up`

### For Business Opportunities Sheet

**NO AUTO-MAPPING** - Use exact database enum values:

1. **Opportunity Stage** (Case-insensitive):
   - `identified`
   - `inbound`
   - `proposed`

2. **Opportunity Type** (Case-insensitive):
   - `sip`
   - `lumpsum`
   - `swp`
   - `ncd`
   - `fd`
   - `life_insurance`
   - `health_insurance`
   - `las`

3. **Opportunity Identified From** (Case-insensitive):
   - `goal_planning`
   - `portfolio_rebalancing`
   - `client_servicing`
   - `financial_activities`

---

## SYNC BEHAVIOR SPECIFICATIONS

### Manual Sync
1. User edits any cell in Leads, Client Profile, or Business Opportunities tab
2. `onEditTrigger()` fires (Apps Script)
3. 3-second debounce window (prevents multiple rapid syncs)
4. Webhook POST to `https://whjgmbptnlsxswehlfhq.supabase.co/functions/v1/sheets-webhook`
5. Webhook verifies secret: `your-webhook-secret-bffd0b2d86670879037f23b1e1776793d9bea9f22cbe48f32f675095078cbfb4`
6. **ALL previous rows deleted** (ensures clean state)
7. **Only non-empty rows synced** (filters out blank rows)
8. Data synced to corresponding PostgreSQL table

### Full Sync
1. User clicks "📥 Full Sync (All Data)" menu item
2. All three sheets (Leads, Client Profile, Business Opportunities) synced simultaneously
3. Same deletion/sync process as manual sync

### Auto-Sync (Optional)
1. User clicks "⚙️ Enable Auto-Sync" menu item
2. `setupTrigger()` installs `onEdit` trigger
3. Trigger automatically fires on every cell edit
4. Same 3-second debounce and sync logic

---

## DATA VALIDATION RULES

### Column Name Validation
- Column names are **case-sensitive**
- Extra spaces or typos prevent column lookup
- Exact column names from mapping tables MUST be used

### Enum Value Validation
- **Case-insensitive** (e.g., "Male", "male", "MALE" all valid)
- Space normalization (e.g., "don't know" matches `dont_know`)
- Leading/trailing spaces auto-trimmed
- Invalid enum values cause row rejection (logged as error)

### Required Field Validation
- **Leads**: Row rejected if `Prospect Name` is empty
- **Clients**: Row rejected if `Client Name` is empty
- **Business Opportunities**: Row rejected if `Expected Amount` is empty or non-numeric
- Other fields: Optional

### Data Type Validation
- **Phone**: Any format accepted (stored as text)
- **Email**: Basic validation (stored as text)
- **Number**: Integer or decimal accepted
- **Decimal**: Converts to numeric type
- **Date**: DD/MM/YYYY auto-converted to YYYY-MM-DD
- **Text**: Any content accepted

---

## DATABASE TABLES AND FOREIGN KEYS

### Leads Table
- **Columns**: id, user_id, name, phone, email, age_group, gender, marital_status, occupation, income_group, dependants, area, source, source_description, sourced_by, status, notes, scheduled_date, tat_days, created_at, updated_at
- **Primary Key**: id (UUID)
- **Foreign Key**: user_id → auth.users(id)
- **Unique Constraint**: None

### Clients Table
- **Columns**: id, user_id, name, phone, email, address, area, birthdate, gender, marital_status, occupation, income_group, dependants, risk_profile, source, source_description, sourced_by, total_aum, sip, term_insurance, health_insurance, pa_insurance, swp, corpus, pms, aif, las, li_premium, ulips, notes, created_at, updated_at
- **Primary Key**: id (UUID)
- **Foreign Key**: user_id → auth.users(id)
- **Unique Constraint**: None

### Business Opportunities Table
- **Columns**: id, user_id, expected_amount, opportunity_stage, opportunity_type, opportunity_source, additional_info, due_date, tat_days, created_at, updated_at
- **Primary Key**: id (UUID)
- **Foreign Key**: user_id → auth.users(id)
- **Unique Constraint**: None

---

## EDGE FUNCTION ENDPOINTS

### sheets-webhook
- **URL**: `https://whjgmbptnlsxswehlfhq.supabase.co/functions/v1/sheets-webhook`
- **Method**: POST
- **Headers Required**: `x-webhook-secret: your-webhook-secret-bffd0b2d86670879037f23b1e1776793d9bea9f22cbe48f32f675095078cbfb4`
- **Content-Type**: application/json
- **Payload Structure**:
  ```json
  {
    "sheetId": "spreadsheet-id",
    "sheetName": "sheet-tab-name",
    "rows": [
      {
        "column_name_1": "value_1",
        "column_name_2": "value_2"
      }
    ],
    "timestamp": "ISO8601-timestamp",
    "changeType": "edit" | "full_sync"
  }
  ```
- **Response**: `{ "success": true, "synced": number, "table": "table_name" }`
- **Error Response**: `{ "error": "error message" }`

---

## IMPLEMENTATION CHECKLIST

- ✅ OAuth flow configured and tested
- ✅ Template sheet created with Code.gs
- ✅ Supabase edge functions deployed
- ✅ Enum mapping implemented for Leads sheet
- ✅ Enum mapping implemented for Client Profile sheet
- ✅ Business Opportunities sync without auto-mapping
- ✅ Date parsing (DD/MM/YYYY → YYYY-MM-DD)
- ✅ Numeric parsing (handles decimals and integers)
- ✅ Row filtering (empty name/amount rows rejected)
- ✅ 3-second debounce implemented
- ✅ Webhook secret validation
- ✅ All-rows-delete-on-sync logic
- ✅ Error logging to Supabase logs
- ✅ Menu UI with sync options

---

## TROUBLESHOOTING GUIDE

| Problem | Cause | Solution |
|---|---|---|
| Data not syncing | Column name typo | Verify exact column name from mapping (case-sensitive) |
| | Empty required field | Check Prospect Name (Leads), Client Name (Clients), or Expected Amount (BO) is filled |
| | Invalid enum value | Use values from mapping table, ensure proper spacing |
| Only partial rows syncing | Mixed data quality | Some rows have missing required fields, others don't |
| Webhook errors in logs | RLS policy blocking | Service account has proper access |
| All data disappeared | Normal behavior | Sync deletes previous rows and replaces with new data |
| 3-second delay on sync | Expected behavior | Debounce prevents rapid-fire syncs |

---

## FUTURE ENHANCEMENTS

1. **Reverse Sync**: Database → Google Sheets (push updates)
2. **Conflict Resolution**: Handle simultaneous edits from multiple users
3. **Partial Sync**: Option to append instead of replacing all rows
4. **Audit Logging**: Track who synced what and when
5. **Data Validation UI**: Show errors directly in Apps Script UI
6. **Conditional Sync**: Sync only sheets with changes
7. **Scheduled Sync**: Automatic sync at set intervals
8. **Multi-Language Support**: Enum values in different languages

