"""
Test AWS Lambda compatibility and cold start performance
Task 22.1 - Configure AWS Lambda compatibility
"""
import os
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


def test_storage_selection_local_environment():
    """
    Test that InMemoryStorage is used in local development environment.
    
    Validates: Requirement 19.4 (in-memory fallback for local dev)
    """
    # Clear environment variables
    os.environ.pop("AWS_EXECUTION_ENV", None)
    os.environ.pop("USE_DYNAMODB", None)
    
    # Import storage module (will create new instance)
    import importlib
    import storage as storage_module
    importlib.reload(storage_module)
    
    # Verify InMemoryStorage is used
    from storage import storage, InMemoryStorage
    assert isinstance(storage, InMemoryStorage), \
        "Expected InMemoryStorage for local development"


def test_storage_selection_lambda_environment():
    """
    Test that DynamoDBStorage is used in AWS Lambda environment.
    
    Validates: Requirement 19.3 (DynamoDB storage in Lambda)
    """
    # Set Lambda environment variable
    os.environ["AWS_EXECUTION_ENV"] = "AWS_Lambda_python3.11"
    
    # Mock boto3 to avoid actual AWS calls
    with patch('boto3.resource') as mock_boto3:
        mock_dynamodb = MagicMock()
        mock_boto3.return_value = mock_dynamodb
        
        # Mock table objects
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Import storage module
        import importlib
        import storage as storage_module
        importlib.reload(storage_module)
        
        from storage import storage
        from dynamodb_storage import DynamoDBStorage
        
        # Verify DynamoDBStorage is used
        assert isinstance(storage, DynamoDBStorage), \
            "Expected DynamoDBStorage in Lambda environment"
    
    # Clean up
    os.environ.pop("AWS_EXECUTION_ENV", None)


def test_storage_selection_explicit_dynamodb_flag():
    """
    Test that DynamoDBStorage is used when USE_DYNAMODB flag is set.
    
    Validates: Requirement 19.4 (environment variable configuration)
    """
    # Set explicit DynamoDB flag
    os.environ["USE_DYNAMODB"] = "true"
    os.environ.pop("AWS_EXECUTION_ENV", None)
    
    # Mock boto3
    with patch('boto3.resource') as mock_boto3:
        mock_dynamodb = MagicMock()
        mock_boto3.return_value = mock_dynamodb
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Import storage module
        import importlib
        import storage as storage_module
        importlib.reload(storage_module)
        
        from storage import storage
        from dynamodb_storage import DynamoDBStorage
        
        # Verify DynamoDBStorage is used
        assert isinstance(storage, DynamoDBStorage), \
            "Expected DynamoDBStorage when USE_DYNAMODB=true"
    
    # Clean up
    os.environ.pop("USE_DYNAMODB", None)


def test_lambda_handler_exists():
    """
    Test that lambda_handler module exists and has required function.
    
    Validates: Requirement 19.1 (Lambda handler wrapper)
    """
    from lambda_handler import lambda_handler, handler
    
    # Verify handler function exists
    assert callable(lambda_handler), "lambda_handler must be callable"
    assert handler is not None, "Mangum handler must be initialized"


def test_lambda_handler_signature():
    """
    Test that lambda_handler has correct AWS Lambda signature.
    
    Validates: Requirement 19.1 (Lambda compatibility)
    """
    from lambda_handler import lambda_handler
    import inspect
    
    # Get function signature
    sig = inspect.signature(lambda_handler)
    params = list(sig.parameters.keys())
    
    # Verify Lambda signature (event, context)
    assert len(params) == 2, "lambda_handler must accept 2 parameters"
    assert params[0] == "event", "First parameter must be 'event'"
    assert params[1] == "context", "Second parameter must be 'context'"


@patch('lambda_handler.handler')
def test_lambda_handler_invocation(mock_handler):
    """
    Test that lambda_handler correctly invokes Mangum handler.
    
    Validates: Requirement 19.1 (Lambda handler wrapper)
    """
    from lambda_handler import lambda_handler
    
    # Mock event and context
    mock_event = {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {},
        "body": None
    }
    mock_context = Mock()
    mock_context.aws_request_id = "test-request-id"
    
    # Mock handler response
    mock_handler.return_value = {
        "statusCode": 200,
        "body": '{"status": "healthy"}'
    }
    
    # Invoke lambda_handler
    response = lambda_handler(mock_event, mock_context)
    
    # Verify handler was called with event and context
    mock_handler.assert_called_once_with(mock_event, mock_context)
    
    # Verify response
    assert response["statusCode"] == 200


def test_lambda_cold_start_performance():
    """
    Test Lambda cold start performance (< 3 seconds).
    
    This simulates a cold start by measuring import and initialization time.
    
    Validates: Requirement 19.5 (cold start < 3 seconds)
    """
    # Measure cold start time
    start_time = time.time()
    
    # Simulate cold start: import main application
    import importlib
    import sys
    
    # Remove modules to simulate fresh import
    modules_to_remove = [
        'main', 'lambda_handler', 'storage', 'dynamodb_storage',
        'complaint_processor', 'ai_classifier', 'weather_integrator',
        'traffic_analyzer', 'cluster_detector', 'risk_engine'
    ]
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
    
    # Import main application (simulates Lambda cold start)
    from lambda_handler import lambda_handler
    
    # Calculate cold start time
    cold_start_time = time.time() - start_time
    
    print(f"Cold start time: {cold_start_time:.3f} seconds")
    
    # Verify cold start is under 3 seconds
    assert cold_start_time < 3.0, \
        f"Cold start time {cold_start_time:.3f}s exceeds 3 second requirement"


def test_environment_variables_configuration():
    """
    Test that environment variables are correctly configured for AWS services.
    
    Validates: Requirement 19.4 (environment variable configuration)
    """
    # Set environment variables
    os.environ["AWS_REGION"] = "us-west-2"
    os.environ["DYNAMODB_TABLE_COMPLAINTS"] = "test-complaints"
    os.environ["DYNAMODB_TABLE_RISK_ZONES"] = "test-risk-zones"
    os.environ["DYNAMODB_TABLE_REPORTS"] = "test-reports"
    os.environ["USE_DYNAMODB"] = "true"
    
    # Mock boto3
    with patch('boto3.resource') as mock_boto3:
        mock_dynamodb = MagicMock()
        mock_boto3.return_value = mock_dynamodb
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Import DynamoDB storage
        from dynamodb_storage import DynamoDBStorage
        
        # Create storage instance
        storage = DynamoDBStorage()
        
        # Verify configuration
        assert storage.region == "us-west-2"
        assert storage.complaints_table_name == "test-complaints"
        assert storage.risk_zones_table_name == "test-risk-zones"
        assert storage.reports_table_name == "test-reports"
        
        # Verify boto3 was called with correct region
        mock_boto3.assert_called_with('dynamodb', region_name='us-west-2')
    
    # Clean up
    os.environ.pop("AWS_REGION", None)
    os.environ.pop("DYNAMODB_TABLE_COMPLAINTS", None)
    os.environ.pop("DYNAMODB_TABLE_RISK_ZONES", None)
    os.environ.pop("DYNAMODB_TABLE_REPORTS", None)
    os.environ.pop("USE_DYNAMODB", None)


def test_dynamodb_storage_complaint_operations():
    """
    Test DynamoDB storage complaint operations with mocked DynamoDB.
    
    Validates: Requirement 19.3 (DynamoDB integration)
    """
    from models import Complaint
    from datetime import datetime
    
    # Mock boto3
    with patch('boto3.resource') as mock_boto3:
        mock_dynamodb = MagicMock()
        mock_boto3.return_value = mock_dynamodb
        
        # Mock complaints table
        mock_complaints_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_complaints_table
        
        # Import DynamoDB storage
        from dynamodb_storage import DynamoDBStorage
        storage = DynamoDBStorage()
        
        # Create test complaint
        complaint = Complaint(
            location="Koramangala",
            category="pothole",
            description="Large pothole on main road",
            timestamp=datetime.now(),
            coordinates=(12.9352, 77.6245),
            complaint_id="test-123"
        )
        
        # Test add_complaint
        storage.add_complaint(complaint)
        
        # Verify put_item was called
        assert mock_complaints_table.put_item.called
        call_args = mock_complaints_table.put_item.call_args
        item = call_args[1]['Item']
        
        # Verify item structure
        assert item['complaint_id'] == "test-123"
        assert item['location'] == "Koramangala"
        assert item['category'] == "pothole"


def test_dynamodb_storage_fallback_on_error():
    """
    Test that DynamoDB storage handles errors gracefully.
    
    Validates: Requirement 20.3 (graceful error handling)
    """
    from botocore.exceptions import ClientError
    
    # Mock boto3
    with patch('boto3.resource') as mock_boto3:
        mock_dynamodb = MagicMock()
        mock_boto3.return_value = mock_dynamodb
        
        # Mock table that raises error
        mock_table = MagicMock()
        mock_table.scan.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'Scan'
        )
        mock_dynamodb.Table.return_value = mock_table
        
        # Import DynamoDB storage
        from dynamodb_storage import DynamoDBStorage
        storage = DynamoDBStorage()
        
        # Test get_all_complaints with error
        complaints = storage.get_all_complaints()
        
        # Verify graceful handling (returns empty list instead of crashing)
        assert complaints == []


def test_mangum_adapter_initialization():
    """
    Test that Mangum adapter is correctly initialized with FastAPI app.
    
    Validates: Requirement 19.1 (Lambda handler wrapper)
    """
    from lambda_handler import handler
    from mangum import Mangum
    
    # Verify handler is Mangum instance
    assert isinstance(handler, Mangum), "Handler must be Mangum instance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
