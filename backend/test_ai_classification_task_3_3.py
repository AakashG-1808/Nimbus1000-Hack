"""
Property-based tests for AI Classification (Task 3.3)
Tests Properties 6, 7, and 8 with reduced examples for faster execution

Task 3.3: Write property tests for AI classification
- Property 6: AI Classification Attempts Bedrock First
- Property 7: Classification Fallback on Bedrock Failure
- Property 8: Single Category Assignment
"""
import pytest
from unittest.mock import patch
from hypothesis import given, strategies as st, settings
from ai_classifier import AIClassifier
from constants import COMPLAINT_CATEGORIES, BENGALURU_LOCATIONS
from botocore.exceptions import ClientError, ReadTimeoutError


class TestAIClassificationTask33:
    """Property-based tests for AI Classification (Task 3.3)"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = AIClassifier()
    
    # Feature: urbanguard-ai-system, Property 6: AI Classification Attempts Bedrock First
    @given(
        description=st.text(min_size=1, max_size=500),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=20)
    def test_property_6_bedrock_attempted_first(self, description, location):
        """
        **Validates: Requirements 2.1**
        
        Property 6: AI Classification Attempts Bedrock First
        For any complaint received, the AI_Classifier should attempt classification 
        using Amazon Bedrock before falling back to keyword-based classification.
        
        This test verifies that:
        1. Bedrock classification is attempted first
        2. Even if Bedrock fails, a valid category is returned via fallback
        """
        # Create a fresh classifier with mocked Bedrock client
        classifier = AIClassifier()
        
        # Track if Bedrock was called
        bedrock_called = []
        
        def mock_bedrock_classify(desc, loc):
            bedrock_called.append(True)
            # Return None to trigger fallback
            return None
        
        # Replace the _bedrock_classify method
        classifier._bedrock_classify = mock_bedrock_classify
        
        # Classify the complaint
        category, confidence = classifier.classify_complaint(description, location)
        
        # Verify Bedrock was attempted first
        assert len(bedrock_called) > 0, "Bedrock classification should be attempted first"
        
        # Verify a valid category was still returned (via fallback)
        assert category in COMPLAINT_CATEGORIES
        assert 0.0 <= confidence <= 1.0
    
    # Feature: urbanguard-ai-system, Property 7: Classification Fallback on Bedrock Failure
    @given(
        description=st.text(min_size=1, max_size=500),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=20)
    def test_property_7_fallback_on_bedrock_unavailable(self, description, location):
        """
        **Validates: Requirements 2.2**
        
        Property 7: Classification Fallback on Bedrock Failure
        For any complaint, if Amazon Bedrock is unavailable or returns an error, 
        the AI_Classifier should use keyword-based fallback classification and 
        still return a valid category.
        
        This test simulates Bedrock being unavailable (no client).
        """
        # Create a classifier with no Bedrock client (simulating unavailability)
        classifier = AIClassifier()
        classifier.bedrock_client = None
        
        # Classify the complaint - should use fallback
        category, confidence = classifier.classify_complaint(description, location)
        
        # Verify fallback returns a valid category
        assert category in COMPLAINT_CATEGORIES, f"Expected valid category, got: {category}"
        assert isinstance(category, str)
        assert len(category) > 0
        
        # Verify confidence is in valid range
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
        
        # Verify exactly one category is returned (not multiple)
        assert category.count(',') == 0
        assert category.count(';') == 0
    
    # Feature: urbanguard-ai-system, Property 7: Fallback on Bedrock Timeout
    @given(
        description=st.text(min_size=1, max_size=500),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=20)
    def test_property_7_fallback_on_bedrock_timeout(self, description, location):
        """
        **Validates: Requirements 2.2**
        
        Property 7 (Timeout Case): Classification Fallback on Bedrock Failure
        For any complaint, if Amazon Bedrock times out, the AI_Classifier should 
        use keyword-based fallback classification and still return a valid category.
        
        This test simulates Bedrock timing out.
        """
        # Create a classifier and mock Bedrock to raise timeout
        classifier = AIClassifier()
        
        def mock_bedrock_timeout(desc, loc):
            # Simulate Bedrock timeout
            raise ReadTimeoutError(endpoint_url="test")
        
        # Mock the _call_bedrock_api method to raise timeout
        with patch.object(classifier, '_call_bedrock_api', side_effect=mock_bedrock_timeout):
            # Classify the complaint - should use fallback after timeout
            category, confidence = classifier.classify_complaint(description, location)
            
            # Verify fallback returns a valid category
            assert category in COMPLAINT_CATEGORIES
            assert isinstance(category, str)
            assert len(category) > 0
            
            # Verify confidence is in valid range
            assert 0.0 <= confidence <= 1.0
    
    # Feature: urbanguard-ai-system, Property 7: Fallback on Bedrock Client Error
    @given(
        description=st.text(min_size=1, max_size=500),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=20)
    def test_property_7_fallback_on_bedrock_client_error(self, description, location):
        """
        **Validates: Requirements 2.2**
        
        Property 7 (Client Error Case): Classification Fallback on Bedrock Failure
        For any complaint, if Amazon Bedrock returns a client error, the AI_Classifier 
        should use keyword-based fallback classification and still return a valid category.
        
        This test simulates Bedrock returning a client error.
        """
        # Create a classifier and mock Bedrock to raise client error
        classifier = AIClassifier()
        
        def mock_bedrock_error(desc, loc):
            # Simulate Bedrock client error
            raise ClientError(
                error_response={'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
                operation_name='InvokeModel'
            )
        
        # Mock the _call_bedrock_api method to raise client error
        with patch.object(classifier, '_call_bedrock_api', side_effect=mock_bedrock_error):
            # Classify the complaint - should use fallback after error
            category, confidence = classifier.classify_complaint(description, location)
            
            # Verify fallback returns a valid category
            assert category in COMPLAINT_CATEGORIES
            assert isinstance(category, str)
            assert len(category) > 0
            
            # Verify confidence is in valid range
            assert 0.0 <= confidence <= 1.0
    
    # Feature: urbanguard-ai-system, Property 8: Single Category Assignment
    @given(
        description=st.text(min_size=0, max_size=500),
        location=st.sampled_from(list(BENGALURU_LOCATIONS.keys()))
    )
    @settings(max_examples=20)
    def test_property_8_single_category_assignment(self, description, location):
        """
        **Validates: Requirements 2.3**
        
        Property 8: Single Category Assignment
        For any complaint processed by the AI_Classifier, exactly one category 
        should be assigned (no more, no less).
        
        This test verifies that:
        1. A single category string is returned
        2. The category is valid (from the 8 supported categories)
        3. No multiple categories are returned (no commas, semicolons, etc.)
        """
        category, confidence = self.classifier.classify_complaint(description, location)
        
        # Verify exactly one category is returned
        assert isinstance(category, str)
        assert category in COMPLAINT_CATEGORIES
        
        # Verify it's a single category (not a list or multiple values)
        assert len(category) > 0
        assert category.count(',') == 0  # No comma-separated categories
        assert category.count(';') == 0  # No semicolon-separated categories
        assert category.count('|') == 0  # No pipe-separated categories
        
        # Verify confidence is valid
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
