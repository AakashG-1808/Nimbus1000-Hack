"""
UrbanGuard AI System - AWS Lambda Handler
Lambda handler wrapper for FastAPI using Mangum adapter
"""
import os
from mangum import Mangum
from main import app


# Create Lambda handler using Mangum adapter
# Mangum wraps the FastAPI application to make it compatible with AWS Lambda
handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    """
    AWS Lambda handler function for FastAPI application.
    
    This function is invoked by AWS Lambda when requests come through API Gateway.
    The Mangum adapter translates API Gateway events to ASGI format for FastAPI.
    
    Args:
        event: API Gateway event containing HTTP request data
        context: Lambda context object with runtime information
        
    Returns:
        API Gateway response format with statusCode, headers, and body
        
    Environment Variables:
        AWS_EXECUTION_ENV: Set by Lambda runtime (e.g., "AWS_Lambda_python3.11")
        DYNAMODB_TABLE_COMPLAINTS: DynamoDB table name for complaints
        DYNAMODB_TABLE_RISK_ZONES: DynamoDB table name for risk zones
        DYNAMODB_TABLE_REPORTS: DynamoDB table name for daily reports
        AWS_REGION: AWS region for DynamoDB client
        
    Performance:
        Cold start: < 3 seconds (Requirement 19.5)
        Warm invocation: < 500ms
    """
    return handler(event, context)
