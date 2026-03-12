"""
UrbanGuard AI System - Error Handling and Logging
Comprehensive error handling with retry logic and structured logging
"""
import logging
import json
import time
from datetime import datetime
from typing import Optional, Callable, Any
from functools import wraps


# ============================================================================
# Structured Logging Configuration
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON with timestamp, level, component, message, and context.
    
    Validates: Requirement 20.1, 20.4
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["error_details"] = {
                "error_type": record.exc_info[0].__name__,
                "error_message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra context if present
        if hasattr(record, 'context'):
            log_data["context"] = record.context
        
        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True
) -> None:
    """
    Configure logging system with structured JSON formatting.
    
    Args:
        level: Log level (ERROR, WARN, INFO, DEBUG)
        json_format: Whether to use JSON formatting
        
    Validates: Requirement 20.1, 20.4
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    
    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_error(
    component: str,
    message: str,
    error: Optional[Exception] = None,
    context: Optional[dict] = None
) -> None:
    """
    Log an error with structured information.
    
    Args:
        component: Component name where error occurred
        message: Error message
        error: Exception object (optional)
        context: Additional context (optional)
        
    Validates: Requirement 20.1
    """
    logger = logging.getLogger(component)
    
    if context:
        logger.error(message, exc_info=error, extra={"context": context})
    else:
        logger.error(message, exc_info=error)


# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function with retry logic
        
    Retry delays:
        - Attempt 1: 1 second
        - Attempt 2: 2 seconds
        - Attempt 3: 4 seconds
        
    Validates: Requirement 20.2
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Log retry attempt
                        logger = logging.getLogger(func.__module__)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        
                        # Wait before retry
                        time.sleep(delay)
                        
                        # Increase delay exponentially
                        delay *= backoff_factor
                    else:
                        # All retries exhausted
                        logger = logging.getLogger(func.__module__)
                        logger.error(
                            f"All {max_retries} retry attempts failed for {func.__name__}: {e}",
                            exc_info=True
                        )
            
            # Raise the last exception after all retries
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================================
# Error Response Classes
# ============================================================================

class ErrorResponse:
    """
    Structured error response for API endpoints.
    
    Validates: Requirement 20.5
    """
    
    @staticmethod
    def validation_error(message: str, field: Optional[str] = None) -> dict:
        """
        Create a 400 Bad Request error response for validation errors.
        
        Args:
            message: Error message
            field: Field name that failed validation (optional)
            
        Returns:
            Error response dict with status code and message
            
        Validates: Requirement 20.5
        """
        response = {
            "error": "Validation Error",
            "message": message,
            "status_code": 400
        }
        
        if field:
            response["field"] = field
        
        return response
    
    @staticmethod
    def external_api_error(service: str, message: str) -> dict:
        """
        Create a 503 Service Unavailable error response for external API failures.
        
        Args:
            service: Name of the external service
            message: Error message
            
        Returns:
            Error response dict with status code and message
            
        Validates: Requirement 20.3, 20.5
        """
        return {
            "error": "External Service Unavailable",
            "message": f"{service}: {message}",
            "status_code": 503
        }
    
    @staticmethod
    def database_error(message: str) -> dict:
        """
        Create a 500 Internal Server Error response for database errors.
        
        Args:
            message: Error message
            
        Returns:
            Error response dict with status code and message
            
        Validates: Requirement 20.5
        """
        return {
            "error": "Database Error",
            "message": message,
            "status_code": 500
        }
    
    @staticmethod
    def not_found_error(resource: str) -> dict:
        """
        Create a 404 Not Found error response.
        
        Args:
            resource: Name of the resource that was not found
            
        Returns:
            Error response dict with status code and message
        """
        return {
            "error": "Not Found",
            "message": f"{resource} not found",
            "status_code": 404
        }
    
    @staticmethod
    def internal_error(message: str) -> dict:
        """
        Create a 500 Internal Server Error response.
        
        Args:
            message: Error message
            
        Returns:
            Error response dict with status code and message
        """
        return {
            "error": "Internal Server Error",
            "message": message,
            "status_code": 500
        }


# ============================================================================
# Request Logging Middleware
# ============================================================================

class RequestLogger:
    """
    Middleware for logging HTTP requests with method, path, and response time.
    
    Validates: Requirement 20.4
    """
    
    def __init__(self, component: str = "API"):
        """
        Initialize request logger.
        
        Args:
            component: Component name for logging
        """
        self.logger = logging.getLogger(component)
        self.component = component
    
    def log_request(
        self,
        method: str,
        path: str,
        response_time_ms: float,
        status_code: int,
        client_ip: Optional[str] = None
    ) -> None:
        """
        Log an HTTP request with details.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            client_ip: Client IP address (optional)
            
        Validates: Requirement 20.4
        """
        context = {
            "method": method,
            "path": path,
            "response_time_ms": round(response_time_ms, 2),
            "status_code": status_code
        }
        
        if client_ip:
            context["client_ip"] = client_ip
        
        self.logger.info(
            f"{method} {path} - {status_code} - {response_time_ms:.2f}ms",
            extra={"context": context}
        )


# ============================================================================
# Graceful Error Handling Utilities
# ============================================================================

def handle_external_api_failure(
    service_name: str,
    fallback_value: Any = None,
    log_component: str = "ExternalAPI"
) -> Callable:
    """
    Decorator for handling external API failures gracefully.
    
    Args:
        service_name: Name of the external service
        fallback_value: Value to return on failure (optional)
        log_component: Component name for logging
        
    Returns:
        Decorated function with graceful error handling
        
    Validates: Requirement 20.3
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                log_error(
                    component=log_component,
                    message=f"{service_name} API call failed",
                    error=e,
                    context={"service": service_name}
                )
                
                # Return fallback value if provided
                if fallback_value is not None:
                    logger = logging.getLogger(log_component)
                    logger.warning(
                        f"Using fallback value for {service_name} after failure"
                    )
                    return fallback_value
                
                # Re-raise if no fallback
                raise
        
        return wrapper
    return decorator


def validate_required_fields(data: dict, required_fields: list) -> Optional[str]:
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Error message if validation fails, None if successful
        
    Validates: Requirement 20.5
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            return f"Missing required field: {field}"
        
        # Check for empty strings
        if isinstance(data[field], str) and len(data[field].strip()) == 0:
            return f"Field '{field}' cannot be empty"
    
    return None


# Initialize logging on module import
setup_logging(level="INFO", json_format=False)  # Use simple format for development
