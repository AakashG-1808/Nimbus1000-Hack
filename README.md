# UrbanGuard AI System

An AI-powered urban infrastructure monitoring and risk prediction system for Bengaluru, India.

## Overview

UrbanGuard AI is a comprehensive system that helps city officials monitor infrastructure complaints, predict potential incidents, and manage urban risks in real-time. The system uses AI classification, geographic clustering, and risk scoring algorithms to identify high-risk areas and predict incidents before they occur.

## Features

- **Real-time Complaint Monitoring**: Citizens can report infrastructure issues (potholes, flooding, traffic, garbage, etc.)
- **AI-Powered Classification**: Automatic categorization using Amazon Bedrock with keyword fallback
- **Risk Zone Visualization**: Interactive map showing risk hotspots with color-coded severity
- **Incident Prediction**: Predicts potential incidents in high-risk zones
- **Weather Integration**: Real-time weather data from OpenWeatherMap API
- **Traffic Analysis**: Simulated traffic congestion monitoring
- **Trend Analysis**: 7-day complaint volume and risk score trends
- **Daily Reports**: Automated daily risk assessment reports

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI/ML**: Amazon Bedrock (with keyword fallback)
- **APIs**: OpenWeatherMap API
- **Storage**: In-memory (development), DynamoDB (production)
- **Testing**: pytest, Hypothesis (property-based testing)

### Frontend
- **Framework**: React 18
- **Mapping**: Leaflet.js
- **Charts**: Chart.js with react-chartjs-2
- **HTTP Client**: Axios
- **Testing**: Jest, React Testing Library, fast-check (property-based testing)

## System Architecture

```
┌─────────────────┐
│   React Frontend │
│   (Port 3000)    │
└────────┬─────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Backend │
│   (Port 8000)    │
└────────┬─────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐
│Bedrock │ │Weather│ │Traffic │ │Storage │
│  AI    │ │  API  │ │Analyzer│ │        │
└────────┘ └──────┘ └────────┘ └────────┘
```

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 16 or higher
- **npm**: 8 or higher
- **OpenWeatherMap API Key** (optional, system works with fallback data)
- **AWS Credentials** (optional, for Bedrock AI features)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd urbanguard-ai-system
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (optional)
# Add your API keys:
# OPENWEATHERMAP_API_KEY=your_key_here
# AWS_ACCESS_KEY_ID=your_key_here
# AWS_SECRET_ACCESS_KEY=your_key_here
# CORS_ALLOW_ORIGINS=http://localhost:3000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

## Running the Application

### Start Backend Server

```bash
cd backend
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On macOS/Linux

python -m uvicorn main:app --reload --port 8000
```

The backend will be available at: http://localhost:8000

### Start Frontend Development Server

```bash
cd frontend
npm start
```

The frontend will be available at: http://localhost:3000

## Usage

1. **View Dashboard**: Open http://localhost:3000 in your browser
2. **Report Complaint**: Click the floating "Report Complaint" button
3. **Fill Form**: Select location, category, and describe the issue
4. **Submit**: Your complaint will appear on the map and feed within seconds
5. **Monitor**: Watch real-time updates every 30 seconds

## Testing

### Backend Tests

```bash
cd backend
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run property-based tests only
python -m pytest -k "property"
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run property-based tests only
npm test -- --testNamePattern="Property"
```

## Test Results

- **Backend**: All component tests passing
- **Frontend**: 148/149 tests passing (99.3%)
- **Property-Based Tests**: 100+ iterations per property
- **Total Properties Validated**: 50 correctness properties

## API Endpoints

### Complaints
- `POST /report-complaint` - Submit a new complaint
- `GET /complaints` - Get complaints (sorted by timestamp), supports `location`, `category`, `since`, `until`, `offset`, `limit`

### Risk & Analysis
- `GET /risk-hotspots` - Get risk zones (score > 20)
- `GET /weather` - Get current weather conditions
- `GET /traffic` - Get traffic congestion data
- `GET /daily-report` - Get latest daily risk report

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Performance

- **Complaint Submission**: < 500ms
- **Complaint Retrieval**: < 200ms (for 1000+ complaints)
- **Weather Data**: < 100ms
- **Traffic Data**: < 50ms
- **Risk Hotspots**: < 300ms
- **Daily Report**: < 200ms

## Data Models

### Complaint
- `location`: Bengaluru location name
- `category`: One of 8 types (pothole, flooding, traffic, garbage, streetlight, water_supply, noise, construction)
- `description`: Free-text description
- `timestamp`: ISO 8601 datetime
- `coordinates`: [latitude, longitude]

### Risk Zone
- `zone_id`: Unique identifier
- `center_coordinates`: [latitude, longitude]
- `risk_score`: 0-100 (LOW: 0-33, MEDIUM: 34-66, HIGH: 67-100)
- `complaint_count`: Number of complaints in zone
- `risk_level`: LOW, MEDIUM, or HIGH

## Configuration

### Backend Configuration
- Port: 8000 (configurable in `main.py`)
- CORS: Set `CORS_ALLOW_ORIGINS` (comma-separated or `*`), defaults to http://localhost:3000
- Polling Intervals:
  - Risk calculation: 15 minutes
  - Weather updates: 30 minutes
  - Traffic updates: 10 minutes

### Frontend Configuration
- Port: 3000 (configurable in `package.json`)
- API Base URL: http://localhost:8000
- Dashboard polling: 30 seconds

## Project Structure

```
urbanguard-ai-system/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Data models
│   ├── constants.py            # Bengaluru locations & categories
│   ├── complaint_processor.py  # Complaint validation & storage
│   ├── ai_classifier.py        # AI classification with fallback
│   ├── weather_integrator.py   # Weather API integration
│   ├── traffic_analyzer.py     # Traffic data generation
│   ├── cluster_detector.py     # Geographic clustering
│   ├── risk_engine.py          # Risk score calculation
│   ├── incident_predictor.py   # Incident prediction
│   ├── report_generator.py     # Daily report generation
│   ├── storage.py              # In-memory data storage
│   ├── simulated_data.py       # Test data generation
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js           # Main dashboard
│   │   │   ├── MapVisualizer.js       # Leaflet map
│   │   │   ├── ComplaintFeed.js       # Complaint list
│   │   │   ├── ComplaintForm.js       # Submission form
│   │   │   ├── TrendCharts.js         # Chart.js visualizations
│   │   │   ├── WeatherPanel.js        # Weather display
│   │   │   └── TrafficPanel.js        # Traffic display
│   │   ├── services/
│   │   │   └── api.js                 # API client
│   │   └── App.js                     # Root component
│   └── package.json            # Node dependencies
└── README.md                   # This file
```

## Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError`
- **Solution**: Ensure virtual environment is activated and dependencies are installed

**Issue**: Weather API errors
- **Solution**: System works with fallback data. Add API key to `.env` for real weather data

**Issue**: Port 8000 already in use
- **Solution**: Change port in `main.py` or stop the conflicting process

### Frontend Issues

**Issue**: `npm install` fails
- **Solution**: Delete `node_modules` and `package-lock.json`, then run `npm install` again

**Issue**: Map not displaying
- **Solution**: Check browser console for errors. Ensure backend is running on port 8000

**Issue**: CORS errors
- **Solution**: Set `CORS_ALLOW_ORIGINS` to include the frontend origin (for example: http://localhost:3000)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- OpenWeatherMap for weather data API
- Amazon Bedrock for AI classification
- Leaflet.js for mapping capabilities
- Chart.js for data visualization
- FastAPI and React communities

## Contact

For questions or support, please open an issue in the repository.

---

**Built with ❤️ for Bengaluru**
