# INFINITY SYNC - GOOGLE SHEETS ENUM AND COLUMN MAPPING

Complete mapping of column names and valid enum values for the three main sync sheets.

---

## LEADS SHEET

| Column Name | Type | Valid Values | Database Maps To | Required | Notes |
|---|---|---|---|---|---|
| Prospect Name | Text | Any text | - | ✅ YES | Row synced only if filled |
| Contact No | Phone | Any format | - | ❌ No | Optional |
| Email | Email | Valid email | - | ❌ No | Optional |
| Age Group | Enum | 18-24, 25-35, 36-45, 46-55, 56+, below 18, don't know | 18_to_24, 25_to_35, 36_to_45, 46_to_55, 56_plus, below_18, dont_know | ❌ No | Case-insensitive |
| Gender | Enum | Male, Female, Others | male, female, other | ❌ No | Case-insensitive |
| Marital Status | Enum | Single, Married, Divorced, Widower, Separated, Don't know | single, married, divorced, widower, separated, dont_know | ❌ No | Case-insensitive |
| Occupation | Enum | Service, Business, Retired, Professional, Student, Self Employed, Housemaker, Don't know | service, business, retired, professional, student, self_employed, housemaker, dont_know | ❌ No | Case-insensitive |
| Income Group | Enum | 1-2.5, 2.6-8.8, 8.9-12, 12.1-24, 24.1-48, 48.1+, don't know | l1_to_2_5, l2_6_to_8_8, l8_9_to_12, l12_1_to_24, l24_1_to_48, l48_1_plus, dont_know | ❌ No | Case-insensitive |
| Dependants | Number | Any number | - | ❌ No | Optional |
| Area | Text | Any text | - | ❌ No | Optional |
| Source of Data | Enum | natural market, referral, social networking, business group, marketing activity, iap, cold call, social media | natural_market, referral, social_networking, business_group, marketing_activity, iap, cold_call, social_media | ❌ No | Defaults to natural_market |
| Source Description | Text | Any text | - | ❌ No | Optional |
| Sourced By | Text | Any text | - | ❌ No | Optional |
| Status | Enum | follow up, meeting scheduled, cancelled, converted | follow_up, meeting_scheduled, cancelled, converted | ❌ No | Defaults to follow_up |
| Remarks / Notes | Text | Any text | - | ❌ No | Optional |
| Date | Date | DD/MM/YYYY | YYYY-MM-DD | ❌ No | Parsed automatically |
| Turn Around Time (TAT) | Number | Any number | - | ❌ No | Optional |

---

## CLIENT PROFILE SHEET

| Column Name | Type | Valid Values | Database Maps To | Required | Notes |
|---|---|---|---|---|---|
| Client Name | Text | Any text | - | ✅ YES | Row synced only if filled |
| Contact no. | Phone | Any format | - | ❌ No | Optional |
| Email ID | Email | Valid email | - | ❌ No | Optional |
| Address | Text | Any text | - | ❌ No | Optional |
| Area | Text | Any text | - | ❌ No | Optional |
| Birthdate | Date | DD/MM/YYYY | YYYY-MM-DD | ❌ No | Optional |
| Gender | Enum | Male, Female, Others | male, female, other | ❌ No | Case-insensitive |
| Marital Status | Enum | Single, Married, Divorced, Widower, Separated, Don't know | single, married, divorced, widower, separated, dont_know | ❌ No | Case-insensitive |
| Occupation | Enum | Service, Business, Retired, Professional, Student, Self Employed, Housemaker, Don't know | service, business, retired, professional, student, self_employed, housemaker, dont_know | ❌ No | Case-insensitive |
| Income Group | Enum | 1-2.5, 2.6-8.8, 8.9-12, 12.1-24, 24.1-48, 48.1+, don't know | l1_to_2_5, l2_6_to_8_8, l8_9_to_12, l12_1_to_24, l24_1_to_48, l48_1_plus, dont_know | ❌ No | Case-insensitive |
| Dependants | Number | Any number | - | ❌ No | Optional |
| Client Risk Profile | Text | Any text | - | ❌ No | Optional |
| Source | Enum | natural market, referral, social networking, business group, marketing activity, iap, cold call, social media | natural_market, referral, social_networking, business_group, marketing_activity, iap, cold_call, social_media | ❌ No | Case-insensitive |
| Source Description | Text | Any text | - | ❌ No | Optional |
| Sourced By | Text | Any text | - | ❌ No | Optional |
| Total AUM | Decimal | Any number | - | ❌ No | Optional |
| SIP | Decimal | Any number | - | ❌ No | Optional |
| Term Insurance | Decimal | Any number | - | ❌ No | Optional |
| Health Insurance | Decimal | Any number | - | ❌ No | Optional |
| PA Insurance | Decimal | Any number | - | ❌ No | Optional |
| SWP | Decimal | Any number | - | ❌ No | Optional |
| Corpus | Decimal | Any number | - | ❌ No | Optional |
| PMS | Decimal | Any number | - | ❌ No | Optional |
| AIF | Decimal | Any number | - | ❌ No | Optional |
| LAS | Decimal | Any number | - | ❌ No | Optional |
| LI Premium | Decimal | Any number | - | ❌ No | Optional |
| ULIPs | Decimal | Any number | - | ❌ No | Optional |
| Notes | Text | Any text | - | ❌ No | Optional |

---

## BUSINESS OPPORTUNITIES SHEET

| Column Name | Type | Valid Values | Database Maps To | Required | Notes |
|---|---|---|---|---|---|
| Sr No. | Number | Any number | - | ❌ No | Auto-generated |
| Client Name/Lead | Text | Any text | - | ❌ No | Reference only |
| Expected Amount | Decimal | Any number | - | ✅ YES | Row synced only if filled |
| Opportunity Stage | Enum | identified, inbound, proposed | identified, inbound, proposed | ✅ YES | Case-insensitive |
| Opportunity Type | Enum | sip, lumpsum, swp, ncd, fd, life_insurance, health_insurance, las | sip, lumpsum, swp, ncd, fd, life_insurance, health_insurance, las | ✅ YES | Case-insensitive |
| Opportunity Identified From | Enum | goal_planning, portfolio_rebalancing, client_servicing, financial_activities | goal_planning, portfolio_rebalancing, client_servicing, financial_activities | ✅ YES | Case-insensitive |
| Additional Info | Text | Any text | - | ❌ No | Optional |
| Due Date | Date | DD/MM/YYYY | YYYY-MM-DD | ❌ No | Optional |
| Time | Time | HH:MM | - | ❌ No | Optional |
| TAT | Number | Any number | - | ❌ No | Optional |

---

## IMPORTANT RULES

### 1. Column Names Must Match Exactly
- Column names are **case-sensitive**
- Extra spaces will cause lookup failure
- Use exact names from tables above

### 2. Enum Values Are Case-Insensitive
- `"Male"`, `"male"`, `"MALE"` → all map to `male`
- `"don't know"`, `"Don't know"` → all map to `dont_know`
- Spaces are auto-normalized

### 3. Row Filtering
- **Leads**: Synced only if **Prospect Name** is not empty
- **Clients**: Synced only if **Client Name** is not empty
- **Business Opportunities**: Synced only if **Expected Amount** is not empty

### 4. Automatic Deletion on Sync
- When you sync a sheet, **ALL previous rows** are deleted and replaced
- Ensures data consistency but means partial syncs remove old data

### 5. Sync Behavior
- **Manual Sync**: Edit a cell → 3 second debounce → webhook syncs that sheet
- **Full Sync**: Menu → all sheets with data sync
- **Auto-Sync**: Install trigger → automatic sync on every edit

---

## QUICK REFERENCE - ENUMS BY CATEGORY

### Age Group
- 18-24 → `18_to_24`
- 25-35 → `25_to_35`
- 36-45 → `36_to_45`
- 46-55 → `46_to_55`
- 56+ → `56_plus`
- below 18 → `below_18`
- don't know → `dont_know`

### Gender
- Male → `male`
- Female → `female`
- Others → `other`

### Marital Status
- Single → `single`
- Married → `married`
- Divorced → `divorced`
- Widower → `widower`
- Separated → `separated`
- Don't know → `dont_know`

### Occupation
- Service → `service`
- Business → `business`
- Retired → `retired`
- Professional → `professional`
- Student → `student`
- Self Employed → `self_employed`
- Housemaker → `housemaker`
- Don't know → `dont_know`

### Income Group
- 1-2.5 → `l1_to_2_5`
- 2.6-8.8 → `l2_6_to_8_8`
- 8.9-12 → `l8_9_to_12`
- 12.1-24 → `l12_1_to_24`
- 24.1-48 → `l24_1_to_48`
- 48.1+ → `l48_1_plus`
- Don't know → `dont_know`

### Source (Leads/Clients)
- natural market → `natural_market`
- referral → `referral`
- social networking → `social_networking`
- business group → `business_group`
- marketing activity → `marketing_activity`
- iap → `iap`
- cold call → `cold_call`
- social media → `social_media`

### Opportunity Stage
- identified → `identified`
- inbound → `inbound`
- proposed → `proposed`

### Opportunity Type
- sip → `sip`
- lumpsum → `lumpsum`
- swp → `swp`
- ncd → `ncd`
- fd → `fd`
- life insurance → `life_insurance`
- health insurance → `health_insurance`
- las → `las`

### Opportunity Source
- goal planning → `goal_planning`
- portfolio rebalancing → `portfolio_rebalancing`
- client servicing → `client_servicing`
- financial activities → `financial_activities`

### Lead Status
- follow up → `follow_up`
- meeting scheduled → `meeting_scheduled`
- cancelled → `cancelled`
- converted → `converted`

---

## TROUBLESHOOTING

| Issue | Solution |
|---|---|
| Data not syncing | Check column names match exactly, verify enum values from list |
| Only some rows syncing | Check required column (name/amount) is filled |
| Enum value errors in logs | Use exact values from "Valid Values" column |
| Column not recognized | Verify column header matches exactly (case-sensitive) |
| All data deleted on sync | This is normal - full sheet replacement ensures consistency |

