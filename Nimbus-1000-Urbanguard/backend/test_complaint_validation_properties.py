"""
UrbanGuard AI System - Complaint Validation Property-Based Tests
Property-based tests using Hypothesis to validate complaint validation logic.

These tests run with minimum 100 iterations to ensure correctness across a wide range of inputs.
"""
import pytest
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st, HealthCheck
from complaint_processor import ComplaintProcessor
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES


# Custom strategies for generating test data
def valid_locations():
    """Strategy for generating valid Bengaluru locations."""
    return st.sampled_from(list(BENGALURU_LOCATIONS.keys()))


def invalid_locations():
    """Strategy for generating invalid locations (not in Bengaluru)."""
    # Generate text that is NOT in the valid locations set
    return st.text(min_size=1).filter(lambda x: x not in BENGALURU_LOCATIONS)


def valid_categories():
    """Strategy for generating valid complaint categories."""
    return st.sampled_from(COMPLAINT_CATEGORIES)


def invalid_categories():
    """Strategy for generating invalid categories."""
    # Generate text that is NOT in the valid categories list
    return st.text(min_size=1).filter(lambda x: x not in COMPLAINT_CATEGORIES)


def valid_descriptions():
    """Strategy for generating valid descriptions."""
    return st.text(min_size=1).filter(lambda x: x.strip() != "")


def valid_timestamps():
    """Strategy for generating valid datetime objects."""
    # Generate timestamps within a reasonable range (past year to future week)
    return st.datetimes(
        min_value=datetime.now() - timedelta(days=365),
        max_value=datetime.now() + timedelta(days=7)
    )


# Property 2: Location Validation - Invalid locations should be rejected
# **Validates: Requirements 1.2**
class TestLocationValidationProperty:
    """Property-based tests for location validation."""
    
    @settings(max_examples=100)
    @given(location=invalid_locations())
    def test_invalid_locations_rejected(self, location):
        """
        Property 2: Location Validation
        
        For any submitted complaint, if the location is not in the predefined 
        Bengaluru_Location set, the Complaint_Processor should reject it with 
        an error message.
        
        **Validates: Requirements 1.2**
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_location(location)
        
        # Invalid location should be rejected
        assert is_valid is False, f"Location '{location}' should be rejected"
        
        # Error message should be descriptive
        assert error is not None, "Error message should not be None"
        assert "Invalid location" in error, "Error should mention 'Invalid location'"
        assert location in error, f"Error should include the invalid location name: {location}"
    
    @settings(max_examples=100)
    @given(location=valid_locations())
    def test_valid_locations_accepted(self, location):
        """
        Property 2 (inverse): Valid locations should be accepted.
        
        For any location in the predefined Bengaluru_Location set, 
        the Complaint_Processor should accept it.
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_location(location)
        
        # Valid location should be accepted
        assert is_valid is True, f"Location '{location}' should be accepted"
        assert error is None, "Error should be None for valid location"


# Property 3: Category Validation - Invalid categories should be rejected
# **Validates: Requirements 1.3**
class TestCategoryValidationProperty:
    """Property-based tests for category validation."""
    
    @settings(max_examples=100)
    @given(category=invalid_categories())
    def test_invalid_categories_rejected(self, category):
        """
        Property 3: Category Validation
        
        For any submitted complaint, if the category is not one of the 8 supported 
        types (pothole, flooding, traffic, garbage, streetlight, water_supply, 
        noise, construction), the Complaint_Processor should reject it with an 
        error message.
        
        **Validates: Requirements 1.3**
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_category(category)
        
        # Invalid category should be rejected
        assert is_valid is False, f"Category '{category}' should be rejected"
        
        # Error message should be descriptive
        assert error is not None, "Error message should not be None"
        assert "Invalid category" in error, "Error should mention 'Invalid category'"
        assert category in error, f"Error should include the invalid category name: {category}"
        assert "Must be one of:" in error, "Error should list valid categories"
    
    @settings(max_examples=100)
    @given(category=valid_categories())
    def test_valid_categories_accepted(self, category):
        """
        Property 3 (inverse): Valid categories should be accepted.
        
        For any category in the 8 supported types, the Complaint_Processor 
        should accept it.
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_category(category)
        
        # Valid category should be accepted
        assert is_valid is True, f"Category '{category}' should be accepted"
        assert error is None, "Error should be None for valid category"


# Property 4: Invalid Complaint Error Response - Invalid data returns descriptive errors
# **Validates: Requirements 1.4**
class TestInvalidComplaintErrorResponseProperty:
    """Property-based tests for error response quality."""
    
    @settings(max_examples=100)
    @given(
        location=invalid_locations(),
        category=valid_categories(),
        description=valid_descriptions(),
        timestamp=valid_timestamps()
    )
    def test_invalid_location_returns_descriptive_error(self, location, category, description, timestamp):
        """
        Property 4: Invalid Complaint Error Response (Invalid Location)
        
        For any complaint with invalid location, the Complaint_Processor should 
        return a descriptive error message.
        
        **Validates: Requirements 1.4**
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        # Should be rejected
        assert is_valid is False, "Complaint with invalid location should be rejected"
        
        # Error should be descriptive
        assert error is not None, "Error message should not be None"
        assert len(error) > 10, "Error message should be descriptive (>10 chars)"
        assert "location" in error.lower(), "Error should mention location"
    
    @settings(max_examples=100)
    @given(
        location=valid_locations(),
        category=invalid_categories(),
        description=valid_descriptions(),
        timestamp=valid_timestamps()
    )
    def test_invalid_category_returns_descriptive_error(self, location, category, description, timestamp):
        """
        Property 4: Invalid Complaint Error Response (Invalid Category)
        
        For any complaint with invalid category, the Complaint_Processor should 
        return a descriptive error message.
        
        **Validates: Requirements 1.4**
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        # Should be rejected
        assert is_valid is False, "Complaint with invalid category should be rejected"
        
        # Error should be descriptive
        assert error is not None, "Error message should not be None"
        assert len(error) > 10, "Error message should be descriptive (>10 chars)"
        assert "category" in error.lower(), "Error should mention category"
    
    @settings(max_examples=100)
    @given(
        location=valid_locations(),
        category=valid_categories(),
        timestamp=valid_timestamps()
    )
    def test_empty_description_returns_descriptive_error(self, location, category, timestamp):
        """
        Property 4: Invalid Complaint Error Response (Empty Description)
        
        For any complaint with empty or whitespace-only description, 
        the Complaint_Processor should return a descriptive error message.
        
        **Validates: Requirements 1.4**
        """
        processor = ComplaintProcessor()
        # Test with empty string
        is_valid, error = processor.validate_complaint(
            location=location,
            category=category,
            description="",
            timestamp=timestamp
        )
        
        # Should be rejected
        assert is_valid is False, "Complaint with empty description should be rejected"
        
        # Error should be descriptive
        assert error is not None, "Error message should not be None"
        assert len(error) > 10, "Error message should be descriptive (>10 chars)"
        assert "description" in error.lower(), "Error should mention description"
    
    @settings(max_examples=100)
    @given(
        location=valid_locations(),
        category=valid_categories(),
        description=valid_descriptions()
    )
    def test_none_timestamp_returns_descriptive_error(self, location, category, description):
        """
        Property 4: Invalid Complaint Error Response (None Timestamp)
        
        For any complaint with None timestamp, the Complaint_Processor should 
        return a descriptive error message.
        
        **Validates: Requirements 1.4**
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=None
        )
        
        # Should be rejected
        assert is_valid is False, "Complaint with None timestamp should be rejected"
        
        # Error should be descriptive
        assert error is not None, "Error message should not be None"
        assert len(error) > 10, "Error message should be descriptive (>10 chars)"
        assert "timestamp" in error.lower(), "Error should mention timestamp"
    
    @settings(max_examples=100)
    @given(
        location=valid_locations(),
        category=valid_categories(),
        description=valid_descriptions(),
        timestamp=valid_timestamps()
    )
    def test_valid_complaint_no_error(self, location, category, description, timestamp):
        """
        Property 4 (inverse): Valid complaints should not return errors.
        
        For any complaint with all valid data, the Complaint_Processor should 
        accept it without error.
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        # Should be accepted
        assert is_valid is True, "Complaint with all valid data should be accepted"
        assert error is None, "Error should be None for valid complaint"


# Additional property: Error messages should always be non-empty strings when validation fails
class TestErrorMessageConsistency:
    """Property-based tests for error message consistency."""
    
    @settings(max_examples=100)
    @given(
        location=st.one_of(valid_locations(), invalid_locations(), st.just(""), st.none()),
        category=st.one_of(valid_categories(), invalid_categories(), st.just(""), st.none()),
        description=st.one_of(valid_descriptions(), st.just(""), st.just("   "), st.none()),
        timestamp=st.one_of(valid_timestamps(), st.none())
    )
    def test_error_messages_always_strings_when_invalid(self, location, category, description, timestamp):
        """
        Property: Error Message Consistency
        
        For any invalid complaint data, if validation fails, the error message 
        should always be a non-empty string.
        """
        processor = ComplaintProcessor()
        is_valid, error = processor.validate_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        # If validation fails, error must be a non-empty string
        if not is_valid:
            assert error is not None, "Error should not be None when validation fails"
            assert isinstance(error, str), "Error should be a string"
            assert len(error) > 0, "Error message should not be empty"
            assert error.strip() != "", "Error message should not be whitespace only"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
