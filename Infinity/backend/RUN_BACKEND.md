.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload





# Backend Setup & Run Guide

Complete guide to set up and run the FastAPI backend server.

---

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **pip**: Python package manager
- **Git**: Version control (if cloning)

---

## 🚀 Quick Start

### 1. Navigate to Backend Directory

```bash
cd Infinity/backend
```

### 2. Create Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:
```bash
copy .env.example .env
```

Edit `.env` file and add your API keys and credentials:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_JWT_SECRET=your_jwt_secret

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

WHATSAPP_NOTIF_ENDPOINT=your_whatsapp_endpoint
WHATSAPP_INPUT_ENDPOINT=your_whatsapp_input_endpoint
EMAIL_SERVICE_ENDPOINT=your_email_endpoint
WEBHOOK_API_KEY=your_webhook_key

FCM_SERVER_KEY=your_fcm_server_key
FCM_SENDER_ID=your_fcm_sender_id
```

### 5. Run the Backend Server

**Development Mode (with auto-reload):**
```bash
uvicorn app.main:app --reload
```

**Production Mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Custom Port:**
```bash
uvicorn app.main:app --reload --port 5000
```

**With Logging:**
```bash
uvicorn app.main:app --reload --log-level debug
```

---

## 🧪 Testing the API

### Interactive API Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

### Test with cURL

**Health Check:**
```bash
curl http://localhost:8000/
```

**Calculator Endpoint Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/calculators/sip-lumpsum-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "sip",
    "monthly_sip": 10000,
    "tenure_years": 15,
    "expected_return_percent": 12.0
  }'
```

**Gold Price Check:**
```bash
curl http://localhost:8000/api/v1/calculators/gold-price
```

---

## 📦 Available Endpoints

### Calculator Endpoints (`/api/v1/calculators/`)

1. **POST /sip-lumpsum-goal** - SIP/Lumpsum/Goal Calculator
2. **POST /vehicle** - Vehicle Purchase Planning
3. **POST /vacation** - Vacation Savings Planning
4. **POST /education** - Education Funding Calculator
5. **POST /wedding** - Wedding Planning Calculator
6. **POST /gold** - Gold Investment Calculator
7. **POST /retirement** - Retirement Planning Calculator
8. **POST /swp** - Systematic Withdrawal Plan
9. **POST /prepayment** - Loan Prepayment Calculator
10. **POST /cash-surplus** - Cash Flow Analyzer

### Utility Endpoints

- **GET /api/v1/calculators/products** - Investment Products List
- **GET /api/v1/calculators/destinations** - Vacation Destinations
- **GET /api/v1/calculators/wedding-pricing** - Wedding Pricing Table
- **GET /api/v1/calculators/loan-types** - Loan Types & Rates
- **GET /api/v1/calculators/banks** - Indian Banks List
- **GET /api/v1/calculators/gold-price** - Live Gold Prices

### Other Module Endpoints

- `/api/v1/clients` - Client Management
- `/api/v1/leads` - Lead Management
- `/api/v1/tasks` - Task Management
- `/api/v1/goals` - Goal Tracking
- `/api/v1/documents` - Document Management
- `/api/v1/notifications` - Notification System
- `/api/v1/dashboard` - Dashboard Data
- `/api/v1/profile` - User Profile
- And many more...

---

## 🛠️ Common Commands

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Freeze Current Dependencies
```bash
pip freeze > requirements.txt
```

### Check Python Version
```bash
python --version
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Run with Specific Workers (Production)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Run with SSL (HTTPS)
```bash
uvicorn app.main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
```

---

## 🐛 Troubleshooting

### ⚠️ CRITICAL: `pydantic_core._pydantic_core` Module Not Found Error

This is the most common error on Python 3.13. **Solution:**

**Option 1: Reinstall pydantic packages (RECOMMENDED)**
```bash
pip uninstall pydantic pydantic_core -y
pip install pydantic pydantic_core --no-cache-dir
```

**Option 2: Force reinstall all dependencies**
```bash
pip install -r requirements.txt --force-reinstall --no-cache-dir
```

**Option 3: Use Python 3.11 or 3.12 (Most Stable)**
```bash
# Check your Python version
python --version

# If using 3.13, consider downgrading to 3.11 or 3.12
# Download from: https://www.python.org/downloads/
```

**Option 4: Install Microsoft C++ Build Tools (if compilation needed)**
Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Port Already in Use
```bash
# Find process using port 8000 (Windows PowerShell)
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Module Not Found Error (General)
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt --no-cache-dir
```

### Permission Errors (Windows)
Run PowerShell as Administrator or change execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Environment Variables Not Loading
- Ensure `.env` file is in the `backend` directory
- Check file is named `.env` (not `.env.txt`)
- Restart the server after editing `.env`

---

## 📊 Development Tips

### Hot Reload
The `--reload` flag automatically restarts the server when code changes are detected.

### API Documentation
FastAPI automatically generates interactive docs - use them for testing!

### Logging
Check console output for errors and debug information.

### Database Connections
Ensure Supabase credentials are correct in `.env` file.

---

## 🔒 Security Notes

- **Never commit `.env` file** to version control
- Keep API keys and secrets secure
- Use environment variables for sensitive data
- Consider using `.env.local` for local overrides

---

## 📝 Quick Reference

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload` | Start dev server with auto-reload |
| `uvicorn app.main:app --port 5000` | Run on custom port |
| `pip install -r requirements.txt` | Install all dependencies |
| `pip list` | Show installed packages |
| `deactivate` | Exit virtual environment |

---

## 🎯 Next Steps

1. ✅ Start the backend server
2. ✅ Visit http://localhost:8000/docs
3. ✅ Test calculator endpoints
4. ✅ Configure frontend to connect to backend
5. ✅ Set up automated testing (optional)

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Uvicorn Docs**: https://www.uvicorn.org/
- **Python Docs**: https://docs.python.org/3/

---

**Happy Coding! 🚀**
