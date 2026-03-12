"""
UrbanGuard AI System - AI Classifier
Categorizes complaints using Amazon Bedrock or keyword-based fallback
"""
import json
import logging
import os
import time
from typing import Optional, Tuple
from datetime import datetime, timedelta
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError
from constants import COMPLAINT_CATEGORIES, CATEGORY_KEYWORDS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern for external API calls.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service recovered, allow one test request
    """
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery (half-open)
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result if successful, None if circuit is open
            
        Raises:
            Exception: If function fails and circuit is closed/half-open
        """
        if self.state == "OPEN":
            # Check if timeout has elapsed
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                logger.info("Circuit breaker entering HALF_OPEN state")
                self.state = "HALF_OPEN"
            else:
                logger.warning("Circuit breaker is OPEN, failing fast")
                return None
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= 3:
                logger.info("Circuit breaker closing after 3 successes")
                self.state = "CLOSED"
                self.failure_count = 0
                self.success_count = 0
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            logger.error(f"Circuit breaker opening after {self.failure_count} failures")
            self.state = "OPEN"


class AIClassifier:
    """
    Classifies complaints using AI or keyword fallback.
    
    Primary: Amazon Bedrock with prompt engineering for 8 categories
    Fallback: Keyword matching when Bedrock unavailable
    Always returns exactly one category
    """
    
    def __init__(self):
        """Initialize the AI classifier with Bedrock client and circuit breaker."""
        self.bedrock_client = None
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        self.bedrock_timeout = 3  # seconds
        
        # Initialize Bedrock client if credentials are available
        try:
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-v2")
            
            # Configure boto3 with timeout settings
            config = Config(
                region_name=aws_region,
                read_timeout=self.bedrock_timeout,
                connect_timeout=2,
                retries={'max_attempts': 0}  # No automatic retries, we handle this
            )
            
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                config=config
            )
            self.model_id = model_id
            logger.info(f"Bedrock client initialized with model {model_id} in region {aws_region}")
        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock client: {e}. Will use keyword fallback only.")
            self.bedrock_client = None
    
    def classify_complaint(
        self,
        description: str,
        location: str
    ) -> Tuple[str, float]:
        """
        Classifies complaint using Amazon Bedrock or keyword fallback.
        
        Args:
            description: Complaint text
            location: Location context for classification
            
        Returns:
            Tuple of (category, confidence_score)
            - category: One of 8 supported categories
            - confidence_score: 0.0 - 1.0
            
        Performance:
            - < 3 seconds total (including Bedrock API call)
            
        Accuracy:
            - Target: 85% on test data
        """
        # Attempt Bedrock classification first
        bedrock_result = self._bedrock_classify(description, location)
        
        if bedrock_result is not None:
            return bedrock_result
        
        # Fall back to keyword classification
        logger.info("Using keyword-based fallback classification")
        return self._keyword_classify(description)
    
    def _bedrock_classify(self, description: str, location: str) -> Optional[Tuple[str, float]]:
        """
        Attempts classification via Amazon Bedrock.
        
        Args:
            description: Complaint text
            location: Location context
            
        Returns:
            Tuple of (category, confidence) if successful, None if failed
        """
        if self.bedrock_client is None:
            logger.debug("Bedrock client not initialized, skipping")
            return None
        
        try:
            # Use circuit breaker to protect against repeated failures
            result = self.circuit_breaker.call(
                self._call_bedrock_api,
                description,
                location
            )
            return result
        except Exception as e:
            logger.warning(f"Bedrock classification failed: {e}")
            return None
    
    def _call_bedrock_api(self, description: str, location: str) -> Tuple[str, float]:
        """
        Makes the actual Bedrock API call.
        
        Args:
            description: Complaint text
            location: Location context
            
        Returns:
            Tuple of (category, confidence)
            
        Raises:
            Exception: If API call fails
        """
        # Create classification prompt
        prompt = self._create_classification_prompt(description, location)
        
        # Prepare request body based on model
        if "anthropic" in self.model_id.lower():
            body = json.dumps({
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 100,
                "temperature": 0.1,
                "top_p": 0.9,
            })
        else:
            # Generic format for other models
            body = json.dumps({
                "prompt": prompt,
                "max_tokens": 100,
                "temperature": 0.1,
            })
        
        try:
            # Call Bedrock API with timeout
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract completion based on model
            if "anthropic" in self.model_id.lower():
                completion = response_body.get('completion', '')
            else:
                completion = response_body.get('generated_text', '')
            
            # Parse the category from completion
            category, confidence = self._parse_bedrock_response(completion)
            
            logger.info(f"Bedrock classified as '{category}' with confidence {confidence}")
            return (category, confidence)
            
        except ReadTimeoutError:
            logger.warning(f"Bedrock API timeout after {self.bedrock_timeout} seconds")
            raise
        except ClientError as e:
            logger.error(f"Bedrock API client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Bedrock API unexpected error: {e}")
            raise
    
    def _create_classification_prompt(self, description: str, location: str) -> str:
        """
        Creates the classification prompt for Bedrock.
        
        Args:
            description: Complaint text
            location: Location context
            
        Returns:
            Formatted prompt string
        """
        categories_list = ", ".join(COMPLAINT_CATEGORIES)
        
        prompt = f"""You are an AI assistant helping to classify urban infrastructure complaints for the city of Bengaluru, India.

Classify the following complaint into exactly ONE of these categories:
{categories_list}

Complaint Location: {location}
Complaint Description: {description}

Respond with ONLY the category name (one word) followed by a confidence score (0.0 to 1.0) separated by a comma.
Example response format: "pothole,0.95" or "flooding,0.87"

Your response:"""
        
        return prompt
    
    def _parse_bedrock_response(self, completion: str) -> Tuple[str, float]:
        """
        Parses Bedrock API response to extract category and confidence.
        
        Args:
            completion: Raw completion text from Bedrock
            
        Returns:
            Tuple of (category, confidence)
            
        Raises:
            ValueError: If response cannot be parsed
        """
        # Clean up the response
        completion = completion.strip().lower()
        
        # Try to parse "category,confidence" format
        if ',' in completion:
            parts = completion.split(',')
            category = parts[0].strip()
            try:
                confidence = float(parts[1].strip())
            except (ValueError, IndexError):
                confidence = 0.85  # Default confidence if parsing fails
        else:
            # If no comma, try to extract just the category
            category = completion.split()[0].strip()
            confidence = 0.85  # Default confidence
        
        # Validate category
        if category not in COMPLAINT_CATEGORIES:
            # Try to find closest match
            for valid_category in COMPLAINT_CATEGORIES:
                if valid_category in category or category in valid_category:
                    category = valid_category
                    break
            else:
                # No match found, raise error to trigger fallback
                raise ValueError(f"Invalid category from Bedrock: {category}")
        
        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))
        
        return (category, confidence)
    
    def _keyword_classify(self, description: str) -> Tuple[str, float]:
        """
        Fallback keyword-based classification.
        
        Args:
            description: Complaint text to classify
            
        Returns:
            Tuple of (category, confidence_score)
            - Always returns exactly one category
            - Confidence based on keyword match strength
            
        Algorithm:
            1. Convert description to lowercase for case-insensitive matching
            2. For each category, count keyword matches
            3. Calculate match score based on number of matches
            4. Return category with highest score
            5. If no keywords match, return default category with low confidence
        """
        description_lower = description.lower()
        
        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            match_count = 0
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    match_count += 1
            category_scores[category] = match_count
        
        # Find category with highest score
        max_score = max(category_scores.values())
        
        if max_score == 0:
            # No keywords matched - return default category with low confidence
            return ("garbage", 0.3)
        
        # Get category with highest score
        best_category = max(category_scores, key=category_scores.get)
        
        # Calculate confidence based on match count
        # More matches = higher confidence
        # Cap at 0.9 for keyword-based classification (not as confident as AI)
        confidence = min(0.9, 0.5 + (max_score * 0.1))
        
        return (best_category, confidence)
