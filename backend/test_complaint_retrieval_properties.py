"""
Property-based tests for complaint retrieval functionality.
Tests Properties 9 and 10 from the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from complaint_processor import ComplaintProcessor
from storage import storage
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES


# Strategy for generating valid complaints
@st.composite
def valid_complaint_data(draw):
    """Generate valid complaint data for testing"""
    location = draw(st.sampled_from(list(BENGALURU_LOCATIONS.keys())))
    category = draw(st.sampled_from(COMPLAINT_CATEGORIES))
    # Generate non-empty, non-whitespace-only descriptions
    description = draw(st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != ''))
    # Generate timestamps within a reasonable range
    days_ago = draw(st.integers(min_value=0, max_value=365))
    timestamp = datetime.now() - timedelta(days=days_ago)
    
    return {
        "location": location,
        "category": category,
        "description": description,
        "timestamp": timestamp
    }


class TestComplaintRetrievalProperties:
    """Property-based tests for complaint retrieval"""
    
    @pytest.fixture(autouse=True)
    def clear_storage(self):
        """Clear storage before and after each test"""
        storage.clear_all()
        yield
        storage.clear_all()
    
    # Feature: urbanguard-ai-system, Property 9: Complaint Retrieval Sorting
    @given(st.lists(valid_complaint_data(), min_size=2, max_size=20))
    @settings(max_examples=100)
    def test_property_9_complaints_sorted_by_timestamp_descending(self, complaint_list):
        """
        Property 9: Complaint Retrieval Sorting
        
        For any set of complaints retrieved from the Dashboard_API,
        they should be sorted by timestamp in descending order (most recent first).
        
        **Validates: Requirements 3.2**
        """
        # Clear storage for this test iteration
        storage.clear_all()
        
        processor = ComplaintProcessor()
        
        # Submit all complaints
        for complaint_data in complaint_list:
            result = processor.submit_complaint(**complaint_data)
            assert result.success, f"Failed to submit complaint: {result.error_message}"
        
        # Retrieve all complaints
        retrieved_complaints = processor.get_all_complaints()
        
        # Verify we got all complaints
        assert len(retrieved_complaints) == len(complaint_list), \
            "Retrieved complaint count doesn't match submitted count"
        
        # Property: Complaints should be sorted by timestamp descending
        for i in range(len(retrieved_complaints) - 1):
            current_timestamp = retrieved_complaints[i].timestamp
            next_timestamp = retrieved_complaints[i + 1].timestamp
            
            assert current_timestamp >= next_timestamp, \
                f"Complaints not sorted correctly: complaint at index {i} " \
                f"(timestamp {current_timestamp}) should be >= complaint at index {i+1} " \
                f"(timestamp {next_timestamp})"
    
    # Feature: urbanguard-ai-system, Property 10: Complaint Response Completeness
    @given(st.lists(valid_complaint_data(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_property_10_complaints_include_coordinates(self, complaint_list):
        """
        Property 10: Complaint Response Completeness
        
        For any complaint returned by the Dashboard_API,
        it should include location coordinates along with all other complaint fields.
        
        **Validates: Requirements 3.4**
        """
        # Clear storage for this test iteration
        storage.clear_all()
        
        processor = ComplaintProcessor()
        
        # Submit all complaints
        submitted_ids = []
        for complaint_data in complaint_list:
            result = processor.submit_complaint(**complaint_data)
            assert result.success, f"Failed to submit complaint: {result.error_message}"
            submitted_ids.append(result.complaint_id)
        
        # Retrieve all complaints
        retrieved_complaints = processor.get_all_complaints()
        
        # Property: Every complaint must include coordinates
        for complaint in retrieved_complaints:
            # Verify coordinates exist
            assert complaint.coordinates is not None, \
                f"Complaint {complaint.complaint_id} missing coordinates"
            
            # Verify coordinates are a tuple/list of 2 elements
            assert len(complaint.coordinates) == 2, \
                f"Complaint {complaint.complaint_id} coordinates should have 2 elements (lat, lon)"
            
            # Verify coordinates are numeric
            lat, lon = complaint.coordinates
            assert isinstance(lat, (int, float)), \
                f"Latitude should be numeric, got {type(lat)}"
            assert isinstance(lon, (int, float)), \
                f"Longitude should be numeric, got {type(lon)}"
            
            # Verify coordinates are within valid Bengaluru bounds
            # Bengaluru is approximately between 12.8-13.2°N and 77.4-77.8°E
            assert 12.5 <= lat <= 13.5, \
                f"Latitude {lat} outside Bengaluru bounds"
            assert 77.0 <= lon <= 78.0, \
                f"Longitude {lon} outside Bengaluru bounds"
            
            # Verify all other required fields are present
            assert complaint.complaint_id is not None, "Missing complaint_id"
            assert complaint.location is not None, "Missing location"
            assert complaint.category is not None, "Missing category"
            assert complaint.description is not None, "Missing description"
            assert complaint.timestamp is not None, "Missing timestamp"
            
            # Verify complaint_id matches one we submitted
            assert complaint.complaint_id in submitted_ids, \
                f"Retrieved complaint {complaint.complaint_id} was not submitted"
    
    # Additional property: Empty retrieval
    def test_property_empty_storage_returns_empty_list(self):
        """
        Property: When no complaints exist, get_all_complaints returns empty list.
        
        This is a boundary case for Properties 9 and 10.
        """
        processor = ComplaintProcessor()
        
        # Ensure storage is empty
        storage.clear_all()
        
        # Retrieve complaints
        complaints = processor.get_all_complaints()
        
        # Property: Should return empty list, not None or error
        assert complaints == [], \
            f"Expected empty list, got {complaints}"
        assert isinstance(complaints, list), \
            f"Expected list type, got {type(complaints)}"
    
    # Additional property: Single complaint
    @given(valid_complaint_data())
    @settings(max_examples=50)
    def test_property_single_complaint_retrieval(self, complaint_data):
        """
        Property: A single complaint can be retrieved with correct sorting and coordinates.
        
        This is a boundary case for Properties 9 and 10.
        """
        # Clear storage for this test iteration
        storage.clear_all()
        
        processor = ComplaintProcessor()
        
        # Submit single complaint
        result = processor.submit_complaint(**complaint_data)
        assert result.success
        
        # Retrieve complaints
        complaints = processor.get_all_complaints()
        
        # Properties for single complaint
        assert len(complaints) == 1, "Should retrieve exactly one complaint"
        assert complaints[0].complaint_id == result.complaint_id
        assert complaints[0].coordinates is not None
        assert len(complaints[0].coordinates) == 2
        assert complaints[0].timestamp == complaint_data["timestamp"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
