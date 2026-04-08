# 📊 **Schema Verification Report**

## **Cross-Check: Database Schema vs. Google Sheets Structure**

---

## **Sheet 1: LEADS**

### Sheet Columns (from your template):
```
Sr No | Month | Date | Prospect Name | Age Group | Gender | Marital Status |
Occupation | Income Group | Dependants | Contact No | Area | Sourced By |
Source of Data | Source Description | Remarks | Conversion Date | 
Turn Around Time (TAT)
```

### Database Schema (from app/models/lead.py):
```python
- id (UUID) ← Sr No
- name (str) ← Prospect Name
- phone (str) ← Contact No
- email (optional)
- gender (GenderType) ← Gender ✅
- marital_status (MaritalStatusType) ← Marital Status ✅
- occupation (OccupationType) ← Occupation ✅
- income_group (IncomeGroupType) ← Income Group ✅
- area (str) ← Area ✅
- source (SourceType) ← Source of Data / Sourced By ✅
- referred_by (str) ← can store "Sourced By"
- status (LeadStatusType) ← lead status
- scheduled_date (date)
- scheduled_time (time)
- notes (str) ← Remarks / Notes ✅
- created_at (datetime) ← Month/Date
- updated_at (datetime)
```

### ✅ MAPPING ANALYSIS:

| Sheet Column | DB Column | Status | Notes |
|---|---|---|---|
| Sr No | id | ✅ | Auto-generated UUID |
| Prospect Name | name | ✅ | Direct match |
| Contact No | phone | ✅ | Direct match |
| Gender | gender | ✅ | Enum type |
| Marital Status | marital_status | ✅ | Enum type |
| Occupation | occupation | ✅ | Enum type |
| Income Group | income_group | ✅ | Enum type |
| Area | area | ✅ | Text field |
| Sourced By | referred_by | ✅ | Name of referrer |
| Source of Data | source | ✅ | Enum type |
| Remarks | notes | ✅ | Text field |
| Month/Date | created_at | ✅ | System timestamp |
| Age Group | ⚠️ NOT IN DB | ⚠️ | **MISSING - need to add** |
| Dependants | ⚠️ NOT IN DB | ⚠️ | **MISSING - need to add** |
| Conversion Date | ⚠️ PARTIAL | ⚠️ | Can track with status = "converted" |
| Turn Around Time (TAT) | ⚠️ NOT IN DB | ⚠️ | **MISSING - calculated field** |

### ❌ ISSUES & FIXES NEEDED:
1. **Age Group** - Not in database, needs migration
2. **Dependants** - Not in database, needs migration
3. **Conversion Date** - Not explicitly tracked (can use updated_at when status="converted")
4. **TAT (Turn Around Time)** - Calculated field (conversion_date - created_at)

---

## **Sheet 2: CLIENTS**

### Sheet Columns:
```
Sr No | Client Name | notes | Touchpoints | Client Creation Year |
Source | Source Description | Birthdate | Age Group | Age | Gender |
Marital Status | Occupation | Income Group | Dependants | Contact no. |
Email ID | Area | Client Risk Profile | Total AUM of Client | SIP | Term |
Health | PA | SWP Corpus | PMS | AIF | LAS | LI Premium | ULIPs
```

### Database Schema (from app/models/client.py):
```python
- id (UUID) ← Sr No
- name (str) ← Client Name ✅
- phone (str) ← Contact no. ✅
- email (EmailStr) ← Email ID ✅
- birthdate (date) ← Birthdate ✅
- age (int) ← Age (calculated from birthdate) ✅
- age_group (AgeGroupType) ← Age Group ✅
- gender (GenderType) ← Gender ✅
- marital_status (MaritalStatusType) ← Marital Status ✅
- occupation (OccupationType) ← Occupation ✅
- income_group (IncomeGroupType) ← Income Group ✅
- area (str) ← Area ✅
- address (str)
- risk_profile (RiskProfileType) ← Client Risk Profile ✅
- source (SourceType) ← Source ✅
- referred_by (str) ← Source Description (referrer name)
- term_insurance (bool) ← Term ✅
- health_insurance (bool) ← Health ✅
- aum (float) ← Total AUM of Client ✅
- aum_bracket (AUMBracketType) ← calculated bracket
- sip_amount (float) ← SIP ✅
- sip_bracket (SIPBracketType) ← calculated bracket
- notes (str) ← notes ✅
- created_at (datetime) ← Client Creation Year/Date
- updated_at (datetime)
```

### ✅ MAPPING ANALYSIS:

| Sheet Column | DB Column | Status | Notes |
|---|---|---|---|
| Sr No | id | ✅ | Auto UUID |
| Client Name | name | ✅ | Direct match |
| Contact no. | phone | ✅ | Direct match |
| Email ID | email | ✅ | Direct match |
| Birthdate | birthdate | ✅ | Direct match |
| Age Group | age_group | ✅ | Enum/calculated |
| Age | age | ✅ | Calculated from birthdate |
| Gender | gender | ✅ | Enum |
| Marital Status | marital_status | ✅ | Enum |
| Occupation | occupation | ✅ | Enum |
| Income Group | income_group | ✅ | Enum |
| Area | area | ✅ | Text |
| Client Risk Profile | risk_profile | ✅ | Enum |
| Source | source | ✅ | Enum |
| Source Description | referred_by | ✅ | Text |
| Total AUM of Client | aum | ✅ | Float |
| SIP | sip_amount | ✅ | Float |
| Term | term_insurance | ✅ | Boolean |
| Health | health_insurance | ✅ | Boolean |
| notes | notes | ✅ | Text |
| **Touchpoints** | ⚠️ SEPARATE TABLE | ℹ️ | Linked via client_id in touchpoints table |
| **Client Creation Year** | created_at | ✅ | Can extract year |
| **PA** | ⚠️ NOT IN DB | ❌ | **MISSING** |
| **SWP Corpus** | ⚠️ NOT IN DB | ❌ | **MISSING** |
| **PMS** | ⚠️ NOT IN DB | ❌ | **MISSING** |
| **AIF** | ⚠️ NOT IN DB | ❌ | **MISSING** |
| **LAS** | ⚠️ NOT IN DB | ❌ | **MISSING** |
| **LI Premium** | ⚠️ NOT IN DB | ❌ | **MISSING** |
| **ULIPs** | ⚠️ NOT IN DB | ❌ | **MISSING** |
| **Dependants** | ⚠️ NOT IN DB | ❌ | **MISSING** |

### ❌ ISSUES & FIXES NEEDED:
1. **Product Holdings** - PA, SWP, PMS, AIF, LAS, LI Premium, ULIPs not in clients table
   - **SOLUTION**: Create separate `client_products` table OR add columns to clients
2. **Dependants** - Not stored, needs migration
3. **Touchpoints** - Stored separately, good design ✅

---

## **Sheet 3: BUSINESS OPPORTUNITIES**

### Sheet Columns:
```
Sr No. | Client Name/Lead | Expected Amount | Opportunity Stage |
Opportunity Type | Opportunity Identified From | Additional Info |
Due Date | Time | TAT (Turn Around Time)
```

### Database Schema (from app/models/business_opportunity.py):
```python
- id (UUID) ← Sr No.
- client_id (UUID) ← Client Name (linked)
- lead_id (UUID) ← Lead (alternative to client)
- client_name (str) ← Client Name/Lead
- lead_name (str) ← Lead Name (alternative)
- opportunity_type (OpportunityType) ← Opportunity Type ✅
- opportunity_stage (OpportunityStageType) ← Opportunity Stage ✅
- opportunity_source (OpportunitySourceType) ← Opportunity Identified From ✅
- expected_amount (float) ← Expected Amount ✅
- due_date (date) ← Due Date ✅
- product_name (str) ← can store product info
- notes (str) ← Additional Info ✅
- outcome (BOOutcomeType) ← outcome status
- outcome_date (date) ← outcome date
- outcome_amount (float) ← outcome amount
- tat_days (int) ← TAT (Turn Around Time) - calculated ✅
- created_at (datetime)
- updated_at (datetime)
```

### ✅ MAPPING ANALYSIS:

| Sheet Column | DB Column | Status | Notes |
|---|---|---|---|
| Sr No. | id | ✅ | Auto UUID |
| Client Name/Lead | client_id / lead_id | ✅ | Flexible linking |
| Expected Amount | expected_amount | ✅ | Direct match |
| Opportunity Stage | opportunity_stage | ✅ | Enum |
| Opportunity Type | opportunity_type | ✅ | Enum |
| Identified From | opportunity_source | ✅ | Enum |
| Additional Info | notes | ✅ | Text |
| Due Date | due_date | ✅ | Date |
| Time | ⚠️ NOT IN DB | ⚠️ | **MISSING - can store in notes** |
| TAT | tat_days | ✅ | Calculated field (outcome_date - created_date) |

### ✅ **NO MAJOR ISSUES** - Good alignment!

---

## **Sheet 4: READ-ONLY DASHBOARD**

### Status: ✅ **PERFECT**

This gets data from DB as shown in the image. No direct mapping needed.

---

## **Sheet 5: ALL CLIENTS (Comprehensive List)**

### Status: ⚠️ **DUPLICATION CONCERN**

This appears to be a view of all clients with duplicated columns (SIP, Term, Health, PA, SWP, etc. with "2" suffix).

**Observation**: These seem to be tracking multiple products per client.

**Schema Issue**: Current clients table only has:
- `sip_amount` (single value)
- `term_insurance` (boolean)
- `health_insurance` (boolean)

But sheet tracks:
- SIP, SIP 2 (multiple products)
- Term, Term 2
- Health, Health 2
- PA, PA 2
- etc.

---

## **🚨 SUMMARY OF ISSUES**

### **High Priority (Block Deployment):**
1. ❌ **Product Holdings Columns Missing** (PA, SWP, PMS, AIF, LAS, LI Premium, ULIPs)
   - **Impact**: Cannot sync these columns from sheet to DB
   - **Solution**: Add to clients table OR create client_products table
   
2. ❌ **Multiple Product Tracking**
   - Sheet tracks: SIP, SIP 2 | Term, Term 2 | etc.
   - DB only has: sip_amount, term_insurance (no "2" versions)
   - **Impact**: Cannot handle multiple product instances per client
   - **Solution**: Refactor to separate products table

### **Medium Priority (Can Work Around):**
1. ⚠️ **Dependants Column**
   - Missing in both Leads and Clients
   - **Solution**: Add to migration
   
2. ⚠️ **Age Group in Leads**
   - Missing in Leads table
   - **Solution**: Add to migration
   
3. ⚠️ **TAT (Turn Around Time)**
   - Need to calculate: conversion_date - created_date
   - **Solution**: Calculated field in sheets formula

### **Low Priority (Can Ignore):**
1. ℹ️ Time field in Business Opportunities
   - Not critical, can use notes field

---

## **RECOMMENDATION BEFORE DEPLOYMENT**

### **Option A: Deploy Now (Limited Sync)**
- ✅ Sync: Name, Phone, Email, Gender, Marital Status, Occupation, Income Group, Area, Risk Profile, Source, Notes, AUM, SIP amount, Term Insurance, Health Insurance
- ❌ Don't sync: Product holdings (PA, SWP, PMS, AIF, LAS, LI Premium, ULIPs), Dependants

### **Option B: Pause & Fix Schema (Recommended)**
- Add missing columns to database
- Add Dependants field to Leads and Clients
- Refactor product tracking (separate table or JSON field)
- Then deploy with full sync capability

---

## **What Should We Do?**

1. **Quick Ask**: Should product holdings be:
   - A) Separate `client_products` table (cleaner)?
   - B) JSON column in clients table (simpler)?
   - C) Add multiple columns (sip_2, term_2, etc.)?

2. **Dependants Field**: Should this be:
   - A) Integer (number of dependants)?
   - B) Text (names of dependants)?
   - C) Boolean (has dependants yes/no)?

Once clarified, I can:
- Create database migrations
- Update the sync logic
- Deploy functions with full capability

**Proceed or pause?** 🤔
