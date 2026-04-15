# AWS Lambda Configuration Guide

## Overview

This guide explains how to configure and deploy the UrbanGuard AI System as AWS Lambda functions with API Gateway and DynamoDB.

**Task 22.1 Implementation:**
- ✅ Lambda handler wrapper for FastAPI (using Mangum)
- ✅ Environment variable configuration for AWS services
- ✅ DynamoDB client code with in-memory fallback
- ✅ Cold start performance optimization (< 3 seconds)

## Architecture

```
API Gateway → Lambda Function → DynamoDB Tables
                ↓
            FastAPI App
```

## Files Added

### 1. `lambda_handler.py`
Lambda handler wrapper that makes FastAPI compatible with AWS Lambda using the Mangum adapter.

**Key Features:**
- Translates API Gateway events to ASGI format
- Handles Lambda context and event objects
- Optimized for cold start performance

### 2. `dynamodb_storage.py`
DynamoDB storage implementation with full CRUD operations for complaints, risk zones, and daily reports.

**Key Features:**
- Type conversion between Python and DynamoDB formats
- Batch operations for efficiency
- Error handling with retry logic
- Automatic TTL for 30-day report retention

### 3. Modified `storage.py`
Enhanced storage module that automatically selects between InMemoryStorage (local dev) and DynamoDBStorage (AWS Lambda).

**Environment Detection:**
- `AWS_EXECUTION_ENV`: Automatically set by Lambda runtime
- `USE_DYNAMODB`: Explicit flag to force DynamoDB usage

## Environment Variables

### Required for AWS Lambda Deployment

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_EXECUTION_ENV=AWS_Lambda_python3.11  # Set automatically by Lambda

# DynamoDB Tables
DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints
DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones
DYNAMODB_TABLE_REPORTS=urbanguard-reports

# External APIs (same as local dev)
OPENWEATHERMAP_API_KEY=your_api_key_here
AWS_BEDROCK_REGION=us-east-1
```

### Optional Configuration

```bash
# Force DynamoDB usage (for testing)
USE_DYNAMODB=true

# Custom table names
DYNAMODB_TABLE_COMPLAINTS=custom-complaints-table
DYNAMODB_TABLE_RISK_ZONES=custom-risk-zones-table
DYNAMODB_TABLE_REPORTS=custom-reports-table
```

## DynamoDB Table Schemas

### Complaints Table

```yaml
Table Name: urbanguard-complaints
Primary Key: complaint_id (String)
Attributes:
  - complaint_id: String (UUID)
  - location: String
  - category: String
  - description: String
  - timestamp: Number (Unix timestamp)
  - coordinates: Map
    - lat: Number
    - lon: Number
  - classification_confidence: Number

Global Secondary Index (Optional):
  Name: timestamp-index
  Partition Key: category
  Sort Key: timestamp
```

### Risk Zones Table

```yaml
Table Name: urbanguard-risk-zones
Primary Key: zone_id (String)
Attributes:
  - zone_id: String (UUID)
  - center_coordinates: Map
    - lat: Number
    - lon: Number
  - radius_meters: Number
  - risk_score: Number
  - risk_level: String (low/medium/high)
  - complaint_count: Number
  - dominant_category: String
  - last_updated: Number (Unix timestamp)

Global Secondary Index (Optional):
  Name: risk-score-index
  Partition Key: risk_level
  Sort Key: risk_score
```

### Daily Reports Table

```yaml
Table Name: urbanguard-reports
Primary Key: report_id (String)
Sort Key: date (Number - Unix timestamp)
Attributes:
  - report_id: String (UUID)
  - date: Number (Unix timestamp)
  - total_complaints: Number
  - high_risk_zones: List (embedded RiskZone objects)
  - predicted_incidents: List (embedded IncidentPrediction objects)
  - weather_summary: String
  - ai_generated_summary: String
  - created_at: Number (Unix timestamp)
  - ttl: Number (Unix timestamp + 30 days)

TTL Attribute: ttl (automatic deletion after 30 days)
```

## Deployment Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Create DynamoDB Tables

Using AWS CLI:

```bash
# Complaints table
aws dynamodb create-table \
  --table-name urbanguard-complaints \
  --attribute-definitions \
    AttributeName=complaint_id,AttributeType=S \
  --key-schema \
    AttributeName=complaint_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Risk zones table
aws dynamodb create-table \
  --table-name urbanguard-risk-zones \
  --attribute-definitions \
    AttributeName=zone_id,AttributeType=S \
  --key-schema \
    AttributeName=zone_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Reports table with TTL
aws dynamodb create-table \
  --table-name urbanguard-reports \
  --attribute-definitions \
    AttributeName=report_id,AttributeType=S \
    AttributeName=date,AttributeType=N \
  --key-schema \
    AttributeName=report_id,KeyType=HASH \
    AttributeName=date,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Enable TTL on reports table
aws dynamodb update-time-to-live \
  --table-name urbanguard-reports \
  --time-to-live-specification \
    Enabled=true,AttributeName=ttl \
  --region us-east-1
```

### 3. Package Lambda Function

```bash
# Create deployment package
cd backend
pip install -r requirements.txt -t package/
cp *.py package/
cd package
zip -r ../lambda-deployment.zip .
cd ..
```

### 4. Create Lambda Function

Using AWS CLI:

```bash
aws lambda create-function \
  --function-name urbanguard-api \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{
    AWS_REGION=us-east-1,
    DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints,
    DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones,
    DYNAMODB_TABLE_REPORTS=urbanguard-reports,
    OPENWEATHERMAP_API_KEY=your_api_key,
    AWS_BEDROCK_REGION=us-east-1
  }" \
  --region us-east-1
```

### 5. Configure API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
  --name urbanguard-api \
  --description "UrbanGuard AI System API" \
  --region us-east-1

# Configure proxy integration with Lambda
# (Use AWS Console or CloudFormation for detailed configuration)
```

### 6. Set Up IAM Permissions

Lambda execution role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/urbanguard-complaints",
        "arn:aws:dynamodb:us-east-1:*:table/urbanguard-risk-zones",
        "arn:aws:dynamodb:us-east-1:*:table/urbanguard-reports"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Local Development with DynamoDB

To test DynamoDB integration locally:

### Option 1: Use DynamoDB Local

```bash
# Start DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Set environment variables
export USE_DYNAMODB=true
export AWS_REGION=us-east-1
export DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints
export DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones
export DYNAMODB_TABLE_REPORTS=urbanguard-reports

# Run application
python main.py
```

### Option 2: Use AWS DynamoDB (with credentials)

```bash
# Configure AWS credentials
aws configure

# Set environment variables
export USE_DYNAMODB=true
export AWS_REGION=us-east-1

# Run application
python main.py
```

## Testing

Run Lambda compatibility tests:

```bash
cd backend
pytest test_lambda_compatibility.py -v
```

**Test Coverage:**
- ✅ Storage selection (InMemory vs DynamoDB)
- ✅ Lambda handler signature and invocation
- ✅ Cold start performance (< 3 seconds)
- ✅ Environment variable configuration
- ✅ DynamoDB operations with mocked client
- ✅ Error handling and graceful fallback

## Performance Optimization

### Cold Start Optimization

**Current Implementation:**
- Lazy loading of heavy dependencies
- Minimal imports in lambda_handler.py
- Efficient Mangum adapter configuration

**Expected Performance:**
- Cold start: < 3 seconds (Requirement 19.5)
- Warm invocation: < 500ms

### DynamoDB Optimization

**Batch Operations:**
- `update_risk_zones()` uses batch write for efficiency
- Reduces API calls and improves performance

**Caching:**
- Weather and traffic data cached in memory
- Reduces DynamoDB read operations

## Monitoring

### CloudWatch Metrics

Monitor these key metrics:
- Lambda duration (cold start and warm)
- Lambda errors and throttles
- DynamoDB read/write capacity
- API Gateway 4xx and 5xx errors

### CloudWatch Logs

All logs are automatically sent to CloudWatch:
- Request/response logging
- Error logging with stack traces
- Component-level logging

## Cost Estimation

**Lambda:**
- Free tier: 1M requests/month, 400,000 GB-seconds
- Beyond free tier: $0.20 per 1M requests

**DynamoDB:**
- On-demand pricing: $1.25 per million write requests, $0.25 per million read requests
- Storage: $0.25 per GB-month

**API Gateway:**
- Free tier: 1M API calls/month
- Beyond free tier: $3.50 per million requests

## Troubleshooting

### Issue: Cold start timeout

**Solution:** Increase Lambda timeout to 30 seconds

```bash
aws lambda update-function-configuration \
  --function-name urbanguard-api \
  --timeout 30
```

### Issue: DynamoDB access denied

**Solution:** Verify IAM role has DynamoDB permissions

```bash
aws iam get-role-policy \
  --role-name lambda-execution-role \
  --policy-name dynamodb-access
```

### Issue: Import errors in Lambda

**Solution:** Ensure all dependencies are in deployment package

```bash
pip install -r requirements.txt -t package/
```

## Next Steps

**Task 22.2 Completed:** Deployment configuration files created

The following files have been created for one-command AWS deployment:

1. **template.yaml** - AWS SAM template with complete infrastructure definition
   - Lambda function with FastAPI + Mangum
   - API Gateway REST API with all 10 endpoints
   - 3 DynamoDB tables (complaints, risk zones, reports)
   - IAM roles and permissions
   - CloudWatch log groups

2. **samconfig.toml** - SAM CLI configuration for multiple environments
   - Development, staging, and production configurations
   - Pre-configured deployment parameters

3. **DEPLOYMENT_GUIDE.md** - Comprehensive deployment documentation
   - Step-by-step deployment instructions
   - API endpoint documentation
   - Monitoring and troubleshooting guide
   - Cost estimation

4. **DEPLOYMENT_QUICK_START.md** - Quick reference for common commands
   - One-command deployment
   - Quick troubleshooting
   - Common operations

**To deploy:**
```bash
cd backend
sam build && sam deploy --guided
```

See `DEPLOYMENT_GUIDE.md` for complete instructions.

## References

- [Mangum Documentation](https://mangum.io/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [DynamoDB Python SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
