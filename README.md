# UrbanGuard AI System

An AI-powered urban infrastructure monitoring and risk prediction system for Bengaluru, India.

---

## Detailed Project Explanation

### Problem Statement

Bengaluru, one of India's fastest-growing metropolises, faces constant urban infrastructure challenges — from waterlogged roads and potholes to traffic gridlock and garbage overflow. City officials lack a unified, real-time view of where problems are clustering, how severe they are, and where an incident is likely to happen next. Thousands of complaints pour in daily through civic portals, but they are rarely correlated geographically or analytically. As a result, resources are reactive rather than proactive, and high-risk neighborhoods often go unnoticed until a crisis unfolds.

**UrbanGuard AI** was built for the Nimbus 1000 hackathon to solve exactly this problem: give city administrators an intelligent, data-driven command centre that transforms raw citizen complaints into actionable risk intelligence — before incidents happen.

---

### What UrbanGuard AI Does

UrbanGuard AI is a full-stack web application with an AI brain at its core. In real time it:

1. **Accepts** infrastructure complaints from citizens (via a web form or API).
2. **Classifies** each complaint automatically into one of 8 infrastructure categories using Amazon Bedrock (Claude model) — or a keyword-based fallback when Bedrock is unavailable.
3. **Clusters** complaints geographically: any group of 5 or more complaints within a 500-metre radius in the past 24 hours becomes a *high-density cluster*.
4. **Scores** every cluster as a *Risk Zone* on a 0–100 scale, factoring in complaint density, live weather conditions, and traffic congestion.
5. **Predicts** the most likely urban incident for every high-risk zone, with a 6- or 24-hour time window.
6. **Visualises** everything on an interactive Leaflet.js map — colour-coded from green (low risk) through orange (medium) to red (high risk) — so city staff can see hotspots at a glance.
7. **Generates** a natural-language daily risk-assessment report at 06:00 every day, powered by Bedrock's Claude model.

---

### Architecture & Data Flow

```
Citizen Web Browser
       │  (complaint form / dashboard view)
       ▼
┌──────────────────────┐
│   React 18 Frontend  │  Port 3000
│  ┌────────────────┐  │
│  │ Dashboard      │  │  ← polling every 30 s
│  │ MapVisualizer  │  │
│  │ ComplaintForm  │  │
│  │ TrendCharts    │  │
│  │ WeatherPanel   │  │
│  │ TrafficPanel   │  │
│  │ Predictions    │  │
│  │ AIInsights     │  │
│  └────────────────┘  │
└──────────┬───────────┘
           │  REST / JSON
           ▼
┌──────────────────────────────────────────────────────┐
│              FastAPI Backend  (Port 8000)             │
│                                                      │
│  POST /report-complaint ──► ComplaintProcessor       │
│                                    │                 │
│                                    ▼                 │
│                             AIClassifier             │
│                          (Bedrock → keyword)         │
│                                    │                 │
│                             Storage (in-memory)      │
│                                    │                 │
│  ┌─────────────────────────────────┘                 │
│  │  Background schedulers (every 15 min)             │
│  │                                                   │
│  │  ClusterDetector ──► RiskEngine ──► IncidentPredictor │
│  │    (Haversine geo-clustering)         (6h / 24h)      │
│  │                     │                            │
│  │              WeatherIntegrator ◄── OpenWeatherMap │
│  │              TrafficAnalyzer   (simulated)        │
│  │                                                   │
│  │  ReportGenerator (daily 06:00, Bedrock summary)   │
│  └───────────────────────────────────────────────────┘
│                                                      │
│  GET /risk-hotspots  GET /weather  GET /traffic      │
│  GET /daily-report   GET /complaints                 │
└──────────────────────────────────────────────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
Amazon Bedrock  OpenWeatherMap
 (Claude AI)       API
```

**Step-by-step data flow for a complaint:**

1. Citizen fills the form → `POST /report-complaint`.
2. `ComplaintProcessor` validates location (must be one of 44 named Bengaluru areas) and category.
3. `AIClassifier` sends the description + location to Amazon Bedrock Claude. If Bedrock is unavailable (circuit breaker open, timeout, or no credentials), it falls back to keyword matching across 8 category-specific word lists.
4. The classified complaint (with confidence score 0–1) is saved to in-memory storage.
5. Every 15 minutes, `ClusterDetector` runs: it reads all complaints from the past 24 hours and groups them using the Haversine formula. Any two complaints within 500 m of each other belong to the same cluster.
6. `RiskEngine` converts each cluster into a `RiskZone` with a 0–100 risk score:
   - **Base score** — complaint density (complaints per km²). Density ≥ 5/km² → 50 base points; scales linearly below that.
   - **Weather modifier** — high rainfall (> 10 mm/hr from OpenWeatherMap) adds up to +30 points for flood-related zones.
   - **Traffic modifier** — high congestion (score = 10) adds up to +15 points for traffic-related zones.
   - Risk level: **LOW** (0–33) / **MEDIUM** (34–66) / **HIGH** (67–100).
7. `IncidentPredictor` scans every zone with `risk_score > 25`:
   - Determines incident type from the zone's dominant complaint category (e.g., `pothole` → `road_damage`, `flooding` → `flooding`).
   - Special rules: high rainfall + flooding complaints → `flooding`; high traffic + traffic complaints → `traffic_gridlock`.
   - Sets a time window: `risk_score > 50` → *next 6 hours*; otherwise → *next 24 hours*.
8. `ReportGenerator` aggregates all of the above at 06:00 and asks Bedrock Claude to write a 2–3 sentence natural-language risk summary for city officials.

---

### Component Deep-Dive

#### 1. AI Classifier (`ai_classifier.py`)

The classifier is the first intelligent layer. It uses a **circuit-breaker pattern** (5-failure threshold, 60-second timeout) to protect against Bedrock outages. When the circuit is closed it calls Bedrock's Claude model with a few-shot prompt:

```
Classify the following complaint into exactly ONE of these categories:
pothole, flooding, traffic, garbage, streetlight, water_supply, noise, construction

Complaint Location: Koramangala
Complaint Description: "Large crater on the main road, burst drainage pipe nearby"

Respond with ONLY the category name followed by a confidence score (0.0–1.0):
```

Bedrock returns `"pothole,0.92"`. The classifier validates the category against the allowed list and clamps the confidence to [0, 1].

**Fallback**: Each category has a curated keyword list (e.g., `pothole` → `["pothole", "road damage", "crater", "hole in road", "broken road"]`). The fallback counts keyword hits per category and returns the winner with a confidence capped at 0.9 (never as confident as the AI).

#### 2. Geographic Cluster Detector (`cluster_detector.py`)

Clusters are detected with a simple but effective greedy algorithm using the **Haversine formula** (accurate great-circle distances on Earth's surface):

1. For each unassigned complaint, find all other complaints within 500 m of it.
2. Group them into a cluster; compute the centroid as the geographic mean of all coordinates.
3. Calculate `density_per_km²` = `count / (π × (0.5 km)²)`.
4. Flag the cluster as `is_high_density` if it has ≥ 5 complaints in the last 24 hours.

The detector runs as a background thread every 15 minutes, storing results in a thread-safe cache.

#### 3. Risk Engine (`risk_engine.py`)

The risk engine translates cluster density into an actionable 0–100 risk score:

| Factor | Condition | Points added |
|--------|-----------|-------------|
| Complaint density | ≥ 5/km² | +50 (scales linearly below) |
| High rainfall | > 10 mm/hr & flooding/water zone | +30 |
| High traffic congestion | congestion score = 10 & traffic zone | +15 |

Scores are clamped to [0, 100] and classified LOW/MEDIUM/HIGH. Zones with score > 20 are surfaced via the `/risk-hotspots` API for map visualisation.

#### 4. Incident Predictor (`incident_predictor.py`)

For every zone with `risk_score > 25`, the predictor:

- Maps the dominant complaint category to a specific incident type. The 8 complaint categories map to 9 incident types: the `traffic` category can yield either `traffic_congestion` (normal) or `traffic_gridlock` (under high-congestion conditions), and an `infrastructure_issue` catch-all handles unexpected inputs.
- Applies environmental override rules: active rainfall + flooding zone → guaranteed `flooding` incident; city-wide high traffic + traffic zone → `traffic_gridlock`.
- Assigns a time window based on score intensity.
- Lists contributing factors (e.g., `["high_complaint_density", "high_rainfall", "flooding_complaints"]`).

#### 5. Weather Integrator (`weather_integrator.py`)

Fetches live conditions from OpenWeatherMap every 30 minutes. Extracts temperature, humidity, precipitation, and wind speed. Sets `high_rainfall_flag = True` when precipitation > 10 mm/hr. Falls back to cached or simulated data if the API is unavailable.

#### 6. Traffic Analyzer (`traffic_analyzer.py`)

Generates traffic congestion levels (LOW / MEDIUM / HIGH) for each of the 44 Bengaluru zones. In the current version data is simulated with time-of-day patterns (rush-hour aware). The architecture is designed to be replaced with a real traffic API (e.g., Google Maps Traffic or HERE Traffic) with zero code changes elsewhere.

#### 7. Report Generator (`report_generator.py`)

At 06:00 every day, the generator collects:
- Total complaint count (24 h)
- All high-risk zones and their scores
- All incident predictions
- Current weather summary

It then calls Bedrock Claude with a structured prompt asking for a 2–3 sentence executive summary. The report is stored for 30 days and served via `GET /daily-report`.

---

### Frontend Components

| Component | Role |
|-----------|------|
| `Dashboard.js` | Main container; polls all APIs every 30 seconds |
| `MapVisualizer.js` | Leaflet.js map with colour-coded risk zone circles and complaint pins |
| `ComplaintForm.js` | Floating form for submitting new complaints; location picker + category dropdown |
| `ComplaintFeed.js` | Live-updating list of the latest complaints |
| `TrendCharts.js` | Chart.js line/bar charts: 7-day complaint volumes and risk score trends |
| `WeatherPanel.js` | Current weather conditions (temperature, humidity, precipitation, wind) |
| `TrafficPanel.js` | Traffic congestion grid for all Bengaluru zones |
| `PredictionsPanel.js` | List of active incident predictions with type, time window and risk score |
| `AIInsightsPanel.js` | Natural-language AI analysis from the daily report |
| `LoginPage.js` | Authentication gate for city official dashboard |

---

### Innovation Highlights

- **Graceful AI degradation**: The system never fails due to an AI outage. The circuit-breaker + keyword-fallback pipeline ensures every complaint is classified even without AWS credentials.
- **Real-time risk intelligence**: Risk zones are re-calculated every 15 minutes, incorporating live weather. A sudden monsoon shower can push a medium-risk flooding zone to high risk within one update cycle.
- **Natural language reporting**: City officials receive a plain-English executive summary every morning — no need to interpret raw data.
- **Property-based test suite**: 50+ correctness properties are validated with Hypothesis (Python) and fast-check (JavaScript), covering edge cases like empty complaint lists, boundary risk scores, and extreme weather inputs.
- **Production-ready architecture**: The backend is deployable as an AWS Lambda function (see `lambda_handler.py` and `template.yaml`), with DynamoDB as the production data store.

---

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
