# UrbanGuard AI - Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- OpenWeatherMap API key (get free at https://openweathermap.org/api)
- AWS account with Bedrock access (optional for development)

## Automated Setup

### Linux/macOS
```bash
chmod +x setup.sh
./setup.sh
```

### Windows
```cmd
setup.bat
```

## Manual Setup

### Backend Setup

1. Create Python virtual environment:
```bash
cd backend
python -m venv venv
```

2. Activate virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the server:
```bash
python main.py
```

Backend will be available at: http://localhost:8000

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env
```

3. Start development server:
```bash
npm start
```

Frontend will open at: http://localhost:3000

## Project Structure

```
urbanguard-ai-system/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # Application entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment template
│   └── .gitignore            # Git ignore rules
│
├── frontend/                  # React frontend
│   ├── public/               # Static files
│   │   └── index.html       # HTML template
│   ├── src/                 # React source code
│   │   ├── App.js          # Main App component
│   │   ├── App.css         # App styles
│   │   ├── index.js        # React entry point
│   │   └── index.css       # Global styles
│   ├── package.json         # Node dependencies
│   ├── .env.example        # Environment template
│   └── .gitignore          # Git ignore rules
│
├── .gitignore               # Root git ignore
├── README.md                # Full documentation
├── QUICK_START.md          # This file
├── setup.sh                # Linux/macOS setup script
└── setup.bat               # Windows setup script
```

## Configuration

### Backend Environment Variables (.env)

```env
# Required for weather integration
OPENWEATHERMAP_API_KEY=your_api_key_here

# Required for AI classification (optional for development)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
BEDROCK_MODEL_ID=anthropic.claude-v2
```

### Frontend Environment Variables (.env)

```env
# Backend API URL
REACT_APP_API_URL=http://localhost:8000

# Map configuration (Bengaluru coordinates)
REACT_APP_MAP_CENTER_LAT=12.9716
REACT_APP_MAP_CENTER_LNG=77.5946
REACT_APP_MAP_ZOOM=12
```

## Verify Installation

### Test Backend
```bash
curl http://localhost:8000
# Should return: {"message":"UrbanGuard AI System API"}
```

### Test Frontend
Open http://localhost:3000 in your browser
- Should see "UrbanGuard AI System" header

## Next Steps

After setup is complete:

1. **Implement Core Components** (Task 1.2)
   - Complaint processor
   - AI classifier
   - Risk engine

2. **Add Data Integration** (Task 1.3)
   - Weather API integration
   - Traffic data processing

3. **Build Frontend UI** (Task 1.4)
   - Map visualization
   - Dashboard components

4. **Write Tests** (Task 1.5)
   - Unit tests
   - Property-based tests

## Troubleshooting

### Python virtual environment issues
- Make sure Python 3.8+ is installed: `python --version`
- Try `python3` instead of `python` on some systems

### Node/npm issues
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

### Port already in use
- Backend (8000): Change port in `backend/main.py`
- Frontend (3000): Set `PORT=3001` in frontend/.env

### API key issues
- Verify OpenWeatherMap API key is active
- Check AWS credentials have Bedrock permissions

## Getting Help

- Check README.md for detailed documentation
- Review requirements.md in .kiro/specs/urbanguard-ai-system/
- Review design.md for architecture details

## Development Workflow

1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm start`
3. Make changes (hot-reload enabled)
4. Run tests: `pytest` (backend) or `npm test` (frontend)
5. Commit changes with descriptive messages

## Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- Uvicorn - ASGI server
- Boto3 - AWS SDK
- Requests - HTTP client
- Hypothesis - Property-based testing

**Frontend:**
- React - UI library
- Leaflet.js - Interactive maps
- Chart.js - Data visualizations
- Axios - HTTP client
- fast-check - Property-based testing
