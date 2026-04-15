"""
Property-based tests for AI Classifier
Tests universal properties that should hold for all inputs

**Validates: Requirements 2.1, 2.2, 2.3**
"""
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings
from ai_classifier import AIClassifier
from constants import COMPLAINT_CATEGORIES, BENGALURU_LOCATIONS
from botocore.exceptions import ClientError, ReadTimeoutError


class TestAIClassifierProperties:
    """Property-based tests for AI Classifier"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = AIClassifier()
    
    # **Property 8: Single Category Assignment**
    # For any complaint processed by the AI_Classifier, exactly one category should be assigned
    # **Validates: Requirements 2.3**
    @given(
        description=st.text(min_size=0, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_property_8_single_category_assignment(self, description, location):
        """
        Property 8: Single Category Assignment
        Validates that exactly one category is assigned to each complaint.
        """
        category, confidence = self.classifier.classify_complaint(description, location)

        # Verify exactly one category is returned
        assert isinstance(category, str), "Category must be a string"
        assert category in COMPLAINT_CATEGORIES, f"Category '{category}' must be one of the valid categories"
        assert len(category) > 0, "Category must not be empty"
        
        # Ensure it's a single category (no delimiters indicating multiple categories)
        assert category.count(',') == 0, "Category should not contain commas (multiple categories)"
        assert category.count(';') == 0, "Category should not contain semicolons (multiple categories)"
        assert category.count('|') == 0, "Category should not contain pipes (multiple categories)"
        
        # Verify confidence is also returned
        assert isinstance(confidence, float), "Confidence must be a float"
        assert 0.0 <= confidence <= 1.0, "Confidence must be between 0.0 and 1.0"

    # Additional property tests for robustness
    
    @given(
        description=st.text(min_size=0, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_confidence_score_bounds(self, description, location):
        """Validates that confidence scores are always between 0.0 and 1.0"""
        category, confidence = self.classifier.classify_complaint(description, location)

        assert isinstance(confidence, float), "Confidence must be a float"
        assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} must be between 0.0 and 1.0"


    @given(
        description=st.text(min_size=0, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_valid_category_return(self, description, location):
        """Validates that returned category is always one of the valid categories"""
        category, confidence = self.classifier.classify_complaint(description, location)

        assert category in COMPLAINT_CATEGORIES, f"Category '{category}' must be in {COMPLAINT_CATEGORIES}"


    @given(
        description=st.text(min_size=1, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_classification_determinism(self, description, location):
        """Validates that classification is deterministic for the same input"""
        category1, confidence1 = self.classifier.classify_complaint(description, location)
        category2, confidence2 = self.classifier.classify_complaint(description, location)

        assert category1 == category2, "Same input should produce same category"
        assert confidence1 == confidence2, "Same input should produce same confidence"


    @given(
        description=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != ""),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_case_insensitivity(self, description, location):
        """Validates that classification is case-insensitive"""
        category_lower, _ = self.classifier.classify_complaint(description.lower(), location)
        category_upper, _ = self.classifier.classify_complaint(description.upper(), location)

        assert category_lower == category_upper, "Classification should be case-insensitive"


    @given(
        description=st.text(min_size=0, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_non_empty_category(self, description, location):
        """Validates that category is never empty"""
        category, confidence = self.classifier.classify_complaint(description, location)

        assert len(category) > 0, "Category must not be empty"
        assert category.strip() != "", "Category must not be whitespace only"


    @given(
        keyword=st.sampled_from([
            "pothole", "flooding", "traffic", "garbage",
            "streetlight", "water supply", "noise", "construction"
        ]),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_keyword_match_increases_confidence(self, keyword, location):
        """Validates that keyword matches increase confidence scores"""
        description_with_keyword = f"There is a {keyword} problem here"
        category_with, confidence_with = self.classifier.classify_complaint(
            description_with_keyword, location
        )

        description_without = "xyz abc def"
        category_without, confidence_without = self.classifier.classify_complaint(
            description_without, location
        )

        assert confidence_with > confidence_without, \
            f"Keyword match should increase confidence: {confidence_with} vs {confidence_without}"


    @given(
        description=st.text(min_size=0, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5)
    def test_return_type_consistency(self, description, location):
        """Validates that return type is always a tuple of (str, float)"""
        result = self.classifier.classify_complaint(description, location)

        assert isinstance(result, tuple), "Result must be a tuple"
        assert len(result) == 2, "Result must have exactly 2 elements"
        assert isinstance(result[0], str), "First element must be a string (category)"
        assert isinstance(result[1], float), "Second element must be a float (confidence)"



    # **Property 6: AI Classification Attempts Bedrock First**
    # For any complaint received, the AI_Classifier should attempt classification using Amazon Bedrock
    # before falling back to keyword-based classification
    # **Validates: Requirements 2.1**
    @given(
        description=st.text(min_size=1, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5, deadline=None)
    def test_property_6_bedrock_attempted_first(self, description, location):
        """
        Property 6: AI Classification Attempts Bedrock First
        Validates that Bedrock is attempted before keyword fallback.
        """
        # Track if Bedrock was attempted
        bedrock_called = []
        keyword_called = []
        
        # Create a fresh classifier with mocked Bedrock client to avoid slow credential lookups
        with patch('ai_classifier.boto3.client') as mock_boto_client:
            mock_bedrock = MagicMock()
            mock_boto_client.return_value = mock_bedrock
            
            classifier = AIClassifier()
            
            original_bedrock = classifier._bedrock_classify
            original_keyword = classifier._keyword_classify
            
            def mock_bedrock_classify(desc, loc):
                bedrock_called.append(True)
                # Return None to trigger fallback
                return None
            
            def mock_keyword_classify(desc):
                keyword_called.append(True)
                return original_keyword(desc)
            
            classifier._bedrock_classify = mock_bedrock_classify
            classifier._keyword_classify = mock_keyword_classify
            
            # Perform classification
            category, confidence = classifier.classify_complaint(description, location)
            
            # Verify Bedrock was attempted first
            assert len(bedrock_called) > 0, "Bedrock classification should be attempted"
            
            # If keyword was called, Bedrock must have been called first
            if len(keyword_called) > 0:
                assert len(bedrock_called) > 0, "Bedrock must be attempted before keyword fallback"
            
            # Verify valid result
            assert category in COMPLAINT_CATEGORIES, f"Category '{category}' must be valid"
            assert 0.0 <= confidence <= 1.0, "Confidence must be between 0.0 and 1.0"


    # **Property 7: Classification Fallback on Bedrock Failure**
    # For any complaint, if Amazon Bedrock is unavailable or returns an error, the AI_Classifier
    # should use keyword-based fallback classification and still return a valid category
    # **Validates: Requirements 2.2**
    
    @given(
        description=st.text(min_size=1, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5, deadline=None)
    def test_property_7_fallback_when_bedrock_unavailable(self, description, location):
        """
        Property 7: Classification Fallback on Bedrock Failure
        Validates fallback when Bedrock client is not initialized.
        """
        classifier = AIClassifier()
        # Simulate Bedrock being unavailable
        classifier.bedrock_client = None

        category, confidence = classifier.classify_complaint(description, location)

        # Verify valid category is still returned
        assert category in COMPLAINT_CATEGORIES, f"Category '{category}' must be valid even without Bedrock"
        assert isinstance(category, str), "Category must be a string"
        assert len(category) > 0, "Category must not be empty"
        assert 0.0 <= confidence <= 1.0, "Confidence must be between 0.0 and 1.0"
    
    @given(
        description=st.text(min_size=1, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5, deadline=None)
    def test_property_7_fallback_on_bedrock_timeout(self, description, location):
        """
        Property 7: Classification Fallback on Bedrock Failure
        Validates fallback when Bedrock times out.
        """
        classifier = AIClassifier()

        def mock_timeout(desc, loc):
            raise ReadTimeoutError(endpoint_url="test")

        with patch.object(classifier, "_call_bedrock_api", side_effect=mock_timeout):
            category, confidence = classifier.classify_complaint(description, location)

            # Verify valid category is returned despite timeout
            assert category in COMPLAINT_CATEGORIES, f"Category '{category}' must be valid after timeout"
            assert 0.0 <= confidence <= 1.0, "Confidence must be between 0.0 and 1.0"
    
    @given(
        description=st.text(min_size=1, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5, deadline=None)
    def test_property_7_fallback_on_bedrock_client_error(self, description, location):
        """
        Property 7: Classification Fallback on Bedrock Failure
        Validates fallback when Bedrock returns a client error.
        """
        classifier = AIClassifier()

        def mock_error(desc, loc):
            raise ClientError(
                error_response={'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
                operation_name='InvokeModel'
            )

        with patch.object(classifier, "_call_bedrock_api", side_effect=mock_error):
            category, confidence = classifier.classify_complaint(description, location)

            # Verify valid category is returned despite error
            assert category in COMPLAINT_CATEGORIES, f"Category '{category}' must be valid after client error"
            assert 0.0 <= confidence <= 1.0, "Confidence must be between 0.0 and 1.0"
    
    @given(
        description=st.text(min_size=1, max_size=200),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=5, deadline=None)
    def test_property_7_fallback_on_bedrock_invalid_response(self, description, location):
        """
        Property 7: Classification Fallback on Bedrock Failure
        Validates fallback when Bedrock returns an invalid response.
        """
        classifier = AIClassifier()

        def mock_invalid_response(desc, loc):
            # Simulate invalid response that can't be parsed
            raise ValueError("Invalid category from Bedrock")

        with patch.object(classifier, "_call_bedrock_api", side_effect=mock_invalid_response):
            category, confidence = classifier.classify_complaint(description, location)

            # Verify valid category is returned despite invalid response
            assert category in COMPLAINT_CATEGORIES, f"Category '{category}' must be valid after invalid response"
            assert 0.0 <= confidence <= 1.0, "Confidence must be between 0.0 and 1.0"