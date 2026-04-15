"""
Property-Based Tests for Error Handling
Tests for Task 12.3: Property tests for error handling and logging using Hypothesis

**Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5**

Properties tested:
- Property 46: Error Logging Completeness
- Property 47: External API Retry Behavior
- Property 48: Graceful Error Response After Retries
- Property 49: Request Logging Completeness
- Property 50: Error Response Format
"""
import pytest
import logging
import time
import json
from io import StringIO
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
from error_handling import (
    retry_with_exponential_backoff,
    ErrorResponse,
    RequestLogger,
    log_error,
    validate_required_fields,
    JSONFormatter
)


# ============================================================================
# Property Tests
# ============================================================================

class TestErrorHandlingProperties:
    """Property-based tests for error handling and logging"""
    
    # Feature: urbanguard-ai-system, Property 46: Error Logging Completeness
    @given(
        component=st.text(min_size=1, max_size=50),
        message=st.text(min_size=1, max_size=200),
        error_type=st.sampled_from(["ValueError", "TypeError", "RuntimeError"])
    )
    @settings(max_examples=100)
    def test_property_46_error_logging_completeness(
        self,
        component,
        message,
        error_type
    ):
        """
        Property 46: For any error that occurs in any component,
        the component should log the error with timestamp, component name,
        and error details.
        
        Validates: Requirement 20.1
        """
        # Create a string buffer to capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(JSONFormatter())
        
        # Set up logger
        logger = logging.getLogger(component)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        # Create an exception
        if error_type == "ValueError":
            error = ValueError(message)
        elif error_type == "TypeError":
            error = TypeError(message)
        else:
            error = RuntimeError(message)
        
        # Log the error
        log_error(component=component, message=message, error=error)
        
        # Get log output
        log_output = log_stream.getvalue()
        
        # Parse JSON log
        log_data = json.loads(log_output.strip())
        
        # Verify all required fields are present
        assert "timestamp" in log_data
        assert "level" in log_data
        assert "component" in log_data
        assert "message" in log_data
        assert "error_details" in log_data
        
        # Verify field values
        assert log_data["level"] == "ERROR"
        assert log_data["component"] == component
        assert message in log_data["message"]
        assert log_data["error_details"]["error_type"] == error_type
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(log_data["timestamp"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)
    
    # Feature: urbanguard-ai-system, Property 47: External API Retry Behavior
    @given(
        max_retries=st.integers(min_value=1, max_value=5),
        should_succeed_on_attempt=st.integers(min_value=1, max_value=6)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_47_external_api_retry_behavior(
        self,
        max_retries,
        should_succeed_on_attempt
    ):
        """
        Property 47: For any external API call that fails,
        the component should retry up to 3 times with exponential backoff.
        
        Validates: Requirement 20.2
        """
        attempt_count = [0]
        retry_delays = []
        
        @retry_with_exponential_backoff(
            max_retries=max_retries,
            initial_delay=0.01,  # Use small delay for testing
            backoff_factor=2.0
        )
        def failing_api_call():
            attempt_count[0] += 1
            
            if attempt_count[0] < should_succeed_on_attempt:
                raise Exception(f"API call failed (attempt {attempt_count[0]})")
            
            return "success"
        
        # Test behavior
        if should_succeed_on_attempt <= max_retries + 1:
            # Should eventually succeed
            result = failing_api_call()
            assert result == "success"
            assert attempt_count[0] == should_succeed_on_attempt
        else:
            # Should fail after all retries
            with pytest.raises(Exception):
                failing_api_call()
            
            # Should have attempted max_retries + 1 times (initial + retries)
            assert attempt_count[0] == max_retries + 1
    
    # Feature: urbanguard-ai-system, Property 47: Exponential backoff timing
    def test_property_47_exponential_backoff_timing(self):
        """
        Property 47 (extended): Retry delays should follow exponential backoff pattern.
        
        Validates: Requirement 20.2
        """
        retry_times = []
        
        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=2.0
        )
        def always_failing_call():
            retry_times.append(time.time())
            raise Exception("Always fails")
        
        # Execute and catch exception
        try:
            always_failing_call()
        except Exception:
            pass
        
        # Should have 4 attempts (initial + 3 retries)
        assert len(retry_times) == 4
        
        # Check delays between attempts (approximately exponential)
        for i in range(1, len(retry_times)):
            delay = retry_times[i] - retry_times[i-1]
            expected_delay = 0.1 * (2.0 ** (i-1))
            
            # Allow 50% tolerance for timing variations
            assert delay >= expected_delay * 0.5
            assert delay <= expected_delay * 2.0
    
    # Feature: urbanguard-ai-system, Property 48: Graceful Error Response After Retries
    @given(
        max_retries=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=3000)
    def test_property_48_graceful_error_response_after_retries(
        self,
        max_retries
    ):
        """
        Property 48: For any external API call, if all retries fail,
        the component should return a graceful error response to the user
        (not crash or hang).
        
        Validates: Requirement 20.3
        """
        @retry_with_exponential_backoff(
            max_retries=max_retries,
            initial_delay=0.01
        )
        def always_failing_call():
            raise Exception("API unavailable")
        
        # Should raise exception after retries (not hang or crash)
        with pytest.raises(Exception) as exc_info:
            always_failing_call()
        
        # Should have a descriptive error message
        assert "API unavailable" in str(exc_info.value)
    
    # Feature: urbanguard-ai-system, Property 49: Request Logging Completeness
    @given(
        method=st.sampled_from(["GET", "POST", "PUT", "DELETE"]),
        path=st.text(min_size=1, max_size=100).map(lambda s: "/" + s.replace(" ", "-")),
        response_time_ms=st.floats(min_value=0.1, max_value=5000.0),
        status_code=st.sampled_from([200, 201, 400, 404, 500])
    )
    @settings(max_examples=100)
    def test_property_49_request_logging_completeness(
        self,
        method,
        path,
        response_time_ms,
        status_code
    ):
        """
        Property 49: For any incoming request to the Dashboard_API,
        it should be logged with method, path, and response time.
        
        Validates: Requirement 20.4
        """
        # Create a string buffer to capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(JSONFormatter())
        
        # Set up logger
        logger = logging.getLogger("TestAPI")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Create request logger
        request_logger = RequestLogger(component="TestAPI")
        
        # Log request
        request_logger.log_request(
            method=method,
            path=path,
            response_time_ms=response_time_ms,
            status_code=status_code
        )
        
        # Get log output
        log_output = log_stream.getvalue()
        
        # Parse JSON log
        log_data = json.loads(log_output.strip())
        
        # Verify all required fields are present
        assert "timestamp" in log_data
        assert "level" in log_data
        assert "component" in log_data
        assert "message" in log_data
        assert "context" in log_data
        
        # Verify context contains request details
        context = log_data["context"]
        assert context["method"] == method
        assert context["path"] == path
        assert "response_time_ms" in context
        assert context["status_code"] == status_code
        
        # Verify message contains key information
        assert method in log_data["message"]
        assert path in log_data["message"]
        assert str(status_code) in log_data["message"]
    
    # Feature: urbanguard-ai-system, Property 50: Error Response Format
    @given(
        error_type=st.sampled_from(["validation", "external_api", "database", "not_found", "internal"]),
        message=st.text(min_size=1, max_size=200)
    )
    @settings(max_examples=100)
    def test_property_50_error_response_format(
        self,
        error_type,
        message
    ):
        """
        Property 50: For any error condition, the Dashboard_API should return
        an error response with an appropriate HTTP status code and a descriptive error message.
        
        Validates: Requirement 20.5
        """
        # Generate error response based on type
        if error_type == "validation":
            response = ErrorResponse.validation_error(message)
            expected_status = 400
        elif error_type == "external_api":
            response = ErrorResponse.external_api_error("TestService", message)
            expected_status = 503
        elif error_type == "database":
            response = ErrorResponse.database_error(message)
            expected_status = 500
        elif error_type == "not_found":
            response = ErrorResponse.not_found_error(message)
            expected_status = 404
        else:  # internal
            response = ErrorResponse.internal_error(message)
            expected_status = 500
        
        # Verify response structure
        assert isinstance(response, dict)
        assert "error" in response
        assert "message" in response
        assert "status_code" in response
        
        # Verify status code
        assert response["status_code"] == expected_status
        
        # Verify message is descriptive (non-empty)
        assert len(response["message"]) > 0
        
        # Verify error type is descriptive
        assert len(response["error"]) > 0
    
    # Feature: urbanguard-ai-system, Additional property: Field validation
    @given(
        required_fields=st.lists(
            st.text(min_size=1, max_size=20),
            min_size=1,
            max_size=10,
            unique=True
        ),
        data=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.text(), st.integers(), st.none()),
            min_size=0,
            max_size=15
        )
    )
    @settings(max_examples=100)
    def test_field_validation(self, required_fields, data):
        """
        Additional property: Field validation should correctly identify missing fields.
        """
        error = validate_required_fields(data, required_fields)
        
        # Check if all required fields are present
        all_present = all(
            field in data and data[field] is not None and
            (not isinstance(data[field], str) or len(data[field].strip()) > 0)
            for field in required_fields
        )
        
        if all_present:
            # Should have no error
            assert error is None
        else:
            # Should have an error message
            assert error is not None
            assert isinstance(error, str)
            assert len(error) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
