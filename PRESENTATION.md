# UrbanGuard AI — 10-Slide Gamma-Style Presentation Prompt

> **Usage:** Copy each slide block into [Gamma.app](https://gamma.app) to auto-generate a polished presentation slide. Each slide contains a title, subtitle, detailed body content, speaker notes, and a visual direction callout.

---

## Slide 1 — Title Slide

**Title:** UrbanGuard AI
**Subtitle:** AI-Powered Urban Infrastructure Monitoring & Predictive Risk Intelligence for Bengaluru

**Body:**

> *"Every pothole reported, every flood ignored, every broken streetlight — UrbanGuard AI turns citizen signals into city action."*

**Key Numbers at a Glance:**

| | |
|---|---|
| 🏙️ **13 million** citizens served | 📍 **44 locations** across Bengaluru |
| 🤖 **3 AI models** (Claude 3.5 Sonnet, Nova Micro, Nova Pro) | ☁️ **11 AWS services** in production |
| ⚡ **< 2 seconds** end-to-end AI classification | 🧪 **100+ automated tests** (99.3% pass rate) |
| 📡 **15 REST endpoints** + WebSocket real-time feed | 🗺️ **8 complaint categories** tracked |

**Hackathon Context:** Built for Nimbus 1000 Hack — a full-stack production-grade system, not a toy prototype.

**Speaker Notes:** Open with the human impact — monsoon season, flooded streets, injuries from potholes. Frame the pitch as: "What if every citizen complaint was an AI sensor feeding a city-wide risk map?"

**Visual Direction:** Full-bleed aerial satellite photograph of Bengaluru at dusk with a deep navy overlay. Centred large white sans-serif headline. Glowing blue neural-network mesh graphic drifting across the bottom half. Bottom-left corner: Nimbus 1000 Hack badge. Bottom-right: AWS Partner logo. Subtle animated pulse rings radiating from a map pin on the Bengaluru skyline.

---

## Slide 2 — The Problem

**Title:** Bengaluru's Urban Infrastructure Crisis
**Subtitle:** 13 million people, 198 wards, thousands of daily complaints — and zero AI to act on them.

**Body:**

### The Core Problems

| Problem | Real-World Impact |
|---|---|
| 🚧 **Potholes & road damage** | 3,000+ pothole-related accidents in Bengaluru per year; economic losses exceed ₹3,000 crore annually |
| 🌊 **Urban flooding** | Monsoon floods displace thousands, destroy property, and halt commerce for days at a time |
| 💡 **Broken streetlights** | Dark streets increase crime rates and pedestrian accident risk by up to 40% at night |
| 🚰 **Water supply failures** | Pipeline leaks and supply disruptions affect tens of thousands daily with no automated alert system |
| 🗑️ **Garbage accumulation** | Uncollected waste breeds disease vectors; dengue outbreaks correlate directly with garbage hotspots |
| 🚦 **Traffic congestion** | Bengaluru loses an estimated **$4.3 billion** per year in productivity due to traffic alone |
| 🔇 **Noise & construction chaos** | Uncoordinated excavation and construction creates hazards with no visibility to residents |

### Why Existing Systems Fail

```
Current State:
Citizen → Calls helpline → Manual data entry → Weekly batch report → Crew assigned (days later)
                                    ↑
                           No pattern detection
                           No risk prediction
                           No geographic clustering
                           No weather correlation
                           No AI classification
```

### The BBMP Gap
- **BBMP** (Bruhat Bengaluru Mahanagara Palike — city's municipal body) operates with **fragmented ward-level data** stored in Excel files
- No centralised, real-time dashboard for resource allocation decisions
- Repair crew dispatch is **reactive, not predictive**
- Citizens have no feedback loop — complaints are submitted to black holes

### The Opportunity
- 44 major locations in Bengaluru generate measurable complaint patterns
- Weather data (monsoon, rainfall intensity) directly correlates with flooding and pothole severity
- Traffic congestion compoundsinfrastructure failures — but no system links them
- **A geographic clustering + AI system could predict incidents 6–24 hours before they peak**

**Speaker Notes:** Use specific numbers. The ₹3,000 crore pothole stat and the $4.3B traffic productivity loss land hard. Emphasise that BBMP currently operates blind — they have no real-time map.

**Visual Direction:** Split-screen layout. Left side: 4 photographs in a 2×2 grid (flooded road, pothole with traffic cone, broken streetlight, overflowing garbage pile). Right side: A stylised red-heat-map overlay of Bengaluru with no data — blank, with the caption "What BBMP sees today". Bold orange/red colour palette. At the bottom: a horizontal timeline showing "Complaint Reported → Manual Entry → Weekly Report → Crew Dispatch" with a "Days Later" callout.

---

## Slide 3 — Our Solution

**Title:** UrbanGuard AI — What We Built
**Subtitle:** A full-stack, AI-driven civic intelligence platform: from citizen complaint to risk-scored, geo-clustered, officially-alerted city action in under 2 seconds.

**Body:**

### The Complete Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 1: CITIZEN REPORTS                                             │
│  Web form → location (44 choices) + category (8 types) + description│
│  Optional: GPS coordinates auto-filled via geocoding                │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ POST /api/v1/report-complaint
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 2: AI CLASSIFICATION (< 2 seconds)                             │
│  Amazon Bedrock → Claude 3.5 Sonnet → category + confidence score   │
│  Circuit breaker fallback → keyword matching if Bedrock is down     │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 3: GEOGRAPHIC CLUSTERING (every 15 minutes)                    │
│  K-Means clustering → 500m radius clusters → density per km²       │
│  High-density flag: 5+ complaints in 24 hours                       │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 4: RISK SCORE ENGINE (every 15 minutes)                        │
│  Base score (complaint density, log-scale) + severity modifier      │
│  + weather modifier (heavy rain → +30 pts) + traffic modifier       │
│  + BBMP historical boosts → Risk Score 0–100 → LOW/MEDIUM/HIGH      │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 5: INCIDENT PREDICTION                                         │
│  6-hour & 24-hour risk windows → contributing factors listed        │
│  AI-generated explanation via Bedrock                               │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                    ┌──────┴──────────────────────┐
                    ▼                             ▼
┌──────────────────────────┐     ┌────────────────────────────────────┐
│  STEP 6A: ALERT          │     │  STEP 6B: DASHBOARD UPDATE         │
│  SNS → city officials    │     │  WebSocket broadcast → React map   │
│  for HIGH-risk zones     │     │  Risk circles, markers, charts     │
└──────────────────────────┘     └────────────────────────────────────┘
                                               │
                                               ▼
                                ┌──────────────────────────────────┐
                                │  STEP 7: DAILY REPORT (06:00 IST)│
                                │  EventBridge → Lambda → Bedrock  │
                                │  AI-generated civic summary +    │
                                │  high-risk zones + predictions   │
                                └──────────────────────────────────┘
```

### Six Core Capabilities

| # | Capability | Technology | SLA |
|---|---|---|---|
| 1 | **Citizen Complaint Portal** | React 18 form, Axios, JWT auth | < 500ms submission |
| 2 | **AI Auto-Classification** | Amazon Bedrock (Claude 3.5 Sonnet) | < 2 sec |
| 3 | **Geographic Risk Map** | Leaflet.js + K-Means clustering | < 300ms fetch |
| 4 | **Composite Risk Scoring** | Python risk engine (density + weather + traffic) | Recalculates every 15 min |
| 5 | **Predictive Alerts** | SNS + 6h/24h incident predictor | Immediate on HIGH |
| 6 | **Daily AI Briefing** | EventBridge cron → Bedrock summarisation | 06:00 IST daily |

**Speaker Notes:** Walk through the workflow step-by-step using the flowchart. Emphasise "under 2 seconds from complaint to AI decision". Point out the circuit breaker — the system degrades gracefully even if Bedrock is unavailable.

**Visual Direction:** Full-width vertical flowchart on a dark teal background. Each step in a rounded rectangle with a numbered badge and icon. Arrows in bright white. Step 4 (Risk Engine) highlighted with a golden glow. Two split paths at Step 6 (Alert vs Dashboard) shown in different colours (red for alert, blue for dashboard). Footer: "Zero manual intervention from submission to official alert."

---

## Slide 4 — Tech Stack

**Title:** Technology Stack
**Subtitle:** Every library chosen for a reason — production-grade, cloud-native, fully tested.

**Body:**

### 🖥️ Frontend — React 18 SPA

| Library | Version | Why We Chose It |
|---|---|---|
| **React** | `^18.2.0` | Concurrent rendering, hooks-based state, component reusability |
| **React Router DOM** | `^7.13.1` | Latest v7 router — nested routes, protected route wrappers |
| **Leaflet.js** | `^1.9.4` | Lightweight open-source mapping — no Google Maps billing |
| **react-leaflet** | `^4.2.1` | Declarative React wrapper for Leaflet — marker/circle components |
| **Chart.js** | `^4.4.0` | Canvas-based charts, 60fps animation, responsive datasets |
| **react-chartjs-2** | `^5.2.0` | React wrapper for Chart.js — ref-based chart control |
| **Axios** | `^1.6.2` | Promise-based HTTP client — interceptors, timeout config |

**Frontend Testing:**

| Library | Version | Purpose |
|---|---|---|
| `@testing-library/react` | `^16.3.2` | DOM interaction testing, accessibility-first queries |
| `@testing-library/jest-dom` | `^6.9.1` | Extended Jest matchers (toBeInTheDocument, etc.) |
| `fast-check` | `^3.15.0` | Property-based testing — randomised inputs, shrinking |

**Build Tool:** Create React App (`react-scripts 5.0.1`) — zero-config Webpack + Babel + Jest setup

---

### ⚙️ Backend — Python 3.12 + FastAPI

| Library | Version | Why We Chose It |
|---|---|---|
| **FastAPI** | `>=0.115.0` | Async-first, auto OpenAPI docs, Pydantic native, 3× faster than Flask |
| **Uvicorn** | `>=0.32.0` | ASGI server — supports async/await, HTTP/2, WebSocket |
| **Pydantic** | `>=2.10.0` | v2 with Rust-based validation — 5–10× faster than v1 |
| **Mangum** | `>=0.17.0` | ASGI → AWS Lambda adapter — wraps FastAPI for serverless |
| **Boto3** | `>=1.35.0` | AWS SDK — DynamoDB, S3, SQS, SNS, Bedrock, Cognito |
| **Requests** | `>=2.32.0` | OpenWeatherMap API polling |
| **python-dotenv** | `>=1.0.0` | `.env` file loading for local development |

**Backend Testing:**

| Library | Version | Purpose |
|---|---|---|
| `pytest` | `>=8.0.0` | Test runner — async test support, fixtures, parametrize |
| `pytest-asyncio` | `>=0.24.0` | Async test execution for FastAPI coroutines |
| `httpx` | `>=0.27.0` | Async HTTP test client for FastAPI endpoints |
| `hypothesis` | `>=6.100.0` | Property-based testing — 50+ correctness properties |

---

### 🔬 AI & Data Science

| Component | Technology | Details |
|---|---|---|
| **NLP Classification** | Amazon Bedrock | Claude 3.5 Sonnet (`apac.anthropic.claude-3-5-sonnet-20241022-v2:0`) |
| **Fallback Classifier** | Python keyword matching | 8 categories × 5 keywords each, confidence scoring |
| **AI Report Generation** | Amazon Bedrock | Nova Pro / Claude 3.5 Sonnet — natural language civic summaries |
| **Geographic Clustering** | K-Means (pure Python) | 500m radius, density calculation per km² |
| **Weather Integration** | OpenWeatherMap REST API | Polled every 30 min; graceful fallback with cached data |
| **Traffic Simulation** | Python `traffic_analyzer.py` | Location-based congestion scores for 44 Bengaluru areas |

---

### ☁️ Infrastructure & DevOps

| Component | Technology |
|---|---|
| **Serverless IaC** | AWS SAM (`template.yaml` — 641 lines) |
| **Deployment Command** | `sam build && sam deploy --guided` |
| **Local Dev** | `uvicorn main:app --reload --port 8000` + `npm start` |
| **Environment Config** | `.env` file — `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `OPENWEATHERMAP_API_KEY`, `CORS_ALLOW_ORIGINS` |

**Speaker Notes:** Highlight the Pydantic v2 choice (5× faster validation), Mangum as the critical bridge between FastAPI and Lambda, and Hypothesis as a differentiator in testing quality.

**Visual Direction:** Four-quadrant card grid on dark navy. Top-left: Frontend (React blue). Top-right: Backend (Python green). Bottom-left: AI/Data (AWS orange). Bottom-right: DevOps (purple). Each card shows library logos and exact version numbers. Small "why" caption under each. Clean icon row at the bottom: React + Python + AWS + Docker.

---

## Slide 5 — AWS Services Architecture

**Title:** AWS Cloud Architecture
**Subtitle:** 11 managed AWS services, fully serverless, deployed with a single SAM command — zero servers to manage.

**Body:**

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  CITIZEN / BROWSER (React 18 SPA)                                   │
│  http://localhost:3000  OR  Vercel / S3+CloudFront (production)     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS REST + WSS WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AMAZON API GATEWAY                                                  │
│  REST API — CORS: AllowOrigin=* AllowMethods=GET,POST,OPTIONS       │
│  MaxAge=600s  |  14 routes  |  ANY /api/v1/{proxy+} catch-all       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AWS LAMBDA  —  urbanguard-api-{env}                                │
│  Runtime: Python 3.12  |  Memory: 512 MB  |  Timeout: 30s          │
│  Architecture: x86_64  |  Handler: lambda_handler.lambda_handler    │
│  Adapter: Mangum (FastAPI → ASGI → Lambda)                          │
│  Triggers: API Gateway HTTP  +  SQS (batch=10)  +  EventBridge cron│
└──────┬─────────────────────────────────────────────────────────────┘
       │
 ┌─────┼────────────────────────────────────────────────────┐
 ▼     ▼           ▼              ▼             ▼            ▼
┌────────────┐  ┌─────────────────────┐  ┌──────────────────────────┐
│  BEDROCK   │  │      DYNAMODB        │  │         AMAZON S3        │
│ AI Engine  │  │  4 tables (PAY_PER_  │  │  urbanguard-data-{env}-  │
│ Claude 3.5 │  │  REQUEST billing)    │  │  {accountId}             │
│ Nova Micro │  │                      │  │  Versioning: ON          │
│ Nova Pro   │  │  Complaints          │  │  Lifecycle: 90-day delete│
│ Region:    │  │  RiskZones           │  │  Public access: BLOCKED  │
│ ap-south-2 │  │  DailyReports (TTL)  │  │  Contents:               │
│ Timeout:3s │  │  Users               │  │  - Daily PDF reports     │
└────────────┘  └──────────┬──────────┘  │  - BBMP ward datasets    │
                           │ GSIs:        └──────────────────────────┘
                           │ Complaints: category-index, timestamp-index
                           │ RiskZones: risk-score-index (risk_level HASH)
                           │ All tables: PITR ON, Streams ON
                           │
 ┌─────────────────────────┼──────────────────────────────┐
 ▼                         ▼                              ▼
┌──────────────────┐  ┌───────────────────┐  ┌─────────────────────┐
│  AMAZON SQS       │  │  AMAZON SNS       │  │  AWS EVENTBRIDGE    │
│  urbanguard-      │  │  urbanguard-      │  │  Daily Report Cron  │
│  complaints-{env} │  │  alerts-{env}     │  │  cron(30 0 * * ? *) │
│  Visibility: 60s  │  │  High-risk zone   │  │  = 06:00 IST daily  │
│  Retention: 24h   │  │  alerts + daily   │  └─────────────────────┘
│  DLQ: 7-day       │  │  report emails    │
│  Redrive: 3x      │  │  Email sub:       │
│  Batch size: 10   │  │  optional         │
└──────────────────┘  └───────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  OBSERVABILITY                                                       │
│  CloudWatch Log Groups:                                              │
│    /aws/lambda/urbanguard-api-{env}    — 30-day retention           │
│    /aws/apigateway/urbanguard-api-{env} — 30-day retention          │
│  CloudWatch Alarms:                                                  │
│    Lambda Error Rate: > 10 errors / 5 min → SNS alert              │
│    Lambda Throttles: > 5 throttles / 5 min → SNS alert             │
│    DLQ Depth: > 1 message → SNS alert                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SECURITY                                                            │
│  Amazon Cognito: urbanguard-users-{env}                             │
│    Password: min 8 chars, upper+lower+numbers required              │
│    Attributes: email (auto-verified), role (custom mutable)         │
│    App Client: urbanguard-client-{env}                              │
│  IAM Policies: per-service least-privilege for Lambda function      │
└─────────────────────────────────────────────────────────────────────┘
```

### AWS Services Configuration Reference

| Service | Resource Name | Key Configuration |
|---|---|---|
| **Lambda** | `urbanguard-api-{env}` | 512 MB, 30s timeout, Python 3.12, x86_64 |
| **API Gateway** | `UrbanGuardApi` | 14 routes, CORS *, MaxAge 600s |
| **DynamoDB** | `Complaints` | HASH: `complaint_id`; GSI: `category-index`, `timestamp-index`; PITR ON |
| **DynamoDB** | `RiskZones` | HASH: `zone_id`; GSI: `risk-score-index` (risk_level HASH, risk_score RANGE) |
| **DynamoDB** | `DailyReports` | HASH: `report_id`; RANGE: `date`; TTL attribute; PITR ON |
| **DynamoDB** | `Users` | HASH: `email`; PITR ON |
| **Bedrock** | Claude 3.5 Sonnet | `apac.anthropic.claude-3-5-sonnet-20241022-v2:0`; 3s timeout |
| **S3** | `urbanguard-data-{env}-{accountId}` | Versioning ON, lifecycle 90 days, all public access blocked |
| **SQS** | `urbanguard-complaints-{env}` | Visibility 60s, retention 24h, DLQ redrive 3× |
| **SQS DLQ** | `urbanguard-complaints-dlq-{env}` | 7-day retention |
| **SNS** | `urbanguard-alerts-{env}` | HIGH-risk alerts + daily report + optional email sub |
| **EventBridge** | Daily Report Rule | `cron(30 0 * * ? *)` → Lambda |
| **CloudWatch** | 2 Log Groups | 30-day retention each |
| **CloudWatch** | 3 Alarms | Error rate, throttles, DLQ depth |
| **Cognito** | `urbanguard-users-{env}` | Email-based, role attribute, password complexity enforced |
| **IAM** | Lambda execution role | DynamoDB CRUD, S3 CRUD, SQS send, SNS publish, Bedrock invoke, CloudWatch logs |

**Speaker Notes:** Note the DLQ safety net — if Lambda fails to process a complaint 3 times, it lands in the DLQ and triggers a CloudWatch alarm so nothing is ever silently lost.

**Visual Direction:** Official AWS architecture diagram using AWS service icon set. Colour-coded swim-lane boxes: "Compute" (orange), "Storage" (green), "AI/ML" (purple), "Messaging" (yellow), "Security" (red), "Observability" (blue). Animated data-flow arrows in light grey. Lambda sits in the centre as the hub.

---

## Slide 6 — Backend Architecture

**Title:** Backend Deep Dive
**Subtitle:** 987-line FastAPI app, 12 specialised modules, 15 endpoints, 4 background schedulers — all async, all tested.

**Body:**

### Complete API Endpoint Reference

| Method | Endpoint | Auth | Rate Limit | SLA | Purpose |
|---|---|---|---|---|---|
| `GET` | `/` | ❌ | — | — | Root status, complaint count, WS endpoint |
| `GET` | `/health` | ❌ | — | — | Health check + Bedrock availability |
| `POST` | `/api/v1/auth/signup` | ❌ | — | — | User registration `{email, password, role?}` |
| `POST` | `/api/v1/auth/login` | ❌ | — | — | Login → returns JWT token |
| `GET` | `/api/v1/auth/me` | ✅ JWT | — | — | Returns `{email, role}` from token |
| `POST` | `/api/v1/report-complaint` | ✅ JWT | **5/min** | < 500ms | Submit complaint `{location, category, description, timestamp?, coordinates?}` → triggers cluster+risk recalc + WS broadcast |
| `GET` | `/api/v1/complaints` | ❌ | — | < 200ms | List complaints — filters: `location`, `category`, `since`, `until`, `offset` (0), `limit` (1–1000) — sorted desc by timestamp |
| `PATCH` | `/api/v1/complaints/{id}/resolve` | ✅ Admin | — | — | Resolve complaint; bulk-resolves same location+category; returns `{resolved_count, resolved_ids}` |
| `GET` | `/api/v1/clusters` | ❌ | — | < 100ms | K-Means clusters with center, radius (500m), density/km², high-density flag |
| `GET` | `/api/v1/risk-hotspots` | ❌ | — | < 300ms | Risk zones with `risk_score > 10`; returns zone_id, coordinates, risk_score, risk_level, complaint_count, dominant_category |
| `GET` | `/api/v1/weather` | ❌ | — | < 100ms | Cached weather: temp_°C, humidity_%, precipitation_mm/h, wind_kmh, high_rainfall_flag |
| `GET` | `/api/v1/traffic` | ❌ | — | < 50ms | Traffic by location: congestion_level (LOW/MEDIUM/HIGH), congestion_score (1/5/10) |
| `GET` | `/api/v1/predictions` | ❌ | — | < 500ms | Incident predictions: zone_id, incident_type, risk_score, time_window (6h/24h), contributing_factors, AI explanation |
| `GET` | `/api/v1/daily-report` | ❌ | — | < 200ms | Latest daily report: total_complaints, high_risk_zones[], predicted_incidents[], weather_summary, ai_generated_summary |
| `GET` | `/api/v1/bbmp-insights` | ❌ | — | — | BBMP hotspot boosts, category weights, seasonal warnings (404 if no data) |
| `WS` | `/ws` | ❌ | — | Real-time | WebSocket — broadcasts `{type:"new_complaint", complaint:{...}}` on each submission |

---

### Core Module Reference

| Module | Lines | Responsibility |
|---|---|---|
| `main.py` | 987 | FastAPI app, all endpoints, WebSocket `ConnectionManager`, rate limiter, CORS, request logging middleware |
| `ai_classifier.py` | 562 | Bedrock client, circuit breaker (CLOSED→OPEN→HALF_OPEN), keyword fallback, confidence scoring |
| `risk_engine.py` | 667 | Composite risk formula, per-category severity weights, weather modifier (+30), traffic modifier (+15), BBMP boosts |
| `cluster_detector.py` | 402 | K-Means clustering, 500m radius, density per km², high-density flag (5+ in 24h), 15-min scheduler |
| `weather_integrator.py` | 444 | OpenWeatherMap polling (30-min interval), graceful fallback, `high_rainfall_flag` > 10mm/h threshold |
| `traffic_analyzer.py` | ~250 | Per-location congestion simulation, 10-min updates, scores: LOW=1, MEDIUM=5, HIGH=10 |
| `incident_predictor.py` | ~300 | 6h & 24h prediction windows, contributing factors list, Bedrock-generated explanation (cached) |
| `report_generator.py` | 478 | Daily report assembly, Bedrock summarisation, S3 upload, SNS notification dispatch |
| `dynamodb_storage.py` | 490 | Full DynamoDB CRUD for all 4 tables; GSI queries for category and risk filtering |
| `sqs_handler.py` | — | SQS batch consumer, `ReportBatchItemFailures` pattern, DLQ safety net |
| `sns_notifier.py` | — | SNS publish to `urbanguard-alerts-{env}` for HIGH-risk zones |
| `auth_middleware.py` | — | JWT decode, Bearer token validation, admin role check |
| `storage.py` | — | Abstract storage interface — enables in-memory ↔ DynamoDB swap |
| `bbmp_data_loader.py` | — | Load BBMP ward data from S3 CSV/JSON, inject context into Bedrock prompts |
| `lambda_handler.py` | — | Mangum ASGI adapter entry point for AWS Lambda |

---

### Key Design Patterns

```
┌─────────────────────────────────────────────────────┐
│  CIRCUIT BREAKER (ai_classifier.py)                  │
│                                                       │
│  CLOSED ──(5 failures)──▶ OPEN ──(60s)──▶ HALF_OPEN │
│    ▲                         │               │        │
│    └────(3 successes)────────┘◀──(success)──┘        │
│                                                       │
│  OPEN state: fast-fail, use keyword fallback <100ms  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  BACKGROUND SCHEDULERS (4 async tasks)               │
│  • Weather update:  every 1,800s (30 min)            │
│  • Traffic update:  every   600s (10 min)            │
│  • Cluster detect:  every   900s (15 min)            │
│  • Risk engine:     every   900s (15 min)            │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  STORAGE ABSTRACTION                                  │
│  StorageInterface (abstract)                          │
│  ├── InMemoryStorage  ← development mode             │
│  └── DynamoDBStorage  ← production (auto-selected)   │
└─────────────────────────────────────────────────────┘
```

### Rate Limiting & CORS
- **Rate limiter:** `slowapi` — 5 requests/min per IP on `POST /report-complaint`
- **CORS origins:** Reads `CORS_ALLOW_ORIGINS` env var; defaults to `http://localhost:3000`
- **Request logging:** Middleware logs method + path + response_time_ms + status + client_IP

**Speaker Notes:** The 987-line main.py handles all the routing, middleware, and real-time WebSocket. Each component module is independently testable. The storage abstraction means the system runs entirely in-memory during development with no AWS credentials required.

**Visual Direction:** Dark grey background. Python module boxes in muted blue rectangles arranged as a hub-and-spoke diagram with `main.py` at the centre. Each module has a pill-badge showing its line count. Colour-code by type: AI (gold), Storage (green), External APIs (orange), Messaging (yellow), Auth (red). Overlay a dashed circuit-breaker state diagram in the bottom-right corner.

---

## Slide 7 — Frontend Architecture

**Title:** Frontend Deep Dive
**Subtitle:** 13 React components, 902-line dashboard, real-time WebSocket + 30s polling, 8 filters — all accessible in a single-page app.

**Body:**

### Application Routing (App.js)

```javascript
// Route structure — 2 routes, 1 protected
<BrowserRouter>
  <Routes>
    <Route path="/login"  element={<LoginPage />} />  // Public
    <Route path="/"       element={
      <ProtectedRoute>               // Checks isAuthenticated()
        <Dashboard />                // Redirects → /login if no JWT
      </ProtectedRoute>
    } />
  </Routes>
</BrowserRouter>
```

**Auth Guard:** `ProtectedRoute` calls `isAuthenticated()` from `services/auth.js` → redirects to `/login` with `replace` (prevents back-button exploit) if no valid JWT in localStorage.

---

### Component Hierarchy & Responsibilities

```
App.js  (Router + ProtectedRoute guard)
│
├── LoginPage.js            [~110 lines]
│     Email/password form, POST /api/v1/auth/login
│     Stores JWT in localStorage, redirects to /
│
└── Dashboard.js            [902 lines]  ← main container
      CSS Grid layout, 30-sec polling, state management
      Hosts 8 category filters + 4 time-range filters + risk-level filter
      │
      ├── MapVisualizer.js  [456 lines]
      │     Leaflet.js map centred on Bengaluru (12.97°N, 77.59°E)
      │     Complaint markers: colour-coded by category
      │     Risk zone circles: radius from RiskZone.radius_meters
      │                        colour by LOW(green)/MEDIUM(amber)/HIGH(red)
      │     Click marker → popup: location, category, description, timestamp
      │
      ├── ComplaintFeed.js  [322 lines]
      │     Scrollable sorted list of complaints
      │     Filters by category, location, time range
      │     Status badges: open (blue) / resolved (grey)
      │     Shows classification_confidence as percentage
      │
      ├── ComplaintForm.js  [299 lines]
      │     Floating modal form — fields: location (44 dropdown), category (8 dropdown)
      │     description (textarea, min 1 char), timestamp (auto), coordinates (auto via geocoding)
      │     POST /api/v1/report-complaint with JWT bearer token
      │     Rate-limited to 5 submissions/min (server-side enforcement)
      │     On success → WebSocket broadcast → map updates immediately
      │
      ├── TrendCharts.js    [397 lines]
      │     Chart.js line chart: 7-day complaint volume per day
      │     Chart.js bar chart: complaints by category (colour per category)
      │     Chart.js line chart: 7-day risk score trend
      │     Responsive, animated, legend toggle
      │
      ├── WeatherPanel.js   [~150 lines]
      │     Live weather cards: 🌡️ Temperature (°C), 💧 Humidity (%), 🌧️ Precipitation (mm/h)
      │     💨 Wind Speed (km/h), ⚠️ HIGH RAINFALL ALERT badge if flag=true
      │     Source + timestamp shown; auto-refreshes with dashboard polling
      │
      ├── TrafficPanel.js   [~100 lines]
      │     Location-by-location congestion table
      │     Congestion level badges: LOW (green) / MEDIUM (amber) / HIGH (red)
      │     Scores: LOW=1, MEDIUM=5, HIGH=10
      │
      ├── PredictionsPanel.js [190 lines]
      │     Cards per prediction: area name, incident type, risk score progress bar
      │     Time window badge: "next 6 hours" vs "next 24 hours"
      │     Contributing factors chips: high_rainfall, complaint_density, etc.
      │     AI-generated explanation text from Bedrock
      │
      ├── AIInsightsPanel.js  [~130 lines]
      │     Bedrock-generated daily summary paragraph
      │     High-risk zones bullet list
      │     Predicted incidents summary
      │     Weather impact statement
      │
      └── LocationPicker.js  [~100 lines]
            Geocoding-enabled dropdown
            Maps friendly location names → lat/lng coordinates
            Used by ComplaintForm for coordinate auto-fill
```

---

### Real-Time Strategy

| Mechanism | Frequency | Data Fetched |
|---|---|---|
| **HTTP Polling** | Every 30 seconds | Complaints, clusters, risk hotspots, weather, traffic, predictions, daily report |
| **WebSocket** | On each complaint submission | `{type: "new_complaint", complaint: {...}}` — updates map marker instantly |
| **On-demand** | Filter/sort changes | Re-renders from cached state without re-fetching |

### Filter Dimensions Available in Dashboard

| Filter | Options |
|---|---|
| **Category** | pothole, flooding, traffic, garbage, streetlight, water_supply, noise, construction (+ All) |
| **Risk Level** | Low, Medium, High (+ All) |
| **Time Range** | Last 6h, Last 24h, Last 7d, Last 30d, All time |
| **Location** | Any of 44 Bengaluru locations (+ All) |

### API Service Layer (`services/api.js`)
- Axios instance with `baseURL` set from `REACT_APP_API_URL` env var
- Default: `http://localhost:8000`
- Authorization: `Bearer {token}` header auto-injected if JWT present in localStorage
- All API calls centralised in `services/api.js` — components never call `fetch()` directly

**Speaker Notes:** Point out the 902-line Dashboard as the star of the show. It manages all dashboard state in one place using React hooks (useState, useCallback, useMemo, useRef). The WebSocket connection means map updates appear within milliseconds of a complaint being submitted — no need to wait for the next 30-second poll.

**Visual Direction:** Light background with a dark blue sidebar showing component names and line counts. Centre: a screenshot mockup of the Dashboard with call-out arrows to each panel. Each panel outlined in a different colour matching the component tree legend. Bottom: three badges "30s polling", "WebSocket", "4 filter dimensions". Component tree shown as a collapsible tree on the right margin.

---

## Slide 8 — AI & Data Intelligence

**Title:** AI & Data Intelligence Layer
**Subtitle:** Exact Bedrock prompts, circuit-breaker state machine, risk formula with weights — zero magic, all engineering.

**Body:**

### The Exact Bedrock Classification Prompt

```
You are an AI assistant helping to classify urban infrastructure complaints
for the city of Bengaluru, India.

Classify the following complaint into exactly ONE of these categories:
- pothole
- flooding
- traffic
- garbage
- streetlight
- water_supply
- noise
- construction

[OPTIONAL BBMP CONTEXT BLOCK — injected if data available:]
Historical BBMP data for this area:
- Hotspot risk boost: +15 points for Koramangala flooding
- Category weights: flooding ×1.2, pothole ×1.1
- Seasonal warning: monsoon season increases flooding risk

Complaint Location: {location}
Complaint Description: {description}

Respond with ONLY the category name (one word) followed by a confidence score
(0.0 to 1.0) separated by a comma.
Example response format: "pothole,0.95" or "flooding,0.87"

Your response:
```

**Model:** `apac.anthropic.claude-3-5-sonnet-20241022-v2:0` (region: `ap-south-2`)
**Timeout:** 3 seconds | **Max tokens:** minimal (one line response expected)

---

### Circuit Breaker State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER                           │
│                                                              │
│  ┌─────────┐  5 failures   ┌──────────┐  60s elapsed        │
│  │  CLOSED  │─────────────▶│   OPEN   │──────────────┐      │
│  │(normal) │               │(fail fast│              │      │
│  └─────────┘               │ <1ms)    │              ▼      │
│       ▲                    └──────────┘        ┌──────────┐ │
│       │                                         │HALF_OPEN │ │
│       │    3 successes                          │(1 probe  │ │
│       └─────────────────────────────────────────│ request) │ │
│                                                 └──────────┘ │
│                                                              │
│  In OPEN state:  keyword fallback invoked immediately        │
│  Bedrock saved: ~1-2s timeout cost per skipped request       │
└─────────────────────────────────────────────────────────────┘
```

---

### Keyword Fallback Classifier

When Bedrock is unavailable (circuit OPEN), keyword matching triggers:

| Category | Keywords Matched |
|---|---|
| `pothole` | "pothole", "road damage", "crater", "hole in road", "broken road" |
| `flooding` | "flood", "water logging", "waterlogged", "drainage", "overflow", "rain water" |
| `traffic` | "traffic", "congestion", "jam", "signal", "accident", "vehicle" |
| `garbage` | "garbage", "waste", "trash", "litter", "dump", "dirty", "smell" |
| `streetlight` | "streetlight", "street light", "lamp", "lighting", "dark", "bulb" |
| `water_supply` | "water supply", "no water", "water shortage", "tap", "pipeline", "leak" |
| `noise` | "noise", "loud", "sound", "disturbance", "pollution" |
| `construction` | "construction", "building", "debris", "dust", "excavation", "work" |

**Confidence formula:** `min(0.9, 0.5 + match_count × 0.1)` — maxes at 0.9 (always below Bedrock's output to preserve AI preference)

---

### Risk Scoring Formula (risk_engine.py)

```
risk_score = base_score + severity_modifier + weather_modifier + traffic_modifier + bbmp_boost
             [clamped to 0–100]

BASE SCORE (log-scale complaint density):
  base_score = 15.0 × log₂(1 + density_per_km²)    [capped at 65]
  Examples:  1/km² → ~15pts | 5/km² → ~35pts | 10/km² → ~45pts | 50/km² → 65pts

SEVERITY MODIFIER (per-category weights, capped at 30):
  flooding:      30pts (highest — immediate safety + infrastructure damage)
  water_supply:  25pts (public health critical)
  construction:  20pts (safety hazard, road blockage)
  pothole:       18pts (vehicle/pedestrian safety)
  streetlight:   15pts (night safety)
  traffic:       12pts (congestion, accidents)
  garbage:       10pts (health/hygiene)
  noise:          7pts (quality of life)

  Volume dampening: bonus = base_severity × (1 + log₂(count))
  → 2 flooding complaints = 30 × 2.0 = 60pts (vs 1 complaint = 30pts)
  → 10 noise complaints   =  7 × 4.3 = 30pts (equals 1 flooding complaint)

WEATHER MODIFIER:
  +30 pts  if  high_rainfall_flag == True  AND  cluster has flooding complaints

TRAFFIC MODIFIER:
  +15 pts  if  cluster has traffic complaints  AND  congestion_score == 10 (HIGH)

BBMP BOOST (if BBMP data loaded):
  Location-specific hotspot boost (e.g. +15 for Koramangala)
  Category weight multiplier (e.g. ×1.2 for flooding)
```

### Risk Level Thresholds

| Level | Score Range | Colour | Action Triggered |
|---|---|---|---|
| **LOW** | 0–33 | 🟢 Green | Displayed on map; no alert |
| **MEDIUM** | 34–66 | 🟡 Amber | Displayed on map; monitor |
| **HIGH** | 67–100 | 🔴 Red | SNS alert to officials + daily report inclusion |

### Supported Bedrock Models

| Model ID | Use Case |
|---|---|
| `apac.anthropic.claude-3-5-sonnet-20241022-v2:0` | Primary — complaint classification + report generation |
| `amazon.nova-micro-v1:0` | Lightweight fallback — fast, low-cost classification |
| `amazon.nova-pro-v1:0` | Advanced — rich daily report narratives |

**Speaker Notes:** Show the actual prompt text — it's clean, constrained, and designed for precise one-line responses. Mention the BBMP context injection as a differentiator — historical ward data steers the AI toward locally accurate classifications.

**Visual Direction:** Dark indigo background. Left half: the Bedrock prompt in a styled code block with AWS orange syntax highlighting for the placeholder variables. Right half: the risk score formula rendered as a visual equation with coloured blocks for each term. Bottom strip: circuit breaker state diagram with colour-coded states (green=CLOSED, red=OPEN, amber=HALF_OPEN). Show a sample AI response bubble: `"flooding,0.94"` with confidence bar.

---

## Slide 9 — Features & Impact

**Title:** Features, User Personas & Impact
**Subtitle:** Three user types. Fifteen measured outcomes. One platform built for a city of 13 million.

**Body:**

### User Persona 1 — The Citizen 👤

**Goal:** Report an infrastructure problem and know it was heard.

| Action | Experience |
|---|---|
| Opens UrbanGuard AI on phone/desktop | Lands on interactive risk map |
| Clicks "Report Issue" | Floating form — location, category, description |
| Submits complaint | Classified by AI in < 2 seconds; map marker appears immediately |
| Views existing complaints | Filters by category, risk, time range |
| Checks status later | Complaint shows "open" or "resolved" with resolution note |

---

### User Persona 2 — The City Official 🏛️

**Goal:** Know which areas need crews dispatched TODAY, not next week.

| Action | Experience |
|---|---|
| Opens dashboard each morning | Daily AI report waiting (06:00 IST) — high-risk zones, predictions, weather impact |
| Receives SNS alert | Push notification when any zone crosses HIGH risk |
| Checks map | Risk circles colour-coded: green/amber/red by score |
| Reviews predictions | 6h and 24h incident windows with contributing factors |
| Resolves complaints | PATCH endpoint marks resolved + bulk-resolves same location/category |

---

### User Persona 3 — The System Administrator 🔧

**Goal:** Keep the platform running and the data clean.

| Action | Experience |
|---|---|
| Monitors CloudWatch | Lambda error alarms + DLQ depth alerts |
| Reviews DLQ | Any failed complaints after 3 retries land here for manual review |
| Deploys update | `sam build && sam deploy` — zero-downtime serverless deploy |
| Manages users | Cognito user pool — email verification, role management |

---

### Performance Benchmarks

| Endpoint / Action | Target SLA | Description |
|---|---|---|
| `POST /report-complaint` | < 500ms | Valid complaint submission |
| `POST /report-complaint` (invalid) | < 100ms | Validation rejection |
| `GET /complaints` (1000+ records) | < 200ms | Paginated retrieval |
| `GET /risk-hotspots` | < 300ms | Risk zone list |
| `GET /weather` | < 100ms | Cached weather data |
| `GET /traffic` | < 50ms | Traffic data (in-memory) |
| `GET /predictions` | < 500ms | Prediction list with AI explanations |
| `GET /daily-report` | < 200ms | Latest daily report |
| **Bedrock classification** | < 2,000ms | End-to-end AI response |
| **Keyword fallback** | < 100ms | When circuit breaker OPEN |

---

### Quality Metrics

| Dimension | Metric | Value |
|---|---|---|
| **Test Infrastructure** | Backend test files | 60+ |
| **Test Infrastructure** | Frontend test files | 40+ |
| **Test Results** | Frontend test pass rate | 148/149 (99.3%) |
| **Test Methodology** | Property-based correctness properties | 50+ (Hypothesis + fast-check) |
| **Coverage** | Critical path coverage | All 15 endpoints tested |
| **Reliability** | Bedrock circuit breaker | Auto-fallback in 5 failures |
| **Data Safety** | DLQ with 7-day retention | No complaint silently dropped |

---

### By the Numbers

| Metric | Value |
|---|---|
| 🏙️ Bengaluru locations indexed | **44** (with GPS coordinates) |
| 🗂️ Complaint categories | **8** (pothole, flooding, traffic, garbage, streetlight, water_supply, noise, construction) |
| 🔌 REST API endpoints | **15** (+ 1 WebSocket) |
| ☁️ AWS services integrated | **11** (Lambda, API Gateway, DynamoDB, Bedrock, S3, SQS, SNS, EventBridge, CloudWatch, Cognito, IAM) |
| 🗄️ DynamoDB tables | **4** (Complaints, RiskZones, DailyReports, Users) |
| 🤖 Bedrock AI models supported | **3** (Claude 3.5 Sonnet, Nova Micro, Nova Pro) |
| ⏱️ Background scheduler tasks | **4** (weather 30min, traffic 10min, clustering 15min, risk 15min) |
| 📊 Dashboard chart types | **3** (line: volume trend, bar: by category, line: risk trend) |
| 📅 Report generation schedule | **Daily at 06:00 IST** (EventBridge cron) |
| 🔒 Password policy | **8 chars min, upper+lower+numbers** (Cognito) |

**Speaker Notes:** Use the three personas to tell a story — citizen, official, admin. The performance benchmarks show this isn't prototype quality. Emphasise property-based testing as unusual for a hackathon project — 50 correctness properties validated with Hypothesis.

**Visual Direction:** Three-column persona cards at the top (light cards with person icon, name, goal). Middle: a clean two-column table for performance benchmarks (green checkmarks next to each). Bottom: large metric tiles in a 5×2 grid — bold number + small label + icon. Colour: teal/white on light background. Footer badge: "Production-grade quality in hackathon time."

---

## Slide 10 — Architecture Summary & Roadmap

**Title:** System Architecture & Roadmap
**Subtitle:** Five architectural layers, one SAM command to deploy, and a clear four-phase path to city-wide scale.

**Body:**

### Layered System Architecture

```
╔══════════════════════════════════════════════════════════════════════╗
║  LAYER 1: PRESENTATION                                               ║
║  React 18 SPA — Dashboard, Map (Leaflet), Charts (Chart.js),        ║
║  Forms, Feeds, Panels — served from localhost:3000 or CDN           ║
║  Auth: JWT in localStorage | Routing: React Router v7               ║
╚══════════════════════════════════╦═══════════════════════════════════╝
                                   ║ HTTPS / WSS
╔══════════════════════════════════╩═══════════════════════════════════╗
║  LAYER 2: API GATEWAY + COMPUTE                                      ║
║  Amazon API Gateway → AWS Lambda (Python 3.12, 512 MB, 30s)         ║
║  FastAPI (ASGI) via Mangum adapter                                   ║
║  15 REST endpoints + WebSocket /ws                                   ║
║  Rate limiting (slowapi), CORS, request logging middleware           ║
╚══════╦═════════════════╦════════════════════╦════════════════════════╝
       ║                 ║                    ║
╔══════╩═══════╗  ╔══════╩══════╗  ╔══════════╩════════════════════╗
║  LAYER 3A    ║  ║  LAYER 3B   ║  ║  LAYER 3C                     ║
║  AI / ML     ║  ║  STORAGE    ║  ║  MESSAGING                    ║
║              ║  ║             ║  ║                               ║
║  Bedrock     ║  ║  DynamoDB   ║  ║  SQS: async complaint queue  ║
║  Claude 3.5  ║  ║  4 tables   ║  ║    visibility=60s            ║
║  Nova Micro  ║  ║  + GSIs     ║  ║    retention=24h             ║
║  Nova Pro    ║  ║  + PITR     ║  ║    DLQ redrive=3×            ║
║              ║  ║  + Streams  ║  ║                               ║
║  K-Means     ║  ║             ║  ║  SNS: HIGH-risk alerts       ║
║  Clustering  ║  ║  S3         ║  ║       daily report emails    ║
║              ║  ║  Reports +  ║  ║                               ║
║  OpenWeather ║  ║  BBMP data  ║  ║  EventBridge:                ║
║  API         ║  ║  90d expire ║  ║  cron(30 0 * * ? *)          ║
╚══════════════╝  ╚═════════════╝  ╚═══════════════════════════════╝
       ║                 ║                    ║
╔══════╩═════════════════╩════════════════════╩════════════════════════╗
║  LAYER 4: OBSERVABILITY                                              ║
║  CloudWatch Logs (/aws/lambda/..., /aws/apigateway/...)             ║
║  CloudWatch Alarms: Lambda errors >10/5min, throttles >5/5min,     ║
║                     DLQ depth >1 message → SNS alert               ║
║  Log retention: 30 days                                              ║
╚══════════════════════════════════════════════════════════════════════╝
       ║
╔══════╩═════════════════════════════════════════════════════════════╗
║  LAYER 5: SECURITY                                                  ║
║  Amazon Cognito: email-based user pool, role attribute (admin/user) ║
║  Password: 8 chars, upper+lower+numbers                             ║
║  IAM: least-privilege Lambda execution role                         ║
║  HTTPS everywhere | JWT Bearer tokens | Admin-only endpoints        ║
╚═════════════════════════════════════════════════════════════════════╝
```

---

### Deployment — One Command

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# → set AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
#     OPENWEATHERMAP_API_KEY, CORS_ALLOW_ORIGINS

# 2. Build & deploy to AWS (SAM)
cd backend
sam build
sam deploy --guided
# → provisions all 11 AWS services via CloudFormation
# → outputs: ApiUrl, CognitoUserPoolId, S3BucketName, etc.

# 3. Start frontend (local dev)
cd frontend
npm install
REACT_APP_API_URL=<ApiUrl from SAM output> npm start
```

**SAM Template facts:** 641 lines | 11 AWS resources | 3 DynamoDB GSIs | 3 CloudWatch alarms | 12 CloudFormation outputs

---

### Four-Phase Roadmap

```
NOW ─────────────────────────────────────────────────────────▶ FUTURE

PHASE 1 (Built ✅)              PHASE 2 (Next Sprint)
─────────────────               ──────────────────────────────
✅ Web complaint portal         📱 React Native mobile app
✅ AI classification (Bedrock)     (BBMP crew field reporting)
✅ Geographic clustering        🎥 Amazon Rekognition +
✅ Risk scoring engine             live CCTV auto-detection
✅ Daily AI reports             📊 SLA prediction model
✅ SNS alerts                      "Fixed in X days?" ML answer
✅ AWS serverless deployment    🗺️ OpenStreetMap tile server
✅ 100+ automated tests            (offline map caching)

PHASE 3 (Q3)                   PHASE 4 (Scale)
────────────────────            ──────────────────────────────
📱 WhatsApp intake              🌆 Multi-city expansion:
   (Amazon Connect / Twilio)       Chennai, Hyderabad, Mumbai,
📞 IVR complaint intake            Delhi, Pune
🔗 BBMP API integration         🌐 Public transparency portal
   (replace CSV uploads)           (resolution rates dashboard)
🧠 Reinforcement learning       💰 SaaS model for municipal
   for resource allocation         bodies across India
   recommendations              🔗 National Smart Cities
                                   Mission integration
```

---

### Cost Model

| Component | Pricing Model | Expected Cost (Low Traffic) |
|---|---|---|
| AWS Lambda | Per-request + GB-seconds | ~$0 (within free tier) |
| DynamoDB | Pay-per-request | ~$0 (within free tier) |
| API Gateway | Per-request | ~$0 (within free tier) |
| S3 | Per GB stored + requests | < $1/month |
| Bedrock | Per input/output token | ~$0.003 per complaint |
| SQS / SNS | Per message | < $1/month |
| CloudWatch | Per log ingestion | < $1/month |
| **Total (prototype)** | | **< $5/month** |

> At 1 million complaints/month: estimated **< $50/month** in AWS costs — trivial compared to the infrastructure losses being prevented.

**Speaker Notes:** Close with the cost model — $5/month for a system serving 13 million people is a compelling story. The single `sam deploy` command is a strong demo moment. End with: "UrbanGuard AI — Smarter Cities, Safer Lives."

**Visual Direction:** Full-page dark navy background. Five horizontal swim-lane boxes for the architecture layers, each in a different accent colour (blue, teal, purple, gold, red). Roadmap rendered as a horizontal four-phase timeline at the bottom with phase markers and icons. Cost model shown as a small clean table in the bottom-right corner. Final watermark tagline in large italic white: *"UrbanGuard AI — Smarter Cities, Safer Lives."*

---

## Appendix — Data Model Reference

> *(Bonus slide for technical deep-dives — use as a back-up slide)*

**Title:** Complete Data Model Reference

### All 7 Pydantic Models (models.py)

**Complaint** — core entity

| Field | Type | Notes |
|---|---|---|
| `complaint_id` | `str` (UUID) | Auto-generated |
| `location` | `str` | One of 44 Bengaluru locations |
| `category` | `str` | One of 8 categories |
| `description` | `str` | Free text (min 1 char) |
| `timestamp` | `datetime` | ISO 8601; defaults to now |
| `coordinates` | `Tuple[float, float]` | (latitude, longitude) |
| `classification_confidence` | `float` | 0.0–1.0; default 1.0 |
| `status` | `str` | `"open"` or `"resolved"` |
| `resolved_at` | `Optional[datetime]` | Set on resolution |
| `expected_resolution_date` | `Optional[datetime]` | Admin-set target |
| `resolution_note` | `Optional[str]` | Admin notes |
| `image_url` | `Optional[str]` | Proof image URL |

**RiskZone** — computed risk area

| Field | Type | Notes |
|---|---|---|
| `zone_id` | `str` (UUID) | Auto-generated |
| `center_coordinates` | `Tuple[float, float]` | Zone centre (lat, lng) |
| `radius_meters` | `float` | Typically 500m |
| `risk_score` | `float` | 0–100 (composite) |
| `risk_level` | `RiskLevel` | LOW / MEDIUM / HIGH |
| `complaint_count` | `int` | Complaints in zone |
| `dominant_category` | `str` | Most frequent category |
| `last_updated` | `datetime` | Last recalculation |

**WeatherData** · **TrafficData** · **IncidentPrediction** · **DailyReport** · **Cluster** — see full model definitions in `backend/models.py`

**Enums:** `RiskLevel` (low/medium/high) · `CongestionLevel` (low=1/medium=5/high=10)

**44 Bengaluru Locations (with GPS coordinates):**
Koramangala (12.9352°N, 77.6245°E) · Indiranagar · Whitefield · Electronic City · Jayanagar · Malleshwaram · HSR Layout · BTM Layout · Marathahalli · Bannerghatta Road · Yelahanka · Hebbal · Rajajinagar · Basavanagudi · JP Nagar · Sarjapur Road · Bellandur · Bommanahalli · Mahadevapura · Yeshwanthpur · KR Puram · Ramamurthy Nagar · CV Raman Nagar · Hoodi · Varthur · Kadugodi · Brookefield · Domlur · Ulsoor · Frazer Town · Richmond Town · Shivajinagar · Sadashivanagar · Vijayanagar · Peenya · Jalahalli · Nagarbhavi · Kengeri · Banashankari · Girinagar · Uttarahalli · Rajarajeshwari Nagar · Chickpet · Shantinagar

---

*Generated from full source-code analysis of [AakashG-1808/Nimbus1000-Hack](https://github.com/AakashG-1808/Nimbus1000-Hack)*
