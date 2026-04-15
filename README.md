# Nimbus1000-Hack

This repository contains **UrbanGuard AI System**, an AI-powered urban infrastructure monitoring and risk prediction platform for Bengaluru.

## Repository Layout

```text
Nimbus1000-Hack/
└── Nimbus-1000-Urbanguard/
    ├── backend/    # FastAPI backend
    ├── frontend/   # React frontend
    ├── README.md
    ├── QUICK_START.md
    └── SETUP_GUIDE.md
```

## Project Features

- Complaint reporting and monitoring
- AI-assisted complaint categorization
- Risk hotspot detection and visualization
- Weather and traffic context integration
- Trend analytics and daily risk reporting

## Quick Start

1. Move into the main project directory:

```bash
cd /home/runner/work/Nimbus1000-Hack/Nimbus1000-Hack/Nimbus-1000-Urbanguard
```

2. Start backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

3. Start frontend (new terminal):

```bash
cd /home/runner/work/Nimbus1000-Hack/Nimbus1000-Hack/Nimbus-1000-Urbanguard/frontend
npm install
npm start
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Testing

Backend:

```bash
cd /home/runner/work/Nimbus1000-Hack/Nimbus1000-Hack/Nimbus-1000-Urbanguard/backend
python -m pytest
```

Frontend:

```bash
cd /home/runner/work/Nimbus1000-Hack/Nimbus1000-Hack/Nimbus-1000-Urbanguard/frontend
npm test -- --watchAll=false
```

## Documentation

- Main project docs: `Nimbus-1000-Urbanguard/README.md`
- Quick start: `Nimbus-1000-Urbanguard/QUICK_START.md`
- Detailed setup: `Nimbus-1000-Urbanguard/SETUP_GUIDE.md`

