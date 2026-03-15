# UrbanGuard AI System - Setup Guide

Complete step-by-step guide to set up and run the UrbanGuard AI System.

## Quick Start (5 Minutes)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --reload --port 8000
```

✅ Backend running at http://localhost:8000

### 2. Frontend Setup (New Terminal)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

✅ Frontend running at http://localhost:3000

### 3. Access the Application

Open your browser and navigate to: **http://localhost:3000**

You should see the UrbanGuard AI Dashboard with:
- Interactive map of Bengaluru
- 60+ simulated complaints
- Real-time weather and traffic data
- Trend charts
- Complaint feed

## Detailed Setup Instructions

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: 3.11 or higher
- **Node.js**: 16.x or higher
- **npm**: 8.x or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for dependencies

### Verify Prerequisites

```bash
# Check Python version
python --version  # Should be 3.11+

# Check Node.js version
node --version  # Should be 16.x+

# Check npm version
npm --version  # Should be 8.x+
```

### Backend Setup (Detailed)

#### Step 1: Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Windows (CMD):
.venv\Scripts\activate.bat

# On macOS/Linux:
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

#### Step 2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)
- Boto3 (AWS SDK, optional)
- Requests (HTTP client)
- pytest (testing)
- Hypothesis (property-based testing)

#### Step 3: Configure Environment Variables (Optional)

Create a `.env` file in the `backend` directory:

```env
# OpenWeatherMap API (optional - system works without it)
OPENWEATHERMAP_API_KEY=your_api_key_here

# AWS Credentials (optional - for Bedrock AI)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# CORS configuration (optional)
# Comma-separated list of allowed origins or "*"
CORS_ALLOW_ORIGINS=http://localhost:3000
```

**Note**: The system works perfectly without these API keys using fallback mechanisms.

#### Step 4: Start Backend Server

```bash
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
✓ Initialized storage with 60 simulated complaints
✓ Started weather integrator
✓ Started traffic analyzer
✓ Started cluster detector
✓ Started risk engine
```

#### Step 5: Verify Backend

Open http://localhost:8000/docs in your browser to see the interactive API documentation.

### Frontend Setup (Detailed)

#### Step 1: Install Node Dependencies

```bash
cd frontend
npm install
```

This installs:
- React (UI framework)
- Leaflet.js (mapping)
- Chart.js (visualizations)
- Axios (HTTP client)
- Jest & React Testing Library (testing)
- fast-check (property-based testing)

#### Step 2: Configure Environment (Optional)

Create a `.env` file in the `frontend` directory:

```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

**Note**: This is the default value, so the file is optional.

#### Step 3: Start Development Server

```bash
npm start
```

The browser should automatically open to http://localhost:3000

You should see:
```
Compiled successfully!

You can now view urbanguard-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

### Troubleshooting

#### Backend Issues

**Problem**: `python: command not found`
- **Solution**: Install Python 3.11+ from python.org
- **Alternative**: Try `python3` instead of `python`

**Problem**: `pip: command not found`
- **Solution**: Reinstall Python with "Add to PATH" option checked

**Problem**: Virtual environment activation fails
- **Windows**: Run PowerShell as Administrator and execute:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **macOS/Linux**: Ensure you have execute permissions:
  ```bash
  chmod +x .venv/bin/activate
  ```

**Problem**: Port 8000 already in use
- **Solution 1**: Stop the process using port 8000
  ```bash
  # Windows
  netstat -ano | findstr :8000
  taskkill /PID <PID> /F
  
  # macOS/Linux
  lsof -ti:8000 | xargs kill -9
  ```
- **Solution 2**: Use a different port
  ```bash
  python -m uvicorn main:app --reload --port 8001
  ```
  Then update frontend `.env` to use port 8001

**Problem**: Module import errors
- **Solution**: Ensure virtual environment is activated (you should see `(.venv)` in prompt)
- **Verify**: Run `pip list` to see installed packages

#### Frontend Issues

**Problem**: `npm: command not found`
- **Solution**: Install Node.js from nodejs.org (includes npm)

**Problem**: `npm install` fails with permission errors
- **Windows**: Run terminal as Administrator
- **macOS/Linux**: Don't use `sudo` with npm. Fix permissions:
  ```bash
  sudo chown -R $USER ~/.npm
  ```

**Problem**: Port 3000 already in use
- **Solution**: The system will prompt you to use a different port (e.g., 3001)
- **Alternative**: Stop the process using port 3000

**Problem**: Map not displaying
- **Check**: Backend is running on port 8000
- **Check**: Browser console for errors (F12)
- **Check**: Network tab shows successful API calls

**Problem**: CORS errors in browser console
- **Solution**: Set `CORS_ALLOW_ORIGINS` to include the frontend origin
- **Example**: `CORS_ALLOW_ORIGINS=http://localhost:3000`

**Problem**: Blank page or white screen
- **Check**: Browser console for JavaScript errors
- **Try**: Clear browser cache and reload (Ctrl+Shift+R)
- **Try**: Delete `node_modules` and run `npm install` again

## Testing the Installation

### 1. Backend Health Check

```bash
# Test API is responding
curl http://localhost:8000/complaints

# Should return JSON array of complaints
```

### 2. Frontend Health Check

Open http://localhost:3000 and verify:
- ✅ Map displays with Bengaluru centered
- ✅ Complaint feed shows 20 recent complaints
- ✅ Weather panel shows temperature, humidity, etc.
- ✅ Traffic panel shows congestion levels
- ✅ Trend charts display data

### 3. Submit a Test Complaint

1. Click the "Report Complaint" button (bottom-right)
2. Fill in the form:
   - Location: Select any Bengaluru location
   - Category: Select a category
   - Description: Enter at least 10 characters
3. Click "Submit Complaint"
4. Verify: Complaint appears in the feed within 2 seconds

### 4. Run Automated Tests

**Backend Tests:**
```bash
cd backend
python -m pytest
```

Expected: All tests pass

**Frontend Tests:**
```bash
cd frontend
npm test -- --watchAll=false
```

Expected: 148/149 tests pass (99.3%)

## Development Workflow

### Making Changes

1. **Backend Changes**: 
   - Edit Python files in `backend/`
   - Server auto-reloads (thanks to `--reload` flag)
   - Test changes immediately

2. **Frontend Changes**:
   - Edit React files in `frontend/src/`
   - Browser auto-refreshes (hot reload)
   - See changes instantly

### Stopping the Servers

**Backend**: Press `Ctrl+C` in the terminal

**Frontend**: Press `Ctrl+C` in the terminal

### Restarting the Servers

Just run the start commands again:
```bash
# Backend
python -m uvicorn main:app --reload --port 8000

# Frontend
npm start
```

## Production Deployment

For production deployment, see:
- Task 22 in `tasks.md` for AWS Lambda deployment
- Build frontend for production: `npm run build`
- Use production ASGI server (Gunicorn + Uvicorn workers)

## Using DynamoDB for Persistent Storage

By default the backend uses **in-memory storage** (data is lost on restart). To persist data to **Amazon DynamoDB** set the following environment variables in `backend/.env`:

```env
USE_DYNAMODB=true

# AWS credentials
AWS_REGION=ap-south-2
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>

# Table names (these match the SAM template defaults)
DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints
DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones
DYNAMODB_TABLE_REPORTS=urbanguard-reports
DYNAMODB_TABLE_USERS=urbanguard-users
```

Tables must already exist in your AWS account. Deploy them in one step with AWS SAM:

```bash
cd backend
sam build
sam deploy --guided
```

### Local Development with DynamoDB Local

You can run DynamoDB locally (no AWS account required):

1. Download [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
2. Start it: `java -jar DynamoDBLocal.jar -sharedDb -port 8001`
3. Create the four tables (see `STORAGE_README.md` for the exact CLI commands)
4. Add to `backend/.env`:
   ```env
   USE_DYNAMODB=true
   DYNAMODB_ENDPOINT_URL=http://localhost:8001
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=dummy
   AWS_SECRET_ACCESS_KEY=dummy
   DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints
   DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones
   DYNAMODB_TABLE_REPORTS=urbanguard-reports
   DYNAMODB_TABLE_USERS=urbanguard-users
   ```
5. Start the backend: `python -m uvicorn main:app --reload --port 8000`

See `backend/STORAGE_README.md` for full details on the DynamoDB integration.

## Getting Help

- **API Documentation**: http://localhost:8000/docs
- **Check Logs**: Look at terminal output for errors
- **Browser Console**: Press F12 to see frontend errors
- **Test Suite**: Run tests to verify functionality

## Next Steps

1. ✅ System is running
2. 📊 Explore the dashboard
3. 📝 Submit test complaints
4. 🧪 Run the test suite
5. 🚀 Start customizing for your needs

---

**Happy Coding! 🎉**
