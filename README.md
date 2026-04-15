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
cd Nimbus1000-Hack
```

2. Create Virtual Environment:

```bash

python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

3. Start backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

4. Start frontend (new terminal):

```bash
cd frontend
npm install
npm start
```

## Testing

Backend:

```bash
cd Nimbus1000-Hack//backend
python -m pytest
```

Frontend:

```bash
cd Nimbus1000-Hack/frontend
npm test -- --watchAll=false
```

## Documentation

- Main project docs: `Nimbus-1000-Urbanguard/README.md`
- Quick start: `Nimbus-1000-Urbanguard/QUICK_START.md`
- Detailed setup: `Nimbus-1000-Urbanguard/SETUP_GUIDE.md`

