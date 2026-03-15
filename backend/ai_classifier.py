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
        
        try:
            aws_region = os.getenv("AWS_BEDROCK_REGION", os.getenv("AWS_REGION", "ap-south-2"))
            model_id = os.getenv("BEDROCK_MODEL_ID", "apac.anthropic.claude-3-5-sonnet-20241022-v2:0")
            bedrock_api_key = os.getenv("BEDROCK_API_KEY")

            config = Config(
                region_name=aws_region,
                read_timeout=self.bedrock_timeout,
                connect_timeout=2,
                retries={'max_attempts': 0}
            )

            if bedrock_api_key:
                # Use Bedrock API key authentication
                self.bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=aws_region,
                    aws_access_key_id=bedrock_api_key,
                    aws_secret_access_key="bedrock-api-key",  # placeholder, not used with API key auth
                    config=config
                )
                # Bedrock API keys use a different auth header — use requests directly
                self._use_api_key = True
                self._api_key = bedrock_api_key
                self._api_region = aws_region
                # Still set bedrock_client to a real boto3 client for compatibility
                # but override the actual call to use API key header
                self.bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=aws_region,
                    config=config
                )
                self._use_api_key = True
            else:
                self._use_api_key = False
                self.bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    config=config
                )

            self.model_id = model_id
            logger.info(f"Bedrock client initialized with model {model_id} in region {aws_region}"
                        + (" (API key auth)" if self._use_api_key else " (IAM auth)"))
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
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}]
            })
        elif "amazon.nova" in self.model_id.lower():
            # Amazon Nova uses Converse-style messages API
            body = json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}]
            })
        else:
            body = json.dumps({
                "prompt": prompt,
                "max_tokens": 100,
                "temperature": 0.1,
            })
        
        try:
            # Call Bedrock API — use API key header if configured, else IAM via boto3
            if getattr(self, '_use_api_key', False):
                import requests as _requests
                url = (f"https://bedrock-runtime.{self._api_region}.amazonaws.com"
                       f"/model/{self.model_id}/invoke")
                resp = _requests.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}",
                    },
                    data=body,
                    timeout=self.bedrock_timeout
                )
                resp.raise_for_status()
                response_body = resp.json()
            else:
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=body
                )
                response_body = json.loads(response['body'].read())
            
            # Extract completion based on model
            if "anthropic" in self.model_id.lower():
                completion = response_body.get("content", [{}])[0].get("text", "")
            elif "amazon.nova" in self.model_id.lower():
                # Nova returns output.message.content[0].text
                completion = (response_body.get("output", {})
                              .get("message", {})
                              .get("content", [{}])[0]
                              .get("text", ""))
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
        Creates the classification prompt for Bedrock, enriched with BBMP
        historical context when available.
        """
        categories_list = ", ".join(COMPLAINT_CATEGORIES)

        # Pull BBMP historical context if analysis has completed
        bbmp_context = ""
        try:
            from bbmp_data_loader import get_bbmp_insights
            insights = get_bbmp_insights()
            if insights:
                weights = insights.get("category_weights", {})
                boosts = insights.get("hotspot_risk_boosts", {})
                seasonal = insights.get("seasonal_warnings", [])

                lines = []
                if location in boosts:
                    lines.append(
                        f"- {location} is a historically high-complaint area "
                        f"(risk boost: +{boosts[location]} points)."
                    )
                if weights:
                    top_cats = sorted(weights.items(), key=lambda x: -x[1])[:3]
                    lines.append(
                        "- Historically high-frequency categories in Bengaluru: "
                        + ", ".join(f"{c} (×{w:.1f})" for c, w in top_cats) + "."
                    )
                if seasonal:
                    lines.append("- Seasonal patterns: " + "; ".join(seasonal))

                if lines:
                    bbmp_context = (
                        "\n\nHistorical BBMP grievance data context:\n"
                        + "\n".join(lines)
                        + "\nUse this context to improve classification accuracy.\n"
                    )
        except Exception:
            pass

        prompt = (
            f"You are an AI assistant helping to classify urban infrastructure complaints "
            f"for the city of Bengaluru, India.\n\n"
            f"Classify the following complaint into exactly ONE of these categories:\n"
            f"{categories_list}"
            f"{bbmp_context}\n"
            f"Complaint Location: {location}\n"
            f"Complaint Description: {description}\n\n"
            f"Respond with ONLY the category name (one word) followed by a confidence score "
            f"(0.0 to 1.0) separated by a comma.\n"
            f'Example response format: "pothole,0.95" or "flooding,0.87"\n\n'
            f"Your response:"
        )
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
    
    def explain_prediction(
        self,
        incident_type: str,
        area_name: str,
        risk_score: float,
        dominant_category: str,
        complaint_count: int,
        contributing_factors: list,
        time_window: str,
    ) -> str:
        """
        Generate a 2-3 sentence natural language explanation for an incident prediction,
        enriched with BBMP historical context when available.
        """
        factors_text = ", ".join(f.replace("_", " ") for f in contributing_factors)

        # Pull BBMP context for the explanation
        bbmp_context = ""
        try:
            from bbmp_data_loader import get_bbmp_insights
            insights = get_bbmp_insights()
            if insights:
                boosts = insights.get("hotspot_risk_boosts", {})
                seasonal = insights.get("seasonal_warnings", [])
                if area_name in boosts:
                    bbmp_context += (
                        f"\nHistorical data: {area_name} is a chronic hotspot "
                        f"with a +{boosts[area_name]}-point historical risk boost."
                    )
                if seasonal:
                    bbmp_context += f"\nSeasonal patterns: {'; '.join(seasonal)}"
        except Exception:
            pass

        prompt = (
            f"You are an urban risk analyst for Bengaluru, India.\n"
            f"Write exactly 2 sentences explaining this incident prediction to a city official.\n"
            f"Be specific, reference historical patterns if relevant, and be actionable. "
            f"Do not use bullet points.\n\n"
            f"Prediction details:\n"
            f"- Area: {area_name}\n"
            f"- Predicted incident: {incident_type.replace('_', ' ')}\n"
            f"- Risk score: {risk_score:.0f}/100\n"
            f"- Dominant complaint type: {dominant_category}\n"
            f"- Number of complaints in zone: {complaint_count}\n"
            f"- Contributing factors: {factors_text}\n"
            f"- Expected time window: {time_window}"
            f"{bbmp_context}\n\n"
            f"Your 2-sentence explanation:"
        )

        try:
            if self.bedrock_client is None:
                raise RuntimeError("No Bedrock client")

            if "amazon.nova" in self.model_id.lower():
                body = json.dumps({
                    "messages": [{"role": "user", "content": [{"text": prompt}]}]
                })
            else:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 150,
                    "temperature": 0.4,
                    "messages": [{"role": "user", "content": prompt}]
                })

            if getattr(self, '_use_api_key', False):
                import requests as _req
                url = (f"https://bedrock-runtime.{self._api_region}.amazonaws.com"
                       f"/model/{self.model_id}/invoke")
                resp = _req.post(
                    url,
                    headers={"Content-Type": "application/json",
                             "Authorization": f"Bearer {self._api_key}"},
                    data=body, timeout=8
                )
                resp.raise_for_status()
                rb = resp.json()
            else:
                response = self.bedrock_client.invoke_model(modelId=self.model_id, body=body)
                rb = json.loads(response['body'].read())

            if "amazon.nova" in self.model_id.lower():
                text = (rb.get("output", {}).get("message", {})
                        .get("content", [{}])[0].get("text", ""))
            else:
                text = rb.get("content", [{}])[0].get("text", "")

            return text.strip() if text.strip() else self._fallback_explanation(
                incident_type, area_name, risk_score, complaint_count, time_window
            )
        except Exception as e:
            logger.warning(f"Bedrock explanation failed: {e}")
            return self._fallback_explanation(
                incident_type, area_name, risk_score, complaint_count, time_window
            )

    def _fallback_explanation(self, incident_type, area_name, risk_score, complaint_count, time_window):
        type_label = incident_type.replace("_", " ").title()
        return (
            f"{complaint_count} complaints have been reported in the {area_name} area, "
            f"pushing the risk score to {risk_score:.0f}/100. "
            f"A {type_label} incident is likely within the {time_window}."
        )
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
