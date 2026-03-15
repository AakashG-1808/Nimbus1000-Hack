# Storage Layer

## Overview

The UrbanGuard AI storage layer provides **two backends** that share an identical interface, making it seamless to switch between local development and production:

| Backend | When used | Module |
|---------|-----------|--------|
| `InMemoryStorage` | Local development (default) | `storage.py` |
| `DynamoDBStorage` | AWS Lambda / any env with `USE_DYNAMODB=true` | `dynamodb_storage.py` |

The correct backend is selected automatically by `get_storage()` in `storage.py`. No application code needs to change when switching.

---

## Enabling DynamoDB

### Option A — Real AWS DynamoDB

1. Create the tables (see *DynamoDB Tables* below or deploy via SAM: `sam deploy`).
2. Add to your `backend/.env`:
   ```env
   USE_DYNAMODB=true
   AWS_REGION=ap-south-2
   AWS_ACCESS_KEY_ID=<your-key>
   AWS_SECRET_ACCESS_KEY=<your-secret>
   DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints
   DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones
   DYNAMODB_TABLE_REPORTS=urbanguard-reports
   DYNAMODB_TABLE_USERS=urbanguard-users
   ```
3. Start the backend normally: `python -m uvicorn main:app --reload --port 8000`

### Option B — DynamoDB Local (no AWS account needed)

1. Download DynamoDB Local from the [AWS docs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html).
2. Start it: `java -jar DynamoDBLocal.jar -sharedDb -port 8001`
3. Create the tables using the AWS CLI (pointing at localhost):
   ```bash
   aws dynamodb create-table --table-name urbanguard-complaints \
     --attribute-definitions AttributeName=complaint_id,AttributeType=S \
     --key-schema AttributeName=complaint_id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --endpoint-url http://localhost:8001

   aws dynamodb create-table --table-name urbanguard-risk-zones \
     --attribute-definitions AttributeName=zone_id,AttributeType=S \
     --key-schema AttributeName=zone_id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --endpoint-url http://localhost:8001

   aws dynamodb create-table --table-name urbanguard-reports \
     --attribute-definitions AttributeName=report_id,AttributeType=S AttributeName=date,AttributeType=N \
     --key-schema AttributeName=report_id,KeyType=HASH AttributeName=date,KeyType=RANGE \
     --billing-mode PAY_PER_REQUEST \
     --endpoint-url http://localhost:8001

   aws dynamodb create-table --table-name urbanguard-users \
     --attribute-definitions AttributeName=email,AttributeType=S \
     --key-schema AttributeName=email,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --endpoint-url http://localhost:8001
   ```
4. Add to `backend/.env`:
   ```env
   USE_DYNAMODB=true
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=dummy
   AWS_SECRET_ACCESS_KEY=dummy
   DYNAMODB_ENDPOINT_URL=http://localhost:8001
   DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints
   DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones
   DYNAMODB_TABLE_REPORTS=urbanguard-reports
   DYNAMODB_TABLE_USERS=urbanguard-users
   ```
5. Start the backend: `python -m uvicorn main:app --reload --port 8000`

### Option C — AWS Lambda (production)

When the Lambda function runs, `AWS_EXECUTION_ENV` is automatically set by the runtime, so DynamoDB is selected without needing `USE_DYNAMODB=true`. Table names are injected via the SAM template environment variables (see `template.yaml`).

---

## DynamoDB Tables

| Table | Primary key | Sort key | Notes |
|-------|-------------|----------|-------|
| `urbanguard-complaints` | `complaint_id` (S) | — | GSI on `category` + `timestamp` |
| `urbanguard-risk-zones` | `zone_id` (S) | — | GSI on `risk_level` + `risk_score` |
| `urbanguard-reports` | `report_id` (S) | `date` (N) | TTL enabled (30 days) |
| `urbanguard-users` | `email` (S) | — | Auth users |

All tables use **PAY_PER_REQUEST** billing and have **Point-in-Time Recovery** enabled.

---

## DynamoDBStorage Class (`dynamodb_storage.py`)

### Key Design Decisions

- **Type conversion** — `float` values are stored as `Decimal` (DynamoDB requirement) and converted back transparently.
- **Timestamps** — stored as Unix epoch numbers (`N` type) to enable range-key sorting on the reports table.
- **Pagination** — all `scan` calls follow `LastEvaluatedKey` to retrieve the full dataset beyond the 1 MB page limit.
- **Reserved keywords** — `location` and `category` are DynamoDB reserved words; all filter expressions use `ExpressionAttributeNames` aliases (`#loc`, `#cat`).
- **`update_risk_zones`** — performs a batch delete of all existing zones followed by a batch put of the new set (atomic replacement per calculation cycle).
- **`clear_all`** — uses `batch_writer` for each table; the reports table delete passes both composite key components (`report_id` + `date`).
- **Custom endpoint** — set `DYNAMODB_ENDPOINT_URL` to redirect to DynamoDB Local without changing any other code.

### API Methods

**Complaint Operations**
- `add_complaint(complaint)` — PutItem to complaints table
- `get_all_complaints()` — Scan + sort by timestamp descending
- `get_complaints_by_location(location)` — FilterExpression on `#loc`
- `get_complaints_by_category(category)` — FilterExpression on `#cat`
- `get_complaint_count()` — Scan with `Select='COUNT'`

**Risk Zone Operations**
- `add_risk_zone(zone)` — PutItem to risk-zones table
- `update_risk_zones(zones)` — Batch delete all + batch put new list
- `get_all_risk_zones()` — Scan with pagination
- `get_high_risk_zones(min_score)` — FilterExpression on `risk_score`

**Daily Report Operations**
- `add_daily_report(report)` — PutItem with a 30-day TTL attribute
- `get_latest_report()` — Scan + pick max date
- `get_all_reports()` — Scan with pagination + sort descending

---

## InMemoryStorage Class (`storage.py`)

Thread-safe in-memory storage backed by Python lists and a `threading.Lock`.  
Used automatically during local development when `USE_DYNAMODB` is not set.

**API Methods** (identical interface to DynamoDBStorage):

Complaint Operations:
- `add_complaint(complaint)` — Append to list
- `get_all_complaints()` — Return sorted copy
- `get_complaints_by_location(location)` — List comprehension filter
- `get_complaints_by_category(category)` — List comprehension filter
- `get_complaint_count()` — `len()`

Risk Zone Operations:
- `add_risk_zone(risk_zone)` — Append to list
- `update_risk_zones(risk_zones)` — Replace list
- `get_all_risk_zones()` — Return copy
- `get_high_risk_zones(min_score)` — Filter by score

Daily Report Operations:
- `add_daily_report(report)` — Append + trim to 30 most recent
- `get_latest_report()` — Return max by date
- `get_all_reports()` — Return sorted copy

---

## Simulated Data (`simulated_data.py`)

**Data Generation:**
- Generates 45 realistic complaints by default (exceeds 40+ requirement)
- Distributed across 30+ Bengaluru locations
- Covers all 8 complaint categories
- Timestamps spread over last 7 days
- Realistic descriptions from category-specific templates

**Functions:**

`generate_simulated_complaints(count=45)`
- Generates random complaints across Bengaluru
- Returns list of Complaint objects

`generate_clustered_complaints(location, category, count=5)`
- Generates complaints at a specific location (for cluster testing)

`initialize_storage_with_simulated_data(storage)`
- Populates the given storage instance with 45 complaints on startup
- Called automatically in the FastAPI `lifespan` handler

---

## Testing

### DynamoDB Tests (`test_dynamodb_storage.py`)

Uses [moto](https://github.com/getmoto/moto) to mock AWS DynamoDB in-process — no real AWS account needed.

```bash
cd backend
python -m pytest test_dynamodb_storage.py -v
```

Covers: add/retrieve complaints, sort order, location/category filters, count, coordinates round-trip, risk zone CRUD, batch update/replace, high-risk filtering, report CRUD, nested object round-trips, clear_all, and the `get_storage()` factory.

### InMemory Tests (`test_storage.py`)

```bash
cd backend
python test_storage.py
```

Covers: 40+ complaint initialization, valid properties, timestamp sorting, location/category distribution, clustered complaint generation, thread safety.

