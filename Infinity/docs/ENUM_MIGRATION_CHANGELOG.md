# Enum Migration, model_dump Bug Fix & DB Schema Alignment

**Date:** 2026-03-19
**Scope:** `backend/app/constants/enums.py` + all services/models that consume enums or call `model_dump()`
**Total:** 5 models rewritten, 7 services patched, 2 routers patched, 1 enum file fully rewritten, ~30 `model_dump` call sites fixed

---

## Problems Found

### Problem 1: Enum values didn't match Supabase DB

The old Python enums had **prefixed `.value` strings** (`"l1_to_2_5"`, `"a18_to_24"`) that didn't match the actual PostgreSQL enum values (`"1_to_2_5"`, `"18_to_24"`). Some class names also used inconsistent casing (`AUMBracketType` vs `AumBracketType`).

### Problem 2: `model_dump()` date serialization bug

Every service used `data.model_dump(exclude_unset=True)` and passed the result directly to Supabase `.insert()`/`.update()`. Without `mode="json"`, Pydantic returns **Python objects** (`date`, `UUID`, `Enum`) — not strings. The Supabase client internally calls `json.dumps()`, which crashes on these types.

Services had ad-hoc workarounds (manual enum loops, `.isoformat()` calls) that were inconsistent and incomplete.

### Problem 3: Pydantic models didn't match DB schema

- **NOT NULL violations** — `leads.source`, `clients.gender`, `clients.source` are NOT NULL in DB but `Optional` in models
- **Type mismatches** — `clients.term_insurance`/`health_insurance` are `numeric` in DB but `bool` in models
- **Phantom fields** — Fields in models that don't exist as DB columns (`reminder_date`/`reminder_time` in tasks, `actual_date`/`notes`/`outcome` in touchpoint updates, `product_name` in business opportunities) — would cause PostgREST errors on insert/update
- **Field name mismatches** — API field names didn't match DB column names (`referred_by` vs `sourced_by`, `aum` vs `total_aum`, `sip_amount` vs `sip`) — would cause PostgREST unknown column errors
- **Missing DB columns** — Response models were missing columns that exist in DB (`google_event_id`, `completed_at`, `mom_audio_url`, etc.)

---

## All Changes Made

---

### 1. `enums.py` — Full rewrite

#### 1A. Enum value corrections (`.value` now matches DB exactly)

| Enum | Old value (Python) | New value (matches DB) |
|---|---|---|
| `IncomeGroupType` | `"l1_to_2_5"`, `"l2_6_to_8_8"`, etc. | `"1_to_2_5"`, `"2_6_to_8_8"`, etc. |
| `AgeGroupType` | `"a18_to_24"`, `"a25_to_35"`, etc. | `"18_to_24"`, `"25_to_35"`, etc. |
| `AumBracketType` | `"l10_to_25_lakhs"`, etc. | `"10_to_25_lakhs"`, etc. |
| `SipBracketType` | `"l5_1k_to_10k"`, etc. | `"5_1k_to_10k"`, etc. |

Python member names use `v_` prefix where needed (e.g., `v18_to_24 = "18_to_24"`) since Python identifiers can't start with digits.

#### 1B. Class renames

| Old name | New name |
|---|---|
| `AUMBracketType` | `AumBracketType` |
| `SIPBracketType` | `SipBracketType` |
| `OpportunityType` | `OpportunityTypeEnum` |
| `InvestmentTypeEnum` | `InvestmentType` |
| `TransactionTypeEnum` | `TransactionType` |
| `NotificationTypeEnum` | `NotificationType` |
| `MessageStatusType` | `MessageStatus` |

**Backward-compat aliases** added so existing imports don't break:
```python
OpportunityType = OpportunityTypeEnum
InvestmentTypeEnum = InvestmentType
TransactionTypeEnum = TransactionType
NotificationTypeEnum = NotificationType
MessageStatusType = MessageStatus
```

#### 1C. Removed members (no longer in DB enum)

| Enum | Removed members |
|---|---|
| `ProductCategoryType` | `equity`, `debt`, `hybrid`, `general_insurance` |
| `ProductStatusType` | `inactive`, `suspended`, `coming_soon`, `discontinued` |
| `InvestmentType` | `swp`, `stp`, `one_time`, `recurring` |
| `TransactionType` | `purchase`, `sip`, `swp`, `stp_in`, `stp_out`, `dividend_reinvest`, `dividend_payout` |

#### 1D. New enums added

| Enum | Purpose |
|---|---|
| `ClientTenureType` | Client relationship duration brackets |
| `CalculatorType` | Calculator types (sip_lumpsum_goal, vehicle, etc.) |
| `CalculationModeType` | target_based / investment_based |
| `SipModeType` | SIP calculation modes |
| `StepUpType` | Step-up types (none, amount, percentage) |
| `PrepaymentStrategyType` | Loan prepayment strategies |
| `GoldPurityType` | Gold purity (24, 22, 18, 14, 13) |
| `GoldPurposeType` | Gold purpose (jewellery, coins, bars, investment) |
| `GoldUnitType` | Gold units (grams, kg) |
| `VacationPackageType` | Vacation tiers |
| `WeddingType` | Wedding scale types |
| `LoanType` | Loan categories |
| `FundType` | Fund types (equity, debt) |
| `PackageTierType` | Package tiers (standard, premium, diamond) |

#### 1E. Kept (app-logic only, not DB enums)

`VoiceInputStatus`, `IntentType`, `InputMode` — used by voice/OCR processing, not stored as DB enum types.

---

### 2. Import & member reference fixes

| File | Change |
|---|---|
| `models/client.py` | `AUMBracketType` → `AumBracketType`, `SIPBracketType` → `SipBracketType` |
| `services/client_service.py` | Same import rename + all member references updated (`a18_to_24` → `v18_to_24`, `l10_to_25_lakhs` → `v10_to_25_lakhs`, `l5_1k_to_10k` → `v5_1k_to_10k`, etc.) |

---

### 3. `model_dump(mode="json")` fix — 16 files, 30+ call sites

Every `model_dump()` and `model_dump(exclude_unset=True)` changed to include `mode="json"`.

**What `mode="json"` does:**
- `date(2026, 3, 19)` → `"2026-03-19"`
- `UUID("550e8400-...")` → `"550e8400-..."`
- `GenderType.male` → `"male"`
- `time(7, 0)` → `"07:00:00"`

#### 3A. Files changed

| File | Call sites fixed |
|---|---|
| `services/lead_service.py` | `create_lead`, `update_lead` |
| `services/client_service.py` | `create_client`, `update_client` |
| `services/touchpoint_service.py` | `create_touchpoint`, `update_touchpoint` |
| `services/task_service.py` | `create_task`, `update_task` |
| `services/bo_service.py` | `create_opportunity`, `update_opportunity` |
| `services/goal_service.py` | `create_goal`, `update_goal` |
| `services/client_product_service.py` | `create_client_product`, `update_client_product`, `add_transaction` |
| `services/profile_service.py` | `create_profile`, `update_profile` |
| `services/campaign_service.py` | `create_campaign`, `update_campaign` |
| `services/scheduler_service.py` | `create_scheduled_notification` |
| `services/template_service.py` | `create_template`, `update_template` |
| `services/calculator_service.py` | `_get_weighted_return`, `_check_supports_monthly` |
| `services/voice/queue.py` | `_make_degraded_result`, `process_voice_job` |
| `services/ocr/queue.py` | `_make_degraded_result`, `process_ocr_job` |
| `routers/webhooks.py` | 3 webhook handlers |
| `routers/pdfs.py` | `generate_gold_calculator_pdf` |

#### 3B. Redundant manual conversion code removed

| Pattern removed | Was in |
|---|---|
| `for key, value in data.items(): if hasattr(value, "value"): data[key] = value.value` | lead_service, client_service, touchpoint_service, task_service, bo_service, goal_service |
| Manual `.isoformat()` on dates | bo_service, client_product_service, scheduler_service |
| Manual `str(uuid)` on UUIDs | client_product_service |
| Manual `[p.model_dump() for p in products]` inside goal_service | goal_service (`mode="json"` handles nested models) |

---

### 4. NOT NULL enforcement (was Optional, now required)

| Model | Field | Before → After |
|---|---|---|
| `LeadCreate` | `source` | `Optional[SourceType] = None` → `SourceType` (required) |
| `ClientCreate` | `gender` | `Optional[GenderType] = None` → `GenderType` (required) |
| `ClientCreate` | `source` | `Optional[SourceType] = None` → `SourceType` (required) |

---

### 5. Type mismatches fixed

| Model | Field | Old type | New type (matches DB `numeric`) |
|---|---|---|---|
| `ClientCreate` | `term_insurance` | `Optional[bool]` | `Optional[float]` |
| `ClientCreate` | `health_insurance` | `Optional[bool]` | `Optional[float]` |
| `ClientUpdate` | `term_insurance` | `Optional[bool]` | `Optional[float]` |
| `ClientUpdate` | `health_insurance` | `Optional[bool]` | `Optional[float]` |
| `ClientResponse` | `term_insurance` | `Optional[bool]` | `Optional[float]` |
| `ClientResponse` | `health_insurance` | `Optional[bool]` | `Optional[float]` |

---

### 6. Phantom fields removed (not in DB → would cause PostgREST errors)

| Model | Removed fields |
|---|---|
| `TaskCreate` | `reminder_date`, `reminder_time` |
| `TaskUpdate` | `reminder_date`, `reminder_time` |
| `TaskResponse` | `reminder_date`, `reminder_time` |
| `TouchpointUpdate` | `actual_date`, `actual_time`, `duration_minutes`, `notes`, `outcome` |
| `TouchpointResponse` | `actual_date`, `actual_time`, `duration_minutes`, `notes`, `outcome` |
| `BOCreate` | `product_name` |
| `BOUpdate` | `product_name` |
| `BOResponse` | `product_name` |

> **Note:** `TouchpointComplete` still has `actual_date`, `actual_time`, `duration_minutes`, `notes`, `outcome` — these are used by the service to build `mom_text`, not sent to DB directly.

---

### 7. Field name mapping (API name ≠ DB column name)

| API field | DB column | Tables | Model fix | Service fix |
|---|---|---|---|---|
| `referred_by` | `sourced_by` | leads, clients | `validation_alias="sourced_by"` on Response | Service pops `referred_by`, sets `sourced_by` |
| `aum` | `total_aum` | clients | `validation_alias="total_aum"` on Response | Service pops `aum`, sets `total_aum` |
| `sip_amount` | `sip` | clients | `validation_alias="sip"` on Response | Service pops `sip_amount`, sets `sip` |
| `original_due_date` | `original_date` | tasks | `validation_alias="original_date"` on Response | Service already writes `original_date` |

All Response models with aliases use `populate_by_name=True` so both the API name and DB column name are accepted.

#### Service-layer mapping code added

| File | Method | What was popped/remapped |
|---|---|---|
| `services/lead_service.py` | `create_lead` | `referred_by` → `sourced_by` |
| `services/lead_service.py` | `update_lead` | `referred_by` → `sourced_by` |
| `services/client_service.py` | `create_client` | `aum` → `total_aum`, `sip_amount` → `sip`, `referred_by` → `sourced_by` |
| `services/client_service.py` | `update_client` | `aum` → `total_aum`, `sip_amount` → `sip`, `referred_by` → `sourced_by` |
| `services/client_service.py` | `convert_from_lead` | `"referred_by"` → `"sourced_by"` in hardcoded dict |

---

### 8. Missing DB columns added to models

| Model | New fields added |
|---|---|
| `LeadCreate`/`LeadUpdate` | `age_group`, `dependants`, `source_description`, `all_day` |
| `LeadResponse` | `age_group`, `dependants`, `source_description`, `all_day`, `converted_to_client_id`, `conversion_date`, `tat_days`, `google_event_id` |
| `ClientResponse` | `dependants`, `conversion_date`, `google_event_id` |
| `TaskCreate`/`TaskUpdate` | `all_day`, `product_type`, `is_business_opportunity` |
| `TaskResponse` | `all_day`, `product_type`, `is_business_opportunity`, `google_event_id` |
| `TouchpointResponse` | `completed_at`, `mom_audio_url`, `mom_sent_to_client`, `mom_sent_at`, `google_event_id` |
| `BOResponse` | `due_time`, `google_event_id` |

---

## How to verify

```bash
# 1. No model_dump() without mode="json" in services/routers:
grep -rn "model_dump()" backend/app/services/ backend/app/routers/ --include="*.py"
# Expected: 0 results (only mode="json" variants)

# 2. No old enum member references:
grep -rn "\.a18_to_24\|\.l10_to_25\|\.l5_1k" backend/app/ --include="*.py"
# Expected: 0 results

# 3. No old class names without alias coverage:
grep -rn "AUMBracketType\|SIPBracketType" backend/app/ --include="*.py"
# Expected: 0 results

# 4. No phantom fields in task models:
grep -rn "reminder_date\|reminder_time" backend/app/models/task.py
# Expected: 0 results

# 5. No phantom fields in touchpoint update/response:
grep -n "actual_date\|actual_time\|duration_minutes" backend/app/models/touchpoint.py
# Expected: only in TouchpointComplete, NOT in TouchpointUpdate or TouchpointResponse

# 6. No product_name in business opportunity models:
grep -rn "product_name" backend/app/models/business_opportunity.py
# Expected: 0 results

# 7. referred_by mapped to sourced_by in services:
grep -n "sourced_by" backend/app/services/lead_service.py backend/app/services/client_service.py
# Expected: mapping code in create/update methods
```
