"""
UrbanGuard AI System - Complaint Validation Tests
Tests for complaint validation logic
"""
import pytest
from datetime import datetime
from complaint_processor import ComplaintProcessor, ComplaintResult
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES


@pytest.fixture
def processor():
    """Create a ComplaintProcessor instance for testing."""
    return ComplaintProcessor()


class TestLocationValidation:
    """Tests for location validation."""
    
    def test_valid_location(self, processor):
        """Valid Bengaluru location should pass validation."""
        is_valid, error = processor.validate_location("Koramangala")
        assert is_valid is True
        assert error is None
    
    def test_invalid_location(self, processor):
        """Invalid location should fail validation with descriptive error."""
        is_valid, error = processor.validate_location("InvalidCity")
        assert is_valid is False
        assert "Invalid location" in error
        assert "InvalidCity" in error
        assert "not found in Bengaluru locations" in error
    
    def test_empty_location(self, processor):
        """Empty location should fail validation."""
        is_valid, error = processor.validate_location("")
        assert is_valid is False
        assert "Missing required field: location" in error
    
    def test_none_location(self, processor):
        """None location should fail validation."""
        is_valid, error = processor.validate_location(None)
        assert is_valid is False
        assert "Missing required field: location" in error
    
    def test_all_predefined_locations_valid(self, processor):
        """All predefined Bengaluru locations should be valid."""
        for location in BENGALURU_LOCATIONS.keys():
            is_valid, error = processor.validate_location(location)
            assert is_valid is True, f"Location {location} should be valid"
            assert error is None


class TestCategoryValidation:
    """Tests for category validation."""
    
    def test_valid_category(self, processor):
        """Valid category should pass validation."""
        is_valid, error = processor.validate_category("pothole")
        assert is_valid is True
        assert error is None
    
    def test_invalid_category(self, processor):
        """Invalid category should fail validation with descriptive error."""
        is_valid, error = processor.validate_category("invalid_category")
        assert is_valid is False
        assert "Invalid category" in error
        assert "invalid_category" in error
        assert "Must be one of:" in error
        # Check that all valid categories are listed in error message
        for category in COMPLAINT_CATEGORIES:
            assert category in error
    
    def test_empty_category(self, processor):
        """Empty category should fail validation."""
        is_valid, error = processor.validate_category("")
        assert is_valid is False
        assert "Missing required field: category" in error
    
    def test_none_category(self, processor):
        """None category should fail validation."""
        is_valid, error = processor.validate_category(None)
        assert is_valid is False
        assert "Missing required field: category" in error
    
    def test_all_supported_categories_valid(self, processor):
        """All 8 supported categories should be valid."""
        for category in COMPLAINT_CATEGORIES:
            is_valid, error = processor.validate_category(category)
            assert is_valid is True, f"Category {category} should be valid"
            assert error is None


class TestDescriptionValidation:
    """Tests for description validation."""
    
    def test_valid_description(self, processor):
        """Valid description should pass validation."""
        is_valid, error = processor.validate_description("Large pothole on main road")
        assert is_valid is True
        assert error is None
    
    def test_empty_description(self, processor):
        """Empty description should fail validation."""
        is_valid, error = processor.validate_description("")
        assert is_valid is False
        assert "Missing required field: description" in error
    
    def test_whitespace_only_description(self, processor):
        """Whitespace-only description should fail validation."""
        is_valid, error = processor.validate_description("   ")
        assert is_valid is False
        assert "cannot be empty or whitespace only" in error
    
    def test_none_description(self, processor):
        """None description should fail validation."""
        is_valid, error = processor.validate_description(None)
        assert is_valid is False
        assert "Missing required field: description" in error
    
    def test_non_string_description(self, processor):
        """Non-string description should fail validation."""
        is_valid, error = processor.validate_description(123)
        assert is_valid is False
        assert "must be a string" in error


class TestTimestampValidation:
    """Tests for timestamp validation."""
    
    def test_valid_timestamp(self, processor):
        """Valid datetime should pass validation."""
        is_valid, error = processor.validate_timestamp(datetime.now())
        assert is_valid is True
        assert error is None
    
    def test_none_timestamp(self, processor):
        """None timestamp should fail validation."""
        is_valid, error = processor.validate_timestamp(None)
        assert is_valid is False
        assert "Missing required field: timestamp" in error
    
    def test_non_datetime_timestamp(self, processor):
        """Non-datetime timestamp should fail validation."""
        is_valid, error = processor.validate_timestamp("2024-01-01")
        assert is_valid is False
        assert "must be a datetime object" in error


class TestCompleteComplaintValidation:
    """Tests for complete complaint validation."""
    
    def test_valid_complaint(self, processor):
        """Valid complaint with all fields should pass validation."""
        is_valid, error = processor.validate_complaint(
            location="Koramangala",
            category="pothole",
            description="Large pothole on main road",
            timestamp=datetime.now()
        )
        assert is_valid is True
        assert error is None
    
    def test_invalid_location_fails_validation(self, processor):
        """Complaint with invalid location should fail."""
        is_valid, error = processor.validate_complaint(
            location="InvalidCity",
            category="pothole",
            description="Test description",
            timestamp=datetime.now()
        )
        assert is_valid is False
        assert "Invalid location" in error
    
    def test_invalid_category_fails_validation(self, processor):
        """Complaint with invalid category should fail."""
        is_valid, error = processor.validate_complaint(
            location="Koramangala",
            category="invalid_category",
            description="Test description",
            timestamp=datetime.now()
        )
        assert is_valid is False
        assert "Invalid category" in error
    
    def test_invalid_description_fails_validation(self, processor):
        """Complaint with invalid description should fail."""
        is_valid, error = processor.validate_complaint(
            location="Koramangala",
            category="pothole",
            description="",
            timestamp=datetime.now()
        )
        assert is_valid is False
        assert "description" in error.lower()
    
    def test_invalid_timestamp_fails_validation(self, processor):
        """Complaint with invalid timestamp should fail."""
        is_valid, error = processor.validate_complaint(
            location="Koramangala",
            category="pothole",
            description="Test description",
            timestamp=None
        )
        assert is_valid is False
        assert "timestamp" in error.lower()
    
    def test_validation_stops_at_first_error(self, processor):
        """Validation should return first error encountered."""
        # Invalid location should be caught first
        is_valid, error = processor.validate_complaint(
            location="InvalidCity",
            category="invalid_category",
            description="",
            timestamp=None
        )
        assert is_valid is False
        assert "Invalid location" in error


class TestCoordinatesRetrieval:
    """Tests for coordinates retrieval."""
    
    def test_get_coordinates_for_valid_location(self, processor):
        """Should return correct coordinates for valid location."""
        coords = processor.get_coordinates("Koramangala")
        assert coords == (12.9352, 77.6245)
    
    def test_get_coordinates_for_all_locations(self, processor):
        """Should return coordinates for all predefined locations."""
        for location, expected_coords in BENGALURU_LOCATIONS.items():
            coords = processor.get_coordinates(location)
            assert coords == expected_coords, f"Coordinates mismatch for {location}"


class TestErrorMessageQuality:
    """Tests for error message quality and descriptiveness."""
    
    def test_location_error_includes_location_name(self, processor):
        """Location error should include the invalid location name."""
        _, error = processor.validate_location("Mumbai")
        assert "Mumbai" in error
    
    def test_category_error_lists_valid_categories(self, processor):
        """Category error should list all valid categories."""
        _, error = processor.validate_category("invalid")
        for category in COMPLAINT_CATEGORIES:
            assert category in error
    
    def test_error_messages_are_descriptive(self, processor):
        """All error messages should be descriptive and helpful."""
        # Test various invalid inputs
        test_cases = [
            processor.validate_location(""),
            processor.validate_category(""),
            processor.validate_description(""),
            processor.validate_timestamp(None),
        ]
        
        for is_valid, error in test_cases:
            assert is_valid is False
            assert error is not None
            assert len(error) > 10, "Error message should be descriptive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
