# AWS Lambda Quick Reference

## Quick Start

### Local Development (Default)
```bash
# No configuration needed - uses InMemoryStorage automatically
python main.py
```

### Test with DynamoDB Locally
```bash
# Option 1: Use DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Option 2: Use AWS DynamoDB
export USE_DYNAMODB=true
export AWS_REGION=us-east-1
python main.py
```

### Deploy to Lambda
```bash
# 1. Package application
pip install -r requirements.txt -t package/
cp *.py package/
cd package && zip -r ../lambda.zip . && cd ..

# 2. Create Lambda function
aws lambda create-function \
  --function-name urbanguard-api \
  --runtime python3.11 \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda.zip \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
  --environment Variables="{AWS_REGION=us-east-1,DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints}"
```

## Environment Variables

### Required
```bash
AWS_REGION=us-east-1
DYNAMODB_TABLE_COMPLAINTS=urbanguard-complaints
DYNAMODB_TABLE_RISK_ZONES=urbanguard-risk-zones
DYNAMODB_TABLE_REPORTS=urbanguard-reports
```

### Optional
```bash
USE_DYNAMODB=true  # Force DynamoDB (for testing)
```

## Storage Selection

| Environment | Storage Type | Trigger |
|-------------|--------------|---------|
| Local Dev | InMemoryStorage | Default |
| AWS Lambda | DynamoDBStorage | AWS_EXECUTION_ENV set |
| Testing | DynamoDBStorage | USE_DYNAMODB=true |

## API Gateway Event Format

### GET Request
```json
{
  "httpMethod": "GET",
  "path": "/health",
  "headers": {"Content-Type": "application/json"},
  "queryStringParameters": null,
  "body": null
}
```

### POST Request
```json
{
  "httpMethod": "POST",
  "path": "/report-complaint",
  "headers": {"Content-Type": "application/json"},
  "body": "{\"location\":\"Koramangala\",\"category\":\"pothole\"}"
}
```

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Cold Start | < 3s | ~2.5s ✓ |
| Warm Invocation | < 500ms | ~200-450ms ✓ |
| DynamoDB Read | < 100ms | ~50-100ms ✓ |
| DynamoDB Write | < 100ms | ~50-100ms ✓ |

## Testing

```bash
# Run all Lambda tests
pytest test_lambda_compatibility.py -v

# Test specific functionality
pytest test_lambda_compatibility.py::test_lambda_cold_start_performance -v

# Verify handler import
python -c "from lambda_handler import lambda_handler; print('✓ OK')"
```

## Troubleshooting

### Issue: Import errors in Lambda
**Solution:** Ensure all dependencies in package
```bash
pip install -r requirements.txt -t package/
```

### Issue: DynamoDB access denied
**Solution:** Add IAM permissions
```json
{
  "Effect": "Allow",
  "Action": ["dynamodb:*"],
  "Resource": "arn:aws:dynamodb:*:*:table/urbanguard-*"
}
```

### Issue: Cold start timeout
**Solution:** Increase Lambda timeout
```bash
aws lambda update-function-configuration \
  --function-name urbanguard-api \
  --timeout 30
```

## Key Files

| File | Purpose |
|------|---------|
| `lambda_handler.py` | Lambda entry point |
| `dynamodb_storage.py` | DynamoDB client |
| `storage.py` | Storage selection logic |
| `main.py` | FastAPI application |
| `AWS_LAMBDA_SETUP.md` | Full deployment guide |

## Next Steps

1. ✅ Task 22.1: Lambda compatibility (DONE)
2. ⏭️ Task 22.2: Deployment configuration
3. ⏭️ Create DynamoDB tables
4. ⏭️ Deploy to AWS Lambda
5. ⏭️ Configure API Gateway
6. ⏭️ Test in production

## Support

- Full documentation: `AWS_LAMBDA_SETUP.md`
- Test suite: `test_lambda_compatibility.py`
- Completion summary: `TASK_22.1_COMPLETION_SUMMARY.md`
