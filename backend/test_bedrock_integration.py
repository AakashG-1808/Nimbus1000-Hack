"""
Unit tests for Amazon Bedrock integration with circuit breaker and fallback
Task 3.2: Implement Amazon Bedrock integration with fallback
"""
import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, ReadTimeoutError
from ai_classifier import AIClassifier, CircuitBreaker
from constants import COMPLAINT_CATEGORIES


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation"""
    
    def test_circuit_breaker_starts_closed(self):
        """Test that circuit breaker starts in CLOSED state"""
        cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    def test_circuit_breaker_opens_after_threshold_failures(self):
        """Test that circuit breaker opens after reaching failure threshold"""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.state == "OPEN"
        assert cb.failure_count == 3
    
    def test_circuit_breaker_fails_fast_when_open(self):
        """Test that circuit breaker returns None immediately when open"""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.state == "OPEN"
        
        # Should fail fast without calling function
        result = cb.call(failing_func)
        assert result is None
    
    def test_circuit_breaker_resets_failure_count_on_success(self):
        """Test that circuit breaker resets failure count on successful call"""
        cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        def failing_func():
            raise Exception("Test failure")
        
        def success_func():
            return "success"
        
        # Trigger some failures
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.failure_count == 2
        
        # Successful call should reset
        result = cb.call(success_func)
        assert result == "success"
        assert cb.failure_count == 0
    
    def test_circuit_breaker_closes_after_successes_in_half_open(self):
        """Test that circuit breaker closes after 3 successes in HALF_OPEN state"""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=0)  # 0 timeout for immediate half-open
        
        def failing_func():
            raise Exception("Test failure")
        
        def success_func():
            return "success"
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.state == "OPEN"
        
        # Should transition to HALF_OPEN and then CLOSED after 3 successes
        for i in range(3):
            result = cb.call(success_func)
            assert result == "success"
        
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0


class TestBedrockIntegration:
    """Test Amazon Bedrock integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock environment variables
        os.environ["AWS_REGION"] = "us-east-1"
        os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-v2"
    
    def test_bedrock_client_initialization(self):
        """Test that Bedrock client initializes with correct configuration"""
        with patch('boto3.client') as mock_boto3:
            classifier = AIClassifier()
            
            # Verify boto3.client was called
            mock_boto3.assert_called_once()
            call_kwargs = mock_boto3.call_args[1]
            
            assert call_kwargs['service_name'] == 'bedrock-runtime'
            assert call_kwargs['config'].region_name == 'us-east-1'
    
    def test_bedrock_classification_success(self):
        """Test successful Bedrock classification"""
        with patch('boto3.client') as mock_boto3:
            # Mock Bedrock response
            mock_client = MagicMock()
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'completion': 'pothole,0.95'
            }).encode()
            mock_client.invoke_model.return_value = mock_response
            mock_boto3.return_value = mock_client
            
            classifier = AIClassifier()
            category, confidence = classifier.classify_complaint(
                "There is a large pothole on the road",
                "Koramangala"
            )
            
            assert category == "pothole"
            assert confidence == 0.95
    
    def test_bedrock_timeout_falls_back_to_keyword(self):
        """Test that Bedrock timeout triggers fallback to keyword classification"""
        with patch('boto3.client') as mock_boto3:
            # Mock Bedrock timeout
            mock_client = MagicMock()
            mock_client.invoke_model.side_effect = ReadTimeoutError(
                endpoint_url="test",
                operation_name="InvokeModel"
            )
            mock_boto3.return_value = mock_client
            
            classifier = AIClassifier()
            category, confidence = classifier.classify_complaint(
                "There is a large pothole on the road",
                "Koramangala"
            )
            
            # Should fall back to keyword classification
            assert category == "pothole"
            assert 0.0 <= confidence <= 1.0
    
    def test_bedrock_client_error_falls_back_to_keyword(self):
        """Test that Bedrock client error triggers fallback to keyword classification"""
        with patch('boto3.client') as mock_boto3:
            # Mock Bedrock client error
            mock_client = MagicMock()
            mock_client.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
                'InvokeModel'
            )
            mock_boto3.return_value = mock_client
            
            classifier = AIClassifier()
            category, confidence = classifier.classify_complaint(
                "Flooding in the street after heavy rain",
                "Indiranagar"
            )
            
            # Should fall back to keyword classification
            assert category == "flooding"
            assert 0.0 <= confidence <= 1.0
    
    def test_bedrock_invalid_response_falls_back_to_keyword(self):
        """Test that invalid Bedrock response triggers fallback"""
        with patch('boto3.client') as mock_boto3:
            # Mock invalid Bedrock response
            mock_client = MagicMock()
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'completion': 'invalid_category,0.95'
            }).encode()
            mock_client.invoke_model.return_value = mock_response
            mock_boto3.return_value = mock_client
            
            classifier = AIClassifier()
            category, confidence = classifier.classify_complaint(
                "Traffic jam at the signal",
                "Whitefield"
            )
            
            # Should fall back to keyword classification
            assert category == "traffic"
            assert 0.0 <= confidence <= 1.0
    
    def test_bedrock_classification_prompt_includes_categories(self):
        """Test that classification prompt includes all 8 categories"""
        with patch('boto3.client') as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.return_value = mock_client
            
            classifier = AIClassifier()
            prompt = classifier._create_classification_prompt(
                "Test description",
                "Koramangala"
            )
            
            # Verify all categories are in prompt
            for category in COMPLAINT_CATEGORIES:
                assert category in prompt
            
            # Verify location and description are in prompt
            assert "Koramangala" in prompt
            assert "Test description" in prompt
    
    def test_bedrock_response_parsing_with_confidence(self):
        """Test parsing Bedrock response with category and confidence"""
        classifier = AIClassifier()
        
        # Test valid response
        category, confidence = classifier._parse_bedrock_response("pothole,0.95")
        assert category == "pothole"
        assert confidence == 0.95
        
        # Test response with spaces
        category, confidence = classifier._parse_bedrock_response(" flooding , 0.87 ")
        assert category == "flooding"
        assert confidence == 0.87
    
    def test_bedrock_response_parsing_without_confidence(self):
        """Test parsing Bedrock response with only category"""
        classifier = AIClassifier()
        
        category, confidence = classifier._parse_bedrock_response("traffic")
        assert category == "traffic"
        assert confidence == 0.85  # Default confidence
    
    def test_bedrock_response_parsing_with_invalid_confidence(self):
        """Test parsing Bedrock response with invalid confidence value"""
        classifier = AIClassifier()
        
        category, confidence = classifier._parse_bedrock_response("garbage,invalid")
        assert category == "garbage"
        assert confidence == 0.85  # Default confidence
    
    def test_bedrock_response_confidence_bounds(self):
        """Test that confidence is bounded between 0.0 and 1.0"""
        classifier = AIClassifier()
        
        # Test confidence > 1.0
        category, confidence = classifier._parse_bedrock_response("pothole,1.5")
        assert confidence == 1.0
        
        # Test confidence < 0.0
        category, confidence = classifier._parse_bedrock_response("flooding,-0.5")
        assert confidence == 0.0
    
    def test_circuit_breaker_integration_with_bedrock(self):
        """Test that circuit breaker protects Bedrock calls"""
        with patch('boto3.client') as mock_boto3:
            # Mock Bedrock to fail repeatedly
            mock_client = MagicMock()
            mock_client.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
                'InvokeModel'
            )
            mock_boto3.return_value = mock_client
            
            classifier = AIClassifier()
            
            # Trigger failures to open circuit
            for i in range(5):
                category, confidence = classifier.classify_complaint(
                    "Test complaint",
                    "Koramangala"
                )
                # Should fall back to keyword classification
                assert category in COMPLAINT_CATEGORIES
            
            # Circuit should be open now
            assert classifier.circuit_breaker.state == "OPEN"
            
            # Next call should fail fast without calling Bedrock
            category, confidence = classifier.classify_complaint(
                "Another test complaint",
                "Koramangala"
            )
            assert category in COMPLAINT_CATEGORIES
    
    def test_bedrock_timeout_is_3_seconds(self):
        """Test that Bedrock timeout is configured to 3 seconds"""
        with patch('boto3.client') as mock_boto3:
            classifier = AIClassifier()
            
            assert classifier.bedrock_timeout == 3
            
            # Verify timeout was passed to boto3 config
            call_kwargs = mock_boto3.call_args[1]
            assert call_kwargs['config'].read_timeout == 3
    
    def test_bedrock_no_automatic_retries(self):
        """Test that Bedrock client has no automatic retries"""
        with patch('boto3.client') as mock_boto3:
            classifier = AIClassifier()
            
            # Verify retries are disabled
            call_kwargs = mock_boto3.call_args[1]
            assert call_kwargs['config'].retries['max_attempts'] == 0
    
    def test_classification_always_returns_valid_category(self):
        """Test that classification always returns a valid category"""
        with patch('boto3.client') as mock_boto3:
            # Mock various failure scenarios
            mock_client = MagicMock()
            mock_client.invoke_model.side_effect = Exception("Random error")
            mock_boto3.return_value = mock_client
            
            classifier = AIClassifier()
            
            test_descriptions = [
                "pothole on road",
                "flooding in street",
                "traffic jam",
                "garbage dump",
                "streetlight not working",
                "no water supply",
                "loud noise",
                "construction work",
            ]
            
            for description in test_descriptions:
                category, confidence = classifier.classify_complaint(
                    description,
                    "Koramangala"
                )
                assert category in COMPLAINT_CATEGORIES
                assert 0.0 <= confidence <= 1.0
    
    def test_bedrock_initialization_failure_uses_keyword_only(self):
        """Test that failed Bedrock initialization falls back to keyword classification"""
        with patch('boto3.client') as mock_boto3:
            # Mock boto3 initialization failure
            mock_boto3.side_effect = Exception("AWS credentials not found")
            
            classifier = AIClassifier()
            
            # Should still work with keyword classification
            category, confidence = classifier.classify_complaint(
                "There is a pothole on the road",
                "Koramangala"
            )
            
            assert category == "pothole"
            assert 0.0 <= confidence <= 1.0
            assert classifier.bedrock_client is None


class TestBedrockFallbackBehavior:
    """Test fallback behavior from Bedrock to keyword classification"""
    
    def test_fallback_maintains_classification_accuracy(self):
        """Test that fallback classification is still accurate"""
        with patch('boto3.client') as mock_boto3:
            # Mock Bedrock unavailable
            mock_boto3.side_effect = Exception("Service unavailable")
            
            classifier = AIClassifier()
            
            test_cases = [
                ("Large pothole on main road", "pothole"),
                ("Flooding after heavy rain", "flooding"),
                ("Traffic jam at signal", "traffic"),
                ("Garbage dump with bad smell", "garbage"),
                ("Street light not working", "streetlight"),
                ("No water supply from tap", "water_supply"),
                ("Loud noise disturbance", "noise"),
                ("Construction debris everywhere", "construction"),
            ]
            
            for description, expected_category in test_cases:
                category, confidence = classifier.classify_complaint(
                    description,
                    "Koramangala"
                )
                assert category == expected_category
    
    def test_fallback_returns_single_category(self):
        """Test that fallback always returns exactly one category"""
        with patch('boto3.client') as mock_boto3:
            mock_boto3.side_effect = Exception("Service unavailable")
            
            classifier = AIClassifier()
            
            category, confidence = classifier.classify_complaint(
                "Multiple issues: pothole, flooding, and traffic",
                "Koramangala"
            )
            
            assert category in COMPLAINT_CATEGORIES
            assert isinstance(category, str)
    
    def test_fallback_performance_under_3_seconds(self):
        """Test that fallback classification completes quickly"""
        import time
        
        with patch('boto3.client') as mock_boto3:
            mock_boto3.side_effect = Exception("Service unavailable")
            
            classifier = AIClassifier()
            
            start_time = time.time()
            category, confidence = classifier.classify_complaint(
                "Test complaint description",
                "Koramangala"
            )
            elapsed_time = time.time() - start_time
            
            assert elapsed_time < 3.0  # Should be much faster than 3 seconds
            assert category in COMPLAINT_CATEGORIES
