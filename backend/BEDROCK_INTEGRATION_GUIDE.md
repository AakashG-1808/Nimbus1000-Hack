# Amazon Bedrock Integration Guide

## Quick Start

### 1. Configure AWS Credentials

Create a `.env` file in the `backend` directory:

```bash
# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
BEDROCK_MODEL_ID=anthropic.claude-v2
```

### 2. Verify IAM Permissions

Ensure your AWS IAM user/role has the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/*"
    }
  ]
}
```

### 3. Test the Integration

Run the demo script:

```bash
cd backend
python demo_bedrock_integration.py
```

## Usage

### Basic Classification

```python
from ai_classifier import AIClassifier

# Initialize classifier
classifier = AIClassifier()

# Classify a complaint
category, confidence = classifier.classify_complaint(
    description="There is a large pothole on the main road",
    location="Koramangala"
)

print(f"Category: {category}")
print(f"Confidence: {confidence}")
```

### Check Circuit Breaker State

```python
# Check if Bedrock is available
if classifier.circuit_breaker.state == "OPEN":
    print("Bedrock is currently unavailable, using fallback")
else:
    print("Bedrock is available")
```

### Monitor Classification Source

The classifier automatically logs whether it used Bedrock or fallback:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Will log: "Bedrock classified as 'pothole' with confidence 0.95"
# Or: "Using keyword-based fallback classification"
category, confidence = classifier.classify_complaint(description, location)
```

## Supported Models

### Anthropic Claude (Recommended)
- `anthropic.claude-v2`
- `anthropic.claude-v2:1`
- `anthropic.claude-instant-v1`

### Other Models
The integration supports other Bedrock models with generic prompt format. Update `BEDROCK_MODEL_ID` in `.env`.

## Configuration Options

### Circuit Breaker Settings

Modify in `ai_classifier.py`:

```python
self.circuit_breaker = CircuitBreaker(
    failure_threshold=5,    # Open after 5 failures
    timeout_seconds=60      # Wait 60s before retry
)
```

### Timeout Settings

Modify in `ai_classifier.py`:

```python
self.bedrock_timeout = 3  # API timeout in seconds
```

## Fallback Behavior

The system automatically falls back to keyword classification when:

1. **AWS credentials not configured**: Uses keyword classification only
2. **Bedrock API timeout**: After 3 seconds, falls back
3. **Bedrock API error**: Any client error triggers fallback
4. **Invalid response**: Parsing errors trigger fallback
5. **Circuit breaker open**: Fails fast to fallback

### Fallback Categories

Keyword classification uses these keywords:

- **pothole**: pothole, road damage, crater, hole in road, broken road
- **flooding**: flood, water logging, waterlogged, drainage, overflow, rain water
- **traffic**: traffic, congestion, jam, signal, accident, vehicle
- **garbage**: garbage, waste, trash, litter, dump, dirty, smell
- **streetlight**: streetlight, street light, lamp, lighting, dark, bulb
- **water_supply**: water supply, no water, water shortage, tap, pipeline, leak
- **noise**: noise, loud, sound, disturbance, pollution
- **construction**: construction, building, debris, dust, excavation, work

## Monitoring

### Log Levels

- **INFO**: Normal operations, successful classifications
- **WARNING**: Fallback activations, circuit breaker state changes
- **ERROR**: API errors, failures

### Key Metrics to Monitor

1. **Circuit Breaker State**: Track OPEN/CLOSED transitions
2. **Fallback Rate**: Percentage of classifications using fallback
3. **Confidence Scores**: Average confidence from Bedrock vs fallback
4. **Response Times**: Track classification latency

### Example Monitoring Code

```python
import logging
from collections import defaultdict

# Track metrics
metrics = defaultdict(int)

# Custom handler to track fallback usage
class MetricsHandler(logging.Handler):
    def emit(self, record):
        if "fallback" in record.getMessage().lower():
            metrics['fallback_count'] += 1
        if "bedrock classified" in record.getMessage().lower():
            metrics['bedrock_count'] += 1

# Add handler
logger = logging.getLogger('ai_classifier')
logger.addHandler(MetricsHandler())

# After classifications
print(f"Bedrock: {metrics['bedrock_count']}")
print(f"Fallback: {metrics['fallback_count']}")
```

## Troubleshooting

### Issue: "Unable to locate credentials"

**Solution**: Configure AWS credentials in `.env` or use IAM roles

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Option 2: AWS CLI configuration
aws configure

# Option 3: IAM role (for Lambda/EC2)
# No configuration needed, automatic
```

### Issue: "Circuit breaker is OPEN"

**Solution**: Wait 60 seconds for automatic recovery, or check AWS service status

```python
# Check circuit breaker state
print(f"State: {classifier.circuit_breaker.state}")
print(f"Failures: {classifier.circuit_breaker.failure_count}")

# Force reset (not recommended in production)
classifier.circuit_breaker.state = "CLOSED"
classifier.circuit_breaker.failure_count = 0
```

### Issue: Low confidence scores

**Solution**: Tune the classification prompt or use a different model

```python
# Check which classification method was used
# Bedrock typically gives 0.85-0.99 confidence
# Keyword fallback gives 0.3-0.9 confidence

if confidence < 0.5:
    print("Low confidence, may need manual review")
```

### Issue: Timeout errors

**Solution**: Increase timeout or check network connectivity

```python
# Increase timeout (in ai_classifier.py)
self.bedrock_timeout = 5  # Increase to 5 seconds
```

## Performance Optimization

### 1. Caching

Implement caching for repeated complaints:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_classify(description_hash, location):
    return classifier.classify_complaint(description, location)
```

### 2. Batch Processing

For bulk classification, process in batches:

```python
def classify_batch(complaints):
    results = []
    for complaint in complaints:
        category, confidence = classifier.classify_complaint(
            complaint['description'],
            complaint['location']
        )
        results.append((category, confidence))
    return results
```

### 3. Async Processing

For high-throughput scenarios, use async:

```python
import asyncio

async def classify_async(description, location):
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        classifier.classify_complaint,
        description,
        location
    )
```

## Testing

### Run All Tests

```bash
cd backend
python -m pytest test_bedrock_integration.py -v
```

### Run Specific Test

```bash
python -m pytest test_bedrock_integration.py::TestBedrockIntegration::test_bedrock_classification_success -v
```

### Run with Coverage

```bash
python -m pytest test_bedrock_integration.py --cov=ai_classifier --cov-report=html
```

## Production Deployment

### AWS Lambda

```python
import os
from ai_classifier import AIClassifier

# Initialize once (outside handler)
classifier = AIClassifier()

def lambda_handler(event, context):
    description = event['description']
    location = event['location']
    
    category, confidence = classifier.classify_complaint(
        description,
        location
    )
    
    return {
        'statusCode': 200,
        'body': {
            'category': category,
            'confidence': confidence,
            'circuit_breaker_state': classifier.circuit_breaker.state
        }
    }
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Use IAM role for credentials (recommended)
# Or pass via environment variables
ENV AWS_REGION=us-east-1

CMD ["python", "main.py"]
```

### Environment Variables

```bash
# Required
AWS_REGION=us-east-1

# Optional (use IAM role instead)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Model configuration
BEDROCK_MODEL_ID=anthropic.claude-v2

# Application settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Cost Considerations

### Bedrock Pricing

- Anthropic Claude v2: ~$0.01 per 1K input tokens, ~$0.03 per 1K output tokens
- Average complaint classification: ~100 input tokens, ~10 output tokens
- Estimated cost: ~$0.001 per classification

### Cost Optimization

1. **Circuit Breaker**: Prevents wasted API calls during outages
2. **Fallback**: Free keyword classification as backup
3. **Caching**: Reduce duplicate API calls
4. **Batch Processing**: Optimize for throughput

### Monthly Cost Estimate

```
Assumptions:
- 10,000 complaints/day
- 300,000 complaints/month
- $0.001 per classification

Monthly cost: 300,000 × $0.001 = $300
```

## Support

For issues or questions:
1. Check logs for error messages
2. Verify AWS credentials and permissions
3. Test with demo script: `python demo_bedrock_integration.py`
4. Review circuit breaker state
5. Check AWS Bedrock service status

## References

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Anthropic Claude Models](https://docs.anthropic.com/claude/docs)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
