# Testing with Swagger UI - Complete Guide

Step-by-step guide to test all your API endpoints using FastAPI's built-in Swagger UI.

---

## 🚀 Step 1: Start Your Backend Server

First, make sure your backend is running:

```bash
cd Infinity/backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1234] using StatReload
INFO:     Started server process [5678]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 🌐 Step 2: Access Swagger UI

Open your web browser and go to:

**http://localhost:8000/docs**

or

**http://127.0.0.1:8000/docs**

You'll see an interactive API documentation page with all your endpoints listed.

---

## 📋 Understanding the Swagger UI Interface

### Main Components:

1. **API Title** - "MFD Digital Diary API" at the top
2. **Endpoint Groups** - Organized by tags (Calculators, Clients, Leads, etc.)
3. **HTTP Methods** - Color-coded:
   - 🟢 **GET** (Green) - Retrieve data
   - 🟡 **POST** (Yellow) - Create/Calculate data
   - 🔵 **PUT** (Blue) - Update data
   - 🔴 **DELETE** (Red) - Delete data

4. **Endpoint Path** - The URL path for each endpoint
5. **Expand/Collapse** - Click on any endpoint to see details

---

## 🧪 Step 3: Testing an Endpoint (Example: SIP Calculator)

Let's test the **SIP/Lumpsum/Goal Calculator** endpoint:

### 1. Find the Endpoint

Scroll to the **Calculators** section and find:

```
POST /api/v1/calculators/sip-lumpsum-goal
```

### 2. Click to Expand

Click on the endpoint row to expand it. You'll see:
- **Description** - What the endpoint does
- **Parameters** - What data it needs
- **Request Body Schema** - The JSON structure
- **Responses** - Possible response codes

### 3. Click "Try it out"

Click the **"Try it out"** button on the right side.

The request body editor will become editable.

### 4. Enter Test Data

Replace the example JSON with your test data:

```json
{
  "mode": "sip",
  "monthly_sip": 10000,
  "tenure_years": 15,
  "expected_return_percent": 12.0,
  "step_up_percent": 0,
  "existing_investment": 0
}
```

### 5. Click "Execute"

Click the blue **"Execute"** button.

### 6. View Response

Scroll down to see:

**Request URL:**
```
http://localhost:8000/api/v1/calculators/sip-lumpsum-goal
```

**Response Body:**
```json
{
  "mode": "sip",
  "total_invested": 1800000,
  "total_corpus": 4997887,
  "total_gains": 3197887,
  "monthly_sip": 10000,
  "tenure_years": 15,
  "expected_return_percent": 12.0
}
```

**Response Code:**
```
200 OK
```

---

## 📝 Testing Other Calculator Endpoints

### 1. Vehicle Calculator

**Endpoint:** `POST /api/v1/calculators/vehicle`

**Sample Request:**
```json
{
  "vehicle_type": "car",
  "current_price": 1500000,
  "years_to_purchase": 3,
  "inflation_rate_percent": 5.0,
  "down_payment_percent": 20,
  "loan_tenure_years": 5,
  "loan_interest_rate_percent": 9.5,
  "expected_return_percent": 12.0,
  "mode": "target_based"
}
```

### 2. Gold Calculator

**Endpoint:** `POST /api/v1/calculators/gold`

**Sample Request:**
```json
{
  "purity": "24k",
  "quantity_grams": 100,
  "purpose": "jewellery",
  "unit": "grams",
  "years_to_purchase": 5,
  "price_per_gram": 7500,
  "inflation_rate_percent": 8.0,
  "expected_return_percent": 12.0,
  "mode": "target_based"
}
```

### 3. Retirement Calculator

**Endpoint:** `POST /api/v1/calculators/retirement`

**Sample Request:**
```json
{
  "current_age": 35,
  "retirement_age": 60,
  "life_expectancy": 80,
  "current_monthly_expense": 50000,
  "expense_inflation_percent": 6.0,
  "expected_return_percent": 12.0,
  "post_retirement_return_percent": 8.0,
  "current_savings": {
    "mf": 500000,
    "stocks": 200000,
    "ppf": 300000
  }
}
```

### 4. Cash Surplus Calculator

**Endpoint:** `POST /api/v1/calculators/cash-surplus`

**Sample Request:**
```json
{
  "period": "monthly",
  "income": {
    "salary": 100000,
    "rent_income": 20000,
    "dividend_income": 5000,
    "interest_income": 3000
  },
  "insurance": {
    "life_insurance": 5000,
    "health_insurance": 3000,
    "motor_insurance": 2000
  },
  "savings": {
    "mutual_funds": 15000,
    "stocks": 5000,
    "ppf": 5000
  },
  "loans": [
    {
      "loan_type": "home",
      "emi_amount": 25000,
      "pending_amount": 5000000
    }
  ],
  "expenses": {
    "household": 15000,
    "ration_grocery": 10000,
    "medicine_health": 5000,
    "transport_fuel": 8000,
    "entertainment": 5000
  }
}
```

---

## 🔍 Testing GET Endpoints (Utility Endpoints)

GET endpoints don't require a request body - just click "Try it out" and "Execute"!

### 1. Get Investment Products

**Endpoint:** `GET /api/v1/calculators/products`

**Steps:**
1. Find the endpoint
2. Click "Try it out"
3. Click "Execute"
4. View the list of all investment products with default returns

### 2. Get Live Gold Price

**Endpoint:** `GET /api/v1/calculators/gold-price`

**Steps:**
1. Find the endpoint
2. Click "Try it out"
3. (Optional) Set `force_refresh` to `true` if you want fresh data
4. Click "Execute"
5. View live gold prices for all purities

### 3. Get Vacation Destinations

**Endpoint:** `GET /api/v1/calculators/destinations`

**Steps:**
1. Click "Try it out"
2. Click "Execute"
3. View all destinations with base prices

---

## 🎯 Advanced Testing Features

### 1. Using Query Parameters

Some endpoints have query parameters:

**Example:** `GET /api/v1/calculators/gold-price?force_refresh=true`

In Swagger UI:
1. Click "Try it out"
2. You'll see a checkbox or field for `force_refresh`
3. Set it to `true` or `false`
4. Click "Execute"

### 2. Testing with Authentication (if required)

If your API requires authentication:

1. Look for the **"Authorize"** button at the top right
2. Click it and enter your API key or token
3. Click "Authorize"
4. Now all requests will include authentication

### 3. Copying cURL Commands

After executing a request:

1. Scroll to the response section
2. Find the **"curl"** command
3. Copy it to use in terminal/scripts

Example:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/calculators/sip-lumpsum-goal' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "mode": "sip",
  "monthly_sip": 10000,
  "tenure_years": 15,
  "expected_return_percent": 12.0
}'
```

### 4. Viewing Response Schemas

Click on **"Schema"** tab in the Request Body section to see:
- All available fields
- Required vs optional fields
- Data types
- Default values
- Field descriptions

---

## ⚠️ Common Response Codes

| Code | Meaning | Description |
|------|---------|-------------|
| **200** | ✅ OK | Request successful |
| **201** | ✅ Created | Resource created successfully |
| **400** | ❌ Bad Request | Invalid input data |
| **404** | ❌ Not Found | Endpoint or resource not found |
| **422** | ❌ Validation Error | Request body validation failed |
| **500** | ❌ Server Error | Internal server error |

---

## 🐛 Troubleshooting Swagger UI

### Error: "Failed to fetch"

**Solution:**
- Check if backend is running (`uvicorn app.main:app --reload`)
- Check console for errors
- Verify URL is correct (http://localhost:8000/docs)

### Error: 422 Unprocessable Entity

**Solution:**
- Check your JSON syntax (missing commas, brackets)
- Verify all required fields are provided
- Check data types (strings, numbers, booleans)
- View the error response for specific field issues

### Error: 400 Bad Request

**Solution:**
- Read the error message in the response
- Check if values are within valid ranges
- Verify enum values (e.g., "sip" not "SIP")

### JSON Syntax Issues

Common mistakes:
```json
// ❌ WRONG - Trailing comma
{
  "mode": "sip",
  "monthly_sip": 10000,
}

// ✅ CORRECT
{
  "mode": "sip",
  "monthly_sip": 10000
}
```

```json
// ❌ WRONG - Using single quotes
{
  'mode': 'sip'
}

// ✅ CORRECT - Use double quotes
{
  "mode": "sip"
}
```

---

## 💡 Pro Tips

### 1. Use the Schema as Reference
Click the "Schema" button to see all available fields and their descriptions.

### 2. Save Common Requests
Copy successful request bodies to a text file for reuse.

### 3. Test Edge Cases
Try testing with:
- Minimum values
- Maximum values
- Zero values
- Negative values (should fail)
- Missing required fields (should fail)

### 4. Compare with Examples
Look at the endpoint description for usage examples.

### 5. Test in Order
For complex workflows:
1. Test GET endpoints first (to see available data)
2. Then test POST endpoints (to create/calculate)
3. Then test PUT/DELETE if needed

---

## 📊 Testing All Calculator Endpoints Checklist

Use this checklist to test all calculators:

- [ ] **SIP/Lumpsum/Goal** - Test all modes (sip, lumpsum, goal_sip, goal_lumpsum, goal_both)
- [ ] **Vehicle** - Test car and bike scenarios
- [ ] **Vacation** - Test different destinations and package types
- [ ] **Education** - Test with multiple children and goals
- [ ] **Wedding** - Test different wedding types and tiers
- [ ] **Gold** - Test different purities and purposes
- [ ] **Retirement** - Test with current savings and irregular income
- [ ] **SWP** - Test with accumulation and withdrawal phases
- [ ] **Prepayment** - Test all loan types and scenarios
- [ ] **Cash Surplus** - Test monthly and yearly periods

**Utility Endpoints:**
- [ ] Get investment products
- [ ] Get vacation destinations
- [ ] Get wedding pricing
- [ ] Get loan types
- [ ] Get Indian banks
- [ ] Get live gold price

---

## 🎓 Example Testing Session

### Complete Workflow Example:

1. **Start Backend**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Open Swagger UI**
   - Go to http://localhost:8000/docs

3. **Test a Simple GET Endpoint**
   - Open `GET /api/v1/calculators/products`
   - Click "Try it out" → "Execute"
   - Verify you get a list of products

4. **Test a POST Calculator**
   - Open `POST /api/v1/calculators/sip-lumpsum-goal`
   - Click "Try it out"
   - Enter test data
   - Click "Execute"
   - Verify response shows correct calculations

5. **Test with Different Modes**
   - Try mode: "lumpsum"
   - Try mode: "goal_sip"
   - Try mode: "goal_both"

6. **Save Successful Requests**
   - Copy working JSON examples
   - Save to a file for future reference

---

## 🔗 Alternative: ReDoc Documentation

FastAPI also provides ReDoc (better for reading):

**URL:** http://localhost:8000/redoc

**Features:**
- Cleaner layout
- Better for documentation browsing
- Not interactive (can't test directly)
- Great for sharing API docs with team

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Swagger UI Guide:** https://swagger.io/tools/swagger-ui/
- **JSON Validator:** https://jsonlint.com/

---

## ✅ Quick Start Summary

1. Run: `uvicorn app.main:app --reload`
2. Visit: http://localhost:8000/docs
3. Find endpoint → Click to expand
4. Click "Try it out"
5. Edit request body
6. Click "Execute"
7. View response

**That's it! Happy Testing! 🚀**