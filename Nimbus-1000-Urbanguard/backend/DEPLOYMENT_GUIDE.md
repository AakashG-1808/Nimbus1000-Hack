# UrbanGuard AI System - AWS Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the UrbanGuard AI System to AWS using AWS SAM (Serverless Application Model).

**Task 22.2 Implementation:**
- ✅ AWS SAM template (template.yaml) with complete infrastructure definition
- ✅ API Gateway REST API with all endpoints configured
- ✅ DynamoDB table definitions with GSIs and TTL
- ✅ IAM roles and permissions for Lambda, DynamoDB, and Bedrock
- ✅ CloudWatch log groups for monitoring
- ✅ Environment-specific configurations (dev, staging, prod)

## Architecture

```
┌─────────────────┐
│   API Gateway   │ ← HTTPS requests from frontend
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Lambda Function │ ← FastAPI + Mangum adapter
│  (Python 3.11)  │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌─────────────┐  ┌──────────────┐
│  DynamoDB   │  │ Amazon       │
│  Tables (3) │  │ Bedrock      │
└─────────────┘  └──────────────┘
         │
         ▼
┌─────────────────┐
│  CloudWatch     │
│  Logs           │
└─────────────────┘
```

## Prerequisites

### 1. Install AWS SAM CLI

**macOS:**
```bash
brew install aws-sam-cli
```

**Linux:**
```bash
# Download the installer
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
```

**Windows:**
Download and run the MSI installer from: https://github.com/aws/aws-sam-cli/releases/latest

**Verify installation:**
```bash
sam --version
# Should output: SAM CLI, version 1.x.x
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

**Verify credentials:**
```bash
aws sts get-caller-identity
```

### 3. Get OpenWeatherMap API Key

1. Sign up at https://openweathermap.org/api
2. Get your free API key from the dashboard
3. Save it for the deployment step

## Deployment Steps

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Build the Application

This packages all Python dependencies and prepares the Lambda deployment package:

```bash
sam build
```

**Expected output:**
```
Building codeuri: . runtime: python3.11 ...
Running PythonPipBuilder:ResolveDependencies
Running PythonPipBuilder:CopySource

Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
```

### Step 3: Deploy to AWS

**For development environment:**

```bash
sam deploy --guided
```

You'll be prompted for:
- **Stack Name**: `urbanguard-ai-system` (or your preferred name)
- **AWS Region**: `us-east-1` (or your preferred region)
- **Parameter OpenWeatherMapApiKey**: Paste your API key
- **Parameter Environment**: `dev`
- **Confirm changes before deploy**: Y
- **Allow SAM CLI IAM role creation**: Y
- **Disable rollback**: N
- **Save arguments to configuration file**: Y
- **SAM configuration file**: `samconfig.toml`
- **SAM configuration environment**: `default`

**For subsequent deployments (after first guided deploy):**

```bash
sam deploy
```

**For production deployment:**

```bash
sam deploy --config-env prod --parameter-overrides "OpenWeatherMapApiKey=YOUR_API_KEY"
```

### Step 4: Verify Deployment

After successful deployment, SAM will output:

```
CloudFormation outputs from deployed stack
---------------------------------------------------------------------------
Outputs
---------------------------------------------------------------------------
Key                 ApiUrl
Description         API Gateway endpoint URL
Value               https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev

Key                 LambdaFunctionArn
Description         Lambda function ARN
Value               arn:aws:lambda:us-east-1:xxxxxxxxxxxx:function:urbanguard-api-dev
---------------------------------------------------------------------------
```

**Test the API:**

```bash
# Replace with your API URL from outputs
export API_URL="https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev"

# Test health endpoint
curl $API_URL/health

# Expected response:
# {"status":"healthy","complaints":0,"risk_zones":0,"reports":0}
```

## Configuration Files

### template.yaml

The main SAM template defining all AWS resources:

**Resources Created:**
1. **Lambda Function** (`UrbanGuardApiFunction`)
   - Runtime: Python 3.11
   - Memory: 512 MB
   - Timeout: 30 seconds
   - Handler: `lambda_handler.lambda_handler`

2. **API Gateway** (`UrbanGuardApi`)
   - REST API with 10 endpoints
   - CORS enabled for frontend access
   - Access logging to CloudWatch

3. **DynamoDB Tables** (3 tables)
   - `ComplaintsTable`: Stores citizen complaints
   - `RiskZonesTable`: Stores calculated risk zones
   - `DailyReportsTable`: Stores daily reports (30-day TTL)

4. **CloudWatch Log Groups** (2 groups)
   - Lambda function logs (30-day retention)
   - API Gateway access logs (30-day retention)

5. **IAM Roles and Policies**
   - DynamoDB CRUD permissions
   - Amazon Bedrock InvokeModel permission
   - CloudWatch Logs write permissions

### samconfig.toml

Configuration file for SAM CLI with environment-specific settings:

**Environments:**
- `default`: Development environment
- `staging`: Staging environment
- `prod`: Production environment

**Usage:**
```bash
# Deploy to dev (default)
sam deploy

# Deploy to staging
sam deploy --config-env staging

# Deploy to production
sam deploy --config-env prod
```

## API Endpoints

All endpoints are available at: `https://{api-id}.execute-api.{region}.amazonaws.com/{environment}`

### Available Endpoints

| Method | Path | Description | Validates |
|--------|------|-------------|-----------|
| GET | `/` | Root endpoint with API info | - |
| GET | `/health` | Health check | - |
| POST | `/report-complaint` | Submit new complaint | Req 19.2 |
| GET | `/complaints` | Get all complaints | Req 19.2 |
| GET | `/clusters` | Get complaint clusters | Req 19.2 |
| GET | `/risk-hotspots` | Get risk zones (score > 20) | Req 19.2 |
| GET | `/daily-report` | Get latest daily report | Req 19.2 |
| GET | `/weather` | Get current weather data | Req 19.2 |
| GET | `/traffic` | Get traffic congestion data | Req 19.2 |
| GET | `/predictions` | Get incident predictions | Req 19.2 |

### Example API Calls

**Submit a complaint:**
```bash
curl -X POST $API_URL/report-complaint \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Koramangala",
    "category": "pothole",
    "description": "Large pothole on main road causing traffic issues",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

**Get all complaints:**
```bash
curl $API_URL/complaints
```

**Get risk hotspots:**
```bash
curl $API_URL/risk-hotspots
```

## DynamoDB Tables

### Complaints Table

**Table Name:** `urbanguard-complaints-{environment}`

**Schema:**
- Primary Key: `complaint_id` (String)
- GSI: `timestamp-index`
  - Partition Key: `category` (String)
  - Sort Key: `timestamp` (Number)

**Attributes:**
- `complaint_id`: UUID
- `location`: String
- `category`: String (pothole, flooding, traffic, etc.)
- `description`: String
- `timestamp`: Number (Unix timestamp)
- `coordinates`: Map {lat: Number, lon: Number}
- `classification_confidence`: Number

### Risk Zones Table

**Table Name:** `urbanguard-risk-zones-{environment}`

**Schema:**
- Primary Key: `zone_id` (String)
- GSI: `risk-score-index`
  - Partition Key: `risk_level` (String)
  - Sort Key: `risk_score` (Number)

**Attributes:**
- `zone_id`: UUID
- `center_coordinates`: Map {lat: Number, lon: Number}
- `radius_meters`: Number
- `risk_score`: Number (0-100)
- `risk_level`: String (low, medium, high)
- `complaint_count`: Number
- `dominant_category`: String
- `last_updated`: Number (Unix timestamp)

### Daily Reports Table

**Table Name:** `urbanguard-reports-{environment}`

**Schema:**
- Primary Key: `report_id` (String)
- Sort Key: `date` (Number)
- TTL: `ttl` attribute (30 days)

**Attributes:**
- `report_id`: UUID
- `date`: Number (Unix timestamp)
- `total_complaints`: Number
- `high_risk_zones`: List
- `predicted_incidents`: List
- `weather_summary`: String
- `ai_generated_summary`: String
- `created_at`: Number (Unix timestamp)
- `ttl`: Number (Unix timestamp + 30 days)

## Environment Variables

The Lambda function automatically receives these environment variables:

| Variable | Description | Source |
|----------|-------------|--------|
| `AWS_REGION` | AWS region | CloudFormation |
| `DYNAMODB_TABLE_COMPLAINTS` | Complaints table name | CloudFormation |
| `DYNAMODB_TABLE_RISK_ZONES` | Risk zones table name | CloudFormation |
| `DYNAMODB_TABLE_REPORTS` | Reports table name | CloudFormation |
| `OPENWEATHERMAP_API_KEY` | Weather API key | Parameter |
| `AWS_BEDROCK_REGION` | Bedrock region | CloudFormation |
| `AWS_EXECUTION_ENV` | Lambda runtime identifier | Lambda runtime |

## Monitoring and Logging

### CloudWatch Logs

**Lambda Function Logs:**
- Log Group: `/aws/lambda/urbanguard-api-{environment}`
- Retention: 30 days
- Contains: Application logs, errors, request processing

**API Gateway Logs:**
- Log Group: `/aws/apigateway/urbanguard-api-{environment}`
- Retention: 30 days
- Contains: Request/response logs, latency, status codes

**View logs:**
```bash
# Lambda logs
sam logs --stack-name urbanguard-ai-system --tail

# Or use AWS CLI
aws logs tail /aws/lambda/urbanguard-api-dev --follow
```

### CloudWatch Metrics

Monitor these key metrics in CloudWatch:

**Lambda Metrics:**
- Invocations
- Duration (cold start vs warm)
- Errors
- Throttles
- Concurrent executions

**API Gateway Metrics:**
- Count (total requests)
- 4XXError (client errors)
- 5XXError (server errors)
- Latency
- IntegrationLatency

**DynamoDB Metrics:**
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- UserErrors
- SystemErrors

## Cost Estimation

### AWS Free Tier (First 12 months)

**Lambda:**
- 1M requests/month free
- 400,000 GB-seconds compute time free

**DynamoDB:**
- 25 GB storage free
- 25 read capacity units free
- 25 write capacity units free

**API Gateway:**
- 1M API calls/month free (first 12 months)

### Beyond Free Tier

**Lambda:**
- $0.20 per 1M requests
- $0.0000166667 per GB-second

**DynamoDB (On-Demand):**
- $1.25 per million write requests
- $0.25 per million read requests
- $0.25 per GB-month storage

**API Gateway:**
- $3.50 per million requests

**Estimated Monthly Cost (Low Traffic):**
- 10,000 API calls/month: ~$0.50
- 1,000 complaints/month: ~$1.00
- Total: **~$1.50/month**

**Estimated Monthly Cost (Medium Traffic):**
- 100,000 API calls/month: ~$5.00
- 10,000 complaints/month: ~$3.00
- Total: **~$8.00/month**

## Troubleshooting

### Issue: Deployment fails with "Unable to upload artifact"

**Solution:** Ensure you have S3 permissions and run:
```bash
sam deploy --guided --resolve-s3
```

### Issue: Lambda function timeout

**Solution:** Increase timeout in template.yaml:
```yaml
Globals:
  Function:
    Timeout: 60  # Increase from 30 to 60 seconds
```

### Issue: DynamoDB access denied

**Solution:** Verify IAM policies in template.yaml include all required tables.

### Issue: CORS errors from frontend

**Solution:** Update CORS configuration in template.yaml:
```yaml
Cors:
  AllowOrigin: "'https://your-frontend-domain.com'"
```

### Issue: Cold start timeout

**Solution:** 
1. Increase Lambda memory (improves CPU allocation):
```yaml
Globals:
  Function:
    MemorySize: 1024  # Increase from 512 to 1024 MB
```

2. Enable provisioned concurrency (costs extra):
```yaml
ProvisionedConcurrencyConfig:
  ProvisionedConcurrentExecutions: 1
```

### Issue: OpenWeatherMap API errors

**Solution:** Verify API key is correct and has not exceeded rate limits.

## Updating the Deployment

### Update Code Only

```bash
sam build
sam deploy
```

### Update Infrastructure

Modify `template.yaml`, then:
```bash
sam build
sam deploy
```

SAM will show a changeset before applying updates.

### Rollback Deployment

```bash
aws cloudformation rollback-stack --stack-name urbanguard-ai-system
```

## Deleting the Stack

To remove all AWS resources:

```bash
sam delete --stack-name urbanguard-ai-system
```

**Warning:** This will delete:
- Lambda function
- API Gateway
- All DynamoDB tables and data
- CloudWatch log groups
- IAM roles

## Local Testing

### Test Lambda Function Locally

```bash
# Start local API
sam local start-api

# API will be available at http://127.0.0.1:3000
curl http://127.0.0.1:3000/health
```

### Invoke Function Directly

```bash
# Create test event
echo '{"httpMethod":"GET","path":"/health"}' > event.json

# Invoke function
sam local invoke UrbanGuardApiFunction -e event.json
```

### Test with DynamoDB Local

```bash
# Start DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Set environment variable
export AWS_SAM_LOCAL=true

# Start local API
sam local start-api --env-vars env.json
```

Create `env.json`:
```json
{
  "UrbanGuardApiFunction": {
    "DYNAMODB_ENDPOINT": "http://host.docker.internal:8000"
  }
}
```

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: aws-actions/setup-sam@v2
      
      - uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and Deploy
        run: |
          cd backend
          sam build
          sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
            --parameter-overrides "OpenWeatherMapApiKey=${{ secrets.OPENWEATHERMAP_API_KEY }}"
```

## Security Best Practices

1. **API Key Management:**
   - Store OpenWeatherMap API key in AWS Secrets Manager
   - Reference in template using `{{resolve:secretsmanager:secret-name}}`

2. **API Gateway:**
   - Enable API key requirement for production
   - Implement rate limiting
   - Use AWS WAF for DDoS protection

3. **DynamoDB:**
   - Enable point-in-time recovery (already enabled in template)
   - Enable encryption at rest (enabled by default)
   - Implement backup strategy

4. **Lambda:**
   - Use least-privilege IAM policies
   - Enable X-Ray tracing for debugging
   - Implement input validation

5. **Monitoring:**
   - Set up CloudWatch alarms for errors
   - Monitor Lambda duration and throttles
   - Track DynamoDB capacity usage

## Next Steps

After successful deployment:

1. **Configure Frontend:**
   - Update frontend API URL to point to deployed API Gateway endpoint
   - Update CORS settings if needed

2. **Initialize Data:**
   - Submit test complaints via API
   - Verify DynamoDB tables are populated
   - Check CloudWatch logs for errors

3. **Set Up Monitoring:**
   - Create CloudWatch dashboards
   - Configure alarms for critical metrics
   - Set up SNS notifications

4. **Performance Testing:**
   - Load test with expected traffic
   - Verify response times meet requirements
   - Optimize Lambda memory/timeout if needed

## References

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)

## Support

For issues or questions:
1. Check CloudWatch logs for error details
2. Review AWS SAM CLI documentation
3. Verify IAM permissions
4. Check AWS service quotas and limits
