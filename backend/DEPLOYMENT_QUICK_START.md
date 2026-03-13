# UrbanGuard AI - Quick Deployment Guide

## Prerequisites Checklist

- [ ] AWS SAM CLI installed (`sam --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] OpenWeatherMap API key obtained
- [ ] In `backend/` directory

## One-Command Deployment

### First Time (Development)

```bash
# Build and deploy with guided setup
sam build && sam deploy --guided
```

**Prompts:**
- Stack Name: `urbanguard-ai-system`
- Region: `us-east-1`
- OpenWeatherMapApiKey: `YOUR_API_KEY`
- Environment: `dev`
- Confirm changes: `Y`
- Allow IAM role creation: `Y`
- Save config: `Y`

### Subsequent Deployments

```bash
# Build and deploy using saved config
sam build && sam deploy
```

### Production Deployment

```bash
sam build && sam deploy --config-env prod \
  --parameter-overrides "OpenWeatherMapApiKey=YOUR_API_KEY"
```

## Quick Commands

### Build
```bash
sam build
```

### Deploy
```bash
sam deploy                    # Use saved config
sam deploy --guided           # Interactive setup
sam deploy --config-env prod  # Deploy to production
```

### Test Locally
```bash
sam local start-api           # Start local API on port 3000
sam local invoke              # Invoke function directly
```

### View Logs
```bash
sam logs --tail               # Tail logs in real-time
sam logs --stack-name urbanguard-ai-system
```

### Delete Stack
```bash
sam delete --stack-name urbanguard-ai-system
```

## Verify Deployment

```bash
# Get API URL from outputs
aws cloudformation describe-stacks \
  --stack-name urbanguard-ai-system \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text

# Test health endpoint
curl $(aws cloudformation describe-stacks \
  --stack-name urbanguard-ai-system \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)/health
```

## Common Issues

### Build fails
```bash
# Clean and rebuild
rm -rf .aws-sam
sam build
```

### Deployment fails
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name urbanguard-ai-system \
  --max-items 10
```

### Lambda timeout
Edit `template.yaml`:
```yaml
Globals:
  Function:
    Timeout: 60  # Increase timeout
```

### CORS errors
Edit `template.yaml`:
```yaml
Cors:
  AllowOrigin: "'*'"  # Allow all origins (dev only)
```

## Environment Variables

Set in `template.yaml` under `Globals.Function.Environment.Variables`:

- `AWS_REGION`: Auto-set by CloudFormation
- `DYNAMODB_TABLE_COMPLAINTS`: Auto-set by CloudFormation
- `DYNAMODB_TABLE_RISK_ZONES`: Auto-set by CloudFormation
- `DYNAMODB_TABLE_REPORTS`: Auto-set by CloudFormation
- `OPENWEATHERMAP_API_KEY`: Set via parameter
- `AWS_BEDROCK_REGION`: Auto-set by CloudFormation

## Resources Created

- **Lambda Function**: `urbanguard-api-{env}`
- **API Gateway**: `urbanguard-api-{env}`
- **DynamoDB Tables**:
  - `urbanguard-complaints-{env}`
  - `urbanguard-risk-zones-{env}`
  - `urbanguard-reports-{env}`
- **CloudWatch Log Groups**:
  - `/aws/lambda/urbanguard-api-{env}`
  - `/aws/apigateway/urbanguard-api-{env}`

## Cost Estimate

**Free Tier (First 12 months):**
- Lambda: 1M requests/month free
- DynamoDB: 25 GB storage free
- API Gateway: 1M calls/month free

**Beyond Free Tier:**
- ~$1.50/month for low traffic (10K requests)
- ~$8.00/month for medium traffic (100K requests)

## Next Steps

1. Get API URL from CloudFormation outputs
2. Update frontend to use deployed API URL
3. Test all endpoints
4. Monitor CloudWatch logs
5. Set up CloudWatch alarms

## Full Documentation

See `DEPLOYMENT_GUIDE.md` for complete documentation.
