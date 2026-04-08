# Database Update Endpoints - JSON Examples

Complete list of endpoints that actually **INSERT/UPDATE/DELETE** data in your database with ready-to-use JSON examples.

---

## 🔥 Quick Test Endpoints (Updates Database)

### 1. Create Task → Updates `tasks` table

**Endpoint:** `POST /api/v1/tasks`

**Database Table:** `tasks`

**Sample JSON:**
```json
{
  "title": "Follow up with client",
  "description": "Discuss mutual fund investment options",
  "priority": "high",
  "due_date": "2026-02-28",
  "due_time": "10:00 AM",
  "medium": "phone",
  "reminder_date": "2026-02-27",
  "reminder_time": "09:00 AM"
}
```

**Minimal Example:**
```json
{
  "title": "Call client",
  "due_date": "2026-02-28"
}
```

**With Client ID:**
```json
{
  "title": "Review portfolio with client",
  "due_date": "2026-03-01",
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "priority": "medium"
}
```

**Priority Options:** `low`, `medium`, `high`
**Medium Options:** `phone`, `email`, `meeting`, `whatsapp`, `other`

---

### 2. Create Lead → Updates `leads` table

**Endpoint:** `POST /api/v1/leads`

**Database Table:** `leads`

**Sample JSON:**
```json
{
  "name": "Rajesh Kumar",
  "phone": "+919876543210",
  "email": "rajesh.kumar@example.com",
  "gender": "male",
  "marital_status": "married",
  "occupation": "salaried",
  "income_group": "10-20 lakhs",
  "area": "Mumbai",
  "source": "referral",
  "referred_by": "Amit Shah",
  "status": "follow_up",
  "scheduled_date": "2026-02-25",
  "scheduled_time": "11:00 AM",
  "notes": "Interested in retirement planning"
}
```

**Minimal Example (Required fields only):**
```json
{
  "name": "Priya Sharma",
  "phone": "+919123456789"
}
```

**Options:**
- **gender:** `male`, `female`, `other`
- **marital_status:** `single`, `married`, `divorced`, `widowed`
- **occupation:** `salaried`, `self_employed`, `business`, `professional`, `retired`, `student`, `homemaker`
- **income_group:** `<5 lakhs`, `5-10 lakhs`, `10-20 lakhs`, `20-50 lakhs`, `50 lakhs+`
- **source:** `referral`, `cold_call`, `event`, `social_media`, `website`, `walk_in`, `other`
- **status:** `new`, `follow_up`, `qualified`, `meeting_scheduled`, `proposal_sent`, `converted`, `lost`

---

### 3. Create Goal → Updates `goals` table

**Endpoint:** `POST /api/v1/goals`

**Database Table:** `goals`

**Sample JSON (Simple Goal):**
```json
{
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "goal_type": "retirement",
  "goal_name": "Retirement Planning",
  "target_amount": 10000000,
  "target_date": "2045-06-01",
  "current_investment": 500000,
  "monthly_sip": 25000,
  "expected_return_rate": 12.0
}
```

**Vehicle Goal:**
```json
{
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "goal_type": "vehicle",
  "goal_name": "Buy new car",
  "vehicle_type": "car",
  "target_amount": 1500000,
  "target_date": "2028-12-31",
  "current_investment": 200000,
  "monthly_sip": 15000,
  "expected_return_rate": 10.0
}
```

**Education Goal (with child):**
```json
{
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "goal_type": "child_education",
  "goal_name": "Son's Engineering Degree",
  "child_name": "Arjun",
  "child_current_age": 10,
  "target_age": 18,
  "target_amount": 3000000,
  "target_date": "2034-06-01",
  "monthly_sip": 20000,
  "expected_return_rate": 12.0
}
```

**Lifestyle Goal:**
```json
{
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "goal_type": "lifestyle",
  "goal_name": "Dream Vacation to Europe",
  "lifestyle_subtype": "vacation",
  "target_amount": 500000,
  "target_date": "2027-06-01",
  "monthly_sip": 8000,
  "expected_return_rate": 10.0
}
```

**Goal Type Options:**
- `retirement`
- `child_education`
- `child_wedding`
- `vehicle`
- `home_purchase`
- `lifestyle`
- `emergency_fund`
- `wealth_creation`
- `other`

**Vehicle Type Options:** `car`, `bike`, `commercial_vehicle`

**Lifestyle Subtype Options:** `vacation`, `home_renovation`, `wedding`, `other`

---

### 4. Update Task → Updates `tasks` table

**Endpoint:** `PUT /api/v1/tasks/{task_id}`

**Database Table:** `tasks`

**Sample JSON:**
```json
{
  "title": "Updated task title",
  "description": "Updated description",
  "priority": "high",
  "status": "completed",
  "due_date": "2026-03-01"
}
```

**Status Options:** `pending`, `in_progress`, `completed`, `cancelled`

---

### 5. Complete Task → Updates `tasks` table

**Endpoint:** `POST /api/v1/tasks/{task_id}/complete`

**Database Table:** `tasks`

**No JSON body needed** - just POST to the endpoint!

**Example:**
```bash
POST /api/v1/tasks/123e4567-e89b-12d3-a456-426614174001/complete
```

---

### 6. Update Lead Status → Updates `leads` table

**Endpoint:** `PATCH /api/v1/leads/{lead_id}/status`

**Database Table:** `leads`

**Sample JSON:**
```json
{
  "status": "meeting_scheduled",
  "scheduled_date": "2026-02-28",
  "scheduled_time": "03:00 PM",
  "notes": "Meeting confirmed with client"
}
```

---

### 7. Update Goal Progress → Updates `goals` table

**Endpoint:** `PATCH /api/v1/goals/{goal_id}/progress?current_investment=750000`

**Database Table:** `goals`

**Query Parameter:** `current_investment` (number)

**No JSON body needed!**

**Example:**
```
PATCH /api/v1/goals/123e4567-e89b-12d3-a456-426614174002/progress?current_investment=750000
```

---

## 🧪 How to Test These in Swagger UI

### Step 1: Start Backend
```bash
uvicorn app.main:app --reload
```

### Step 2: Open Swagger UI
```
http://localhost:8000/docs
```

### Step 3: Test Create Task Endpoint

1. Find `POST /api/v1/tasks` under "Tasks" section
2. Click "Try it out"
3. Paste this JSON:
```json
{
  "title": "Test task from Swagger",
  "due_date": "2026-02-28",
  "priority": "medium"
}
```
4. Click "Execute"
5. Check response - you should get a 201 status with the created task data

### Step 4: Verify in Database

Go to your Supabase dashboard → Table Editor → `tasks` table
You should see your new task!

---

## 📊 Complete Endpoint List with Database Tables

| Endpoint | Method | Database Table | Action |
|----------|--------|----------------|--------|
| `/api/v1/tasks` | POST | `tasks` | INSERT |
| `/api/v1/tasks/{id}` | PUT | `tasks` | UPDATE |
| `/api/v1/tasks/{id}` | DELETE | `tasks` | DELETE |
| `/api/v1/tasks/{id}/complete` | POST | `tasks` | UPDATE |
| `/api/v1/leads` | POST | `leads` | INSERT |
| `/api/v1/leads/{id}` | PUT | `leads` | UPDATE |
| `/api/v1/leads/{id}` | DELETE | `leads` | DELETE |
| `/api/v1/leads/{id}/status` | PATCH | `leads` | UPDATE |
| `/api/v1/goals` | POST | `goals` | INSERT |
| `/api/v1/goals/{id}` | PUT | `goals` | UPDATE |
| `/api/v1/goals/{id}` | DELETE | `goals` | DELETE |
| `/api/v1/goals/{id}/progress` | PATCH | `goals` | UPDATE |
| `/api/v1/clients` | POST | `clients` | INSERT |
| `/api/v1/clients/{id}` | PUT | `clients` | UPDATE |
| `/api/v1/touchpoints` | POST | `touchpoints` | INSERT |
| `/api/v1/notifications` | POST | `notifications` | INSERT |
| `/api/v1/documents` | POST | `documents` | INSERT |
| `/api/v1/calculators/gold-price` | GET | `gold_price_cache` | INSERT/UPDATE |

---

## 🔍 How to Check Database Updates

### Method 1: Supabase Dashboard
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click "Table Editor" (left sidebar)
4. Select the table (e.g., `tasks`, `leads`, `goals`)
5. Check the latest records

### Method 2: SQL Query
In Supabase SQL Editor, run:

```sql
-- Check recent tasks
SELECT * FROM tasks 
ORDER BY created_at DESC 
LIMIT 5;

-- Check recent leads
SELECT * FROM leads 
ORDER BY created_at DESC 
LIMIT 5;

-- Check recent goals
SELECT * FROM goals 
ORDER BY created_at DESC 
LIMIT 5;

-- Count records
SELECT 
  (SELECT COUNT(*) FROM tasks) as total_tasks,
  (SELECT COUNT(*) FROM leads) as total_leads,
  (SELECT COUNT(*) FROM goals) as total_goals;
```

---

## ⚠️ Important Notes

### Authentication Required
Most endpoints require authentication. In Swagger UI:
1. Look for 🔒 icon next to endpoints
2. Click "Authorize" button at top
3. Enter your Bearer token
4. Click "Authorize"

### UUID Format
When testing with `client_id`, `lead_id`, etc., use valid UUIDs from your database:
```
123e4567-e89b-12d3-a456-426614174000
```

### Phone Format
Phone numbers MUST be in this format:
```
+919876543210
```
(Country code +91 followed by 10 digits)

### Date Format
Dates must be in ISO format:
```
2026-02-28
```

---

## 🚀 Quick Testing Workflow

### Test 1: Create a Task
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "due_date": "2026-02-28"
  }'
```

### Test 2: Create a Lead
```bash
curl -X POST "http://localhost:8000/api/v1/leads" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Lead",
    "phone": "+919999999999"
  }'
```

### Test 3: Check Database
```sql
SELECT id, title, due_date, created_at 
FROM tasks 
ORDER BY created_at DESC 
LIMIT 1;

SELECT id, name, phone, created_at 
FROM leads 
ORDER BY created_at DESC 
LIMIT 1;
```

---

## 💡 Pro Tips

1. **Start Simple**: Use minimal JSON examples first
2. **Check Response**: 201 status = successfully created
3. **Get the ID**: Copy the returned `id` for update/delete operations
4. **Use Real Data**: Test with actual client scenarios
5. **Verify in DB**: Always check Supabase after testing

---

## 📝 Testing Checklist

- [ ] Create a task
- [ ] Update the task
- [ ] Complete the task
- [ ] Create a lead
- [ ] Update lead status
- [ ] Create a goal
- [ ] Update goal progress
- [ ] Verify all in Supabase dashboard

---

**Happy Testing! 🎉**

All these endpoints will **actually update your database** unlike the calculator endpoints!
