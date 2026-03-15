# UrbanGuard AI — 10-Slide Gamma-Style Presentation Prompt

> **Usage:** Copy each slide block below as a prompt into [Gamma.app](https://gamma.app) to auto-generate a polished presentation slide. Each slide includes a title, subtitle, body content, and visual direction.

---

## Slide 1 — Title Slide

**Title:** UrbanGuard AI
**Subtitle:** AI-Powered Urban Infrastructure Monitoring & Risk Prediction for Bengaluru

**Body:**
> Turning citizen complaints into city intelligence — in real time.

**Visual Direction:** Full-bleed aerial photograph of Bengaluru city at dusk with a translucent dark overlay. Large white sans-serif headline centred. Include a glowing blue network-mesh graphic to suggest AI connectivity. Bottom-left corner: team/hackathon name badge.

---

## Slide 2 — The Problem

**Title:** Bengaluru's Urban Infrastructure Crisis
**Subtitle:** 13 million citizens, thousands of daily complaints — and no system to act on them fast enough.

**Body:**

- 🚧 **Potholes, flooding & road damage** cause injuries and economic losses every monsoon season
- 🚦 **Traffic congestion** worsened by uncoordinated infrastructure failures
- 💡 **Broken streetlights & water supply failures** go unreported or untracked for weeks
- 🗑️ **Garbage accumulation** leads to public health hazards in dense urban wards
- ❌ **No unified platform** exists to collect, classify, and prioritise citizen complaints at scale
- 📉 **BBMP (municipal body) lacks real-time data** to allocate repair crews efficiently

**Visual Direction:** Split-screen infographic — left side shows photos of potholes, flooded streets, garbage; right side shows a map of Bengaluru with red hotspot pins. Use bold red/orange accent colours to convey urgency.

---

## Slide 3 — Our Solution

**Title:** UrbanGuard AI — What We Built
**Subtitle:** A full-stack, AI-driven civic intelligence platform that transforms raw complaints into actionable risk intelligence.

**Body:**

| Capability | How It Works |
|---|---|
| 📲 **Citizen Complaint Portal** | Citizens submit geotagged complaints via web app |
| 🤖 **AI Auto-Classification** | Amazon Bedrock (Claude 3.5 Sonnet) categorises each complaint instantly |
| 🗺️ **Interactive Risk Map** | Leaflet.js map overlays complaint clusters & risk zones in real time |
| ⚠️ **Risk Score Engine** | Composite scoring using complaint density, weather, and traffic data |
| 📊 **Daily AI Reports** | Automated PDF-style reports generated every morning at 06:00 IST |
| 🔔 **Instant Alerts** | SNS notifications pushed to officials when a zone reaches HIGH risk |

**Visual Direction:** Clean product screenshot mock-up of the dashboard with the map front-and-centre. Use a bright teal/blue colour palette. Annotate key UI sections with callout labels.

---

## Slide 4 — Tech Stack

**Title:** Technology Stack
**Subtitle:** Modern, cloud-native technologies chosen for performance, scalability, and developer velocity.

**Body:**

### 🖥️ Frontend
- **React 18** — Component-based SPA with hooks
- **Leaflet.js / react-leaflet** — Interactive geospatial map
- **Chart.js / react-chartjs-2** — Trend and analytics charts
- **Axios** — HTTP client for REST API calls
- **React Router DOM 7** — Client-side navigation

### ⚙️ Backend
- **Python 3.12 + FastAPI** — Async REST API & WebSocket server
- **Pydantic 2** — Data validation and serialisation
- **Uvicorn** — ASGI production server
- **Mangum** — AWS Lambda ASGI adapter

### 🔬 AI / Data Science
- **Amazon Bedrock** (Claude 3.5 Sonnet / Amazon Nova) — NLP complaint classification
- **K-Means Clustering** — Geographic hotspot detection (Python)
- **OpenWeatherMap API** — Live weather data integration

### 🧪 Testing
- **pytest + Hypothesis** — Property-based backend testing (60+ tests)
- **Jest + React Testing Library + fast-check** — Frontend testing (40+ tests)

**Visual Direction:** Two-column icon grid. Left column = frontend icons (React logo, map pin, chart). Right column = backend icons (Python snake, AWS Lambda, Bedrock brain). Use a dark navy background with coloured logo icons.

---

## Slide 5 — AWS Services Architecture

**Title:** AWS Cloud Architecture
**Subtitle:** Fully serverless, event-driven, and production-ready on AWS.

**Body:**

```
Citizens / Browser
      │
      ▼
┌─────────────────────┐
│  Amazon API Gateway  │  ← REST endpoints + CORS
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐      ┌──────────────────┐
│   AWS Lambda         │─────▶│  Amazon Bedrock   │ AI Classification
│  (Python 3.12 / SAM) │      │  Claude 3.5 Sonnet│
└─────────┬───────────┘      └──────────────────┘
          │
    ┌─────┼──────────────────────────┐
    ▼     ▼                          ▼
┌───────┐ ┌──────────┐  ┌──────────────────────┐
│  SQS  │ │ DynamoDB │  │  Amazon S3            │
│ Queue │ │ 4 Tables │  │  Reports + BBMP Data  │
└───┬───┘ └──────────┘  └──────────────────────┘
    │
    ▼
┌──────────┐   ┌────────────────┐   ┌──────────────────┐
│  SNS     │   │  EventBridge   │   │  CloudWatch       │
│  Alerts  │   │  Daily Cron    │   │  Logs & Alarms    │
└──────────┘   └────────────────┘   └──────────────────┘
    │
    ▼
┌─────────────┐
│  Cognito    │  User Auth + JWT
└─────────────┘
```

**AWS Services Summary:**

| Service | Role |
|---|---|
| **Lambda** | Serverless compute — all API handlers |
| **API Gateway** | Public REST API with CORS |
| **DynamoDB** | NoSQL storage — Complaints, RiskZones, Users, Reports |
| **Bedrock** | Generative AI — NLP classification & report summaries |
| **S3** | Object storage — daily reports, BBMP datasets |
| **SQS + DLQ** | Async complaint ingestion queue with retry |
| **SNS** | Push alerts to city officials on HIGH-risk zones |
| **EventBridge** | Scheduled daily report trigger at 06:00 IST |
| **CloudWatch** | Centralised logs, alarms, metrics |
| **Cognito** | User pool with email verification & JWT |
| **IAM** | Fine-grained access policies for all resources |

**Visual Direction:** AWS architecture diagram using official AWS service icons on a white canvas. Use blue arrows to show data flow. Group related services in dashed-border swim-lane boxes labelled "Compute", "Storage", "AI/ML", "Messaging", "Security".

---

## Slide 6 — Backend Deep Dive

**Title:** Backend Architecture
**Subtitle:** A modular, async Python microservice designed for resilience and extensibility.

**Body:**

### Core Modules

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app, 15+ REST endpoints, WebSocket manager |
| `ai_classifier.py` | Bedrock AI with circuit-breaker & keyword fallback |
| `risk_engine.py` | Composite risk scoring (density + weather + traffic) |
| `cluster_detector.py` | K-Means geographic clustering, density heatmap |
| `weather_integrator.py` | OpenWeatherMap polling every 30 min |
| `traffic_analyzer.py` | Simulated congestion scores per location |
| `incident_predictor.py` | 6h & 24h predictive risk windows |
| `report_generator.py` | Automated daily civic reports via Bedrock |
| `dynamodb_storage.py` | Production DynamoDB CRUD layer |
| `sqs_handler.py` | Async complaint ingestion from SQS |
| `sns_notifier.py` | High-risk zone alert dispatcher |
| `auth_middleware.py` | JWT authentication & admin role checks |

### Key Design Patterns
- ✅ **Circuit Breaker** — AI classifier falls back to keyword matching if Bedrock is unavailable
- ✅ **Rate Limiting** — 5 requests/minute on `/report-complaint`
- ✅ **Background Schedulers** — 4 async tasks running concurrently
- ✅ **Storage Abstraction** — Swappable in-memory ↔ DynamoDB via interface
- ✅ **SAM Serverless Deployment** — One command deploys entire stack

**Visual Direction:** Modular box diagram with each Python module as a coloured rectangle, connected by thin arrows showing data flow. Use a cool grey background. Highlight the AI classifier with a gold glow border.

---

## Slide 7 — Frontend Deep Dive

**Title:** Frontend Architecture
**Subtitle:** A real-time, responsive React dashboard for citizens and city officials.

**Body:**

### Component Hierarchy

```
App.js (Router + Auth Guard)
├── LoginPage.js          — Email/password auth, JWT storage
└── Dashboard.js          — Main layout grid (902 lines)
    ├── MapVisualizer.js  — Leaflet map, markers, risk-zone circles
    ├── ComplaintFeed.js  — Sortable/filterable complaint list
    ├── ComplaintForm.js  — Geotagged submission form (rate-limited)
    ├── TrendCharts.js    — 7-day line + bar charts (Chart.js)
    ├── WeatherPanel.js   — Live weather (temp, humidity, rain, wind)
    ├── TrafficPanel.js   — Congestion scores per location
    ├── PredictionsPanel.js — 6h/24h incident prediction cards
    ├── AIInsightsPanel.js  — AI-generated daily summary
    └── LocationPicker.js   — Geocoding-enabled location selector
```

### Real-Time Features
- 🔄 **30-second polling** for fresh complaint & risk data
- 🔌 **WebSocket connection** for live marker updates
- 🗺️ **Interactive map** — click markers for complaint details
- 📅 **Time range filters** — 6h / 24h / 7d / 30d / all

### Filters Available to Users
- **Category**: Pothole, Flooding, Traffic, Garbage, Streetlight, Water Supply, Noise, Construction
- **Risk Level**: Low / Medium / High
- **Time Range**: Last 6h → All time

**Visual Direction:** Annotated React component tree diagram. Show Dashboard in the centre with branches to each panel component. Use coloured badges next to each component name indicating "Map", "Chart", "Form", "Panel" type. Screenshot thumbnail of the actual UI sits to the right.

---

## Slide 8 — AI & Data Intelligence

**Title:** AI & Intelligence Layer
**Subtitle:** From raw text to predictive risk scores — powered by Amazon Bedrock and data fusion.

**Body:**

### How a Complaint Becomes a Risk Alert

```
1. Citizen submits complaint text
        │
        ▼
2. Amazon Bedrock (Claude 3.5 Sonnet)
   classifies category + confidence score
   [fallback: keyword-based classifier]
        │
        ▼
3. Complaint stored with geocoordinates
        │
        ▼
4. K-Means Cluster Detector
   groups nearby complaints (500m radius)
        │
        ▼
5. Risk Engine combines:
   • Complaint density score
   • Weather modifier (heavy rain → +risk)
   • Traffic congestion score
   → outputs Risk Score (0–100) + Level
        │
        ▼
6. Incident Predictor
   generates 6h / 24h predictions
        │
        ▼
7. If HIGH risk →
   SNS alert to officials
   + Daily Report via Bedrock summarisation
```

### Bedrock Models Supported
- Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
- Amazon Nova Micro (`amazon.nova-micro-v1:0`)
- Amazon Nova Pro (`amazon.nova-pro-v1:0`)

### Data Sources
| Source | Data |
|---|---|
| OpenWeatherMap API | Temperature, humidity, rainfall, wind |
| BBMP Dataset (S3) | Historical ward-level infrastructure data |
| Citizen submissions | Real-time geotagged complaint text |
| Simulated traffic | Congestion scores for 40+ Bengaluru locations |

**Visual Direction:** Vertical flowchart with numbered pipeline steps. Use a dark purple/indigo gradient background. Each step in a rounded rectangle with an icon. Highlight the Bedrock step with an AWS orange glow. Show confidence score badge (e.g. "92% confidence: Pothole").

---

## Slide 9 — Key Features & Impact

**Title:** Features & Impact
**Subtitle:** Built to scale from hackathon prototype to a production system serving millions.

**Body:**

### For Citizens 👤
- ✅ Simple web form to report any infrastructure issue
- ✅ Real-time feedback — complaint confirmed and classified in seconds
- ✅ View all open issues on an interactive city map

### For City Officials 🏛️
- ✅ Live risk map showing hotspots by category & severity
- ✅ AI-generated morning briefing every day at 06:00 IST
- ✅ Automated SNS alerts when a zone crosses HIGH-risk threshold
- ✅ Admin panel to resolve complaints and track status

### By the Numbers (Demo Data)
| Metric | Value |
|---|---|
| Locations Covered | 40+ Bengaluru areas |
| Complaint Categories | 8 types |
| API Endpoints | 15+ |
| AI Classification | < 2 sec response (Bedrock) |
| Test Pass Rate | 99.3% (148/149 tests passing) |
| AWS Resources | 11 managed services |
| Backend Tests | 60+ (unit + property-based) |
| Frontend Tests | 40+ (unit + property-based) |

### What Makes It Different
- **AI-first**: Every complaint is AI-classified, not manually sorted
- **Predictive**: Flags risk *before* an incident occurs — not after
- **Serverless**: Near-zero cost at low traffic, auto-scales on demand
- **Open Data**: Integrates BBMP ward-level historical data for context

**Visual Direction:** Two-column layout. Left column: three icon cards (Citizen / Official / System). Right column: a clean metrics table with large bold numbers. Use a light background with teal accent lines. Bottom banner: "From complaint to resolution — powered by AI."

---

## Slide 10 — Architecture Summary & Roadmap

**Title:** System Architecture & Future Roadmap
**Subtitle:** A production-ready foundation with a clear path to city-wide deployment.

**Body:**

### System Architecture at a Glance

```
┌──────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                     │
│   React 18 SPA → Dashboard / Map / Charts / Forms        │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTPS / WSS
┌──────────────────────▼───────────────────────────────────┐
│                    API LAYER (AWS)                        │
│   API Gateway → Lambda (FastAPI + Mangum)                │
└─────┬──────────────┬─────────────────┬────────────────────┘
      │              │                 │
┌─────▼──┐  ┌────────▼───┐  ┌─────────▼────────┐
│AI Layer│  │  Data Layer│  │  Messaging Layer  │
│Bedrock │  │  DynamoDB  │  │  SQS / SNS        │
│Claude  │  │  S3        │  │  EventBridge      │
└────────┘  └────────────┘  └──────────────────┘
      │              │                 │
┌─────▼──────────────▼─────────────────▼────────┐
│              OBSERVABILITY LAYER               │
│        CloudWatch Logs + Alarms + Metrics      │
└────────────────────────────────────────────────┘
      │
┌─────▼─────────────┐
│   SECURITY LAYER  │
│  Cognito + JWT    │
│  IAM Policies     │
└───────────────────┘
```

### Future Roadmap 🚀

| Phase | Enhancement |
|---|---|
| **Phase 2** | Mobile app (React Native) for on-ground BBMP crew reporting |
| **Phase 2** | Integrate live CCTV feeds with Amazon Rekognition for auto-detection |
| **Phase 3** | WhatsApp / IVR complaint intake via Amazon Connect |
| **Phase 3** | ML-based SLA prediction — "how long will this take to fix?" |
| **Phase 4** | Multi-city expansion (Chennai, Hyderabad, Mumbai) |
| **Phase 4** | Public transparency dashboard with complaint resolution rates |

### Deployment
- **IaC**: AWS SAM (`sam build && sam deploy`)
- **CI/CD**: GitHub Actions → SAM pipeline
- **Env Config**: `.env` variables for API keys, AWS region, table names
- **Cost Model**: Pay-per-request DynamoDB + serverless Lambda = near-zero idle cost

**Visual Direction:** Full-page layered architecture diagram with clear swim-lanes (Presentation / API / AI+Data / Messaging / Security). Use AWS orange & dark navy colour theme. Roadmap rendered as a horizontal timeline at the bottom with phase markers. Final tag line: "UrbanGuard AI — Smarter Cities, Safer Lives."

---

*Generated from repository analysis of [AakashG-1808/Nimbus1000-Hack](https://github.com/AakashG-1808/Nimbus1000-Hack)*
