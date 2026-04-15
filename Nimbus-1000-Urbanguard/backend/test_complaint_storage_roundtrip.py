"""
UrbanGuard AI System - Complaint Storage Round-Trip Property-Based Tests
Property-based tests using Hypothesis to validate complaint storage and retrieval.

These tests run with minimum 100 iterations to ensure correctness across a wide range of inputs.
"""
import pytest
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st
from complaint_processor import ComplaintProcessor
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES
from storage import storage


# Custom strategies for generating test data
def valid_locations():
    """Strategy for generating valid Bengaluru locations."""
    return st.sampled_from(list(BENGALURU_LOCATIONS.keys()))


def valid_categories():
    """Strategy for generating valid complaint categories."""
    return st.sampled_from(COMPLAINT_CATEGORIES)


def valid_descriptions():
    """Strategy for generating valid descriptions."""
    return st.text(min_size=1, max_size=500).filter(lambda x: x.strip() != "")


def valid_timestamps():
    """Strategy for generating valid datetime objects."""
    # Generate timestamps within a reasonable range (past year to future week)
    return st.datetimes(
        min_value=datetime.now() - timedelta(days=365),
        max_value=datetime.now() + timedelta(days=7)
    )


# Property 5: Valid Complaint Storage Round-Trip
# **Validates: Requirements 1.5**
class TestComplaintStorageRoundTrip:
    """Property-based tests for complaint storage and retrieval."""
    
    def setup_method(self):
        """Clear storage before each test"""
        storage.clear_all()
    
    @settings(max_examples=100)
    @given(
        location=valid_locations(),
        category=valid_categories(),
        description=valid_descriptions(),
        timestamp=valid_timestamps()
    )
    def test_valid_complaint_storage_roundtrip(self, location, category, description, timestamp):
        """
        Property 5: Valid Complaint Storage Round-Trip
        
        For any valid complaint, if it is submitted to the Complaint_Processor, 
        then retrieving all complaints should include that complaint with matching data.
        
        **Validates: Requirements 1.5**
        """
        processor = ComplaintProcessor()
        
        # Submit the complaint
        result = processor.submit_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        # Submission should succeed
        assert result.success is True, f"Valid complaint should be accepted: {result.error_message}"
        assert result.complaint_id is not None, "Complaint ID should be generated"
        assert result.error_message is None, "Error message should be None for valid complaint"
        
        # Retrieve all complaints
        all_complaints = processor.get_all_complaints()
        
        # The submitted complaint should be in the retrieved list
        assert len(all_complaints) > 0, "Retrieved complaints list should not be empty"
        
        # Find the complaint by ID
        retrieved_complaint = None
        for complaint in all_complaints:
            if complaint.complaint_id == result.complaint_id:
                retrieved_complaint = complaint
                break
        
        # Verify the complaint was found
        assert retrieved_complaint is not None, \
            f"Submitted complaint with ID {result.complaint_id} should be retrievable"
        
        # Verify all fields match
        assert retrieved_complaint.location == location, \
            f"Location should match: expected '{location}', got '{retrieved_complaint.location}'"
        assert retrieved_complaint.category == category, \
            f"Category should match: expected '{category}', got '{retrieved_complaint.category}'"
        assert retrieved_complaint.description == description, \
            f"Description should match: expected '{description}', got '{retrieved_complaint.description}'"
        assert retrieved_complaint.timestamp == timestamp, \
            f"Timestamp should match: expected '{timestamp}', got '{retrieved_complaint.timestamp}'"
        
        # Verify coordinates are set correctly
        expected_coordinates = BENGALURU_LOCATIONS[location]
        assert retrieved_complaint.coordinates == expected_coordinates, \
            f"Coordinates should match location: expected {expected_coordinates}, got {retrieved_complaint.coordinates}"
        
        # Verify complaint_id matches
        assert retrieved_complaint.complaint_id == result.complaint_id, \
            f"Complaint ID should match: expected '{result.complaint_id}', got '{retrieved_complaint.complaint_id}'"
    
    @settings(max_examples=100)
    @given(
        complaints=st.lists(
            st.tuples(
                valid_locations(),
                valid_categories(),
                valid_descriptions(),
                valid_timestamps()
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_multiple_complaints_storage_roundtrip(self, complaints):
        """
        Property 5 (Multiple Complaints): Multiple valid complaints storage round-trip
        
        For any list of valid complaints, if they are all submitted to the 
        Complaint_Processor, then retrieving all complaints should include all 
        of them with matching data.
        
        **Validates: Requirements 1.5**
        """
        processor = ComplaintProcessor()
        submitted_ids = []
        
        # Submit all complaints
        for location, category, description, timestamp in complaints:
            result = processor.submit_complaint(
                location=location,
                category=category,
                description=description,
                timestamp=timestamp
            )
            assert result.success is True, "All valid complaints should be accepted"
            submitted_ids.append(result.complaint_id)
        
        # Retrieve all complaints
        all_complaints = processor.get_all_complaints()
        
        # All submitted complaints should be retrievable
        assert len(all_complaints) >= len(complaints), \
            f"Should retrieve at least {len(complaints)} complaints, got {len(all_complaints)}"
        
        # Verify all submitted IDs are present
        retrieved_ids = {c.complaint_id for c in all_complaints}
        for submitted_id in submitted_ids:
            assert submitted_id in retrieved_ids, \
                f"Submitted complaint {submitted_id} should be retrievable"
        
        # Verify data integrity for each complaint
        for i, (location, category, description, timestamp) in enumerate(complaints):
            complaint_id = submitted_ids[i]
            retrieved = next(c for c in all_complaints if c.complaint_id == complaint_id)
            
            assert retrieved.location == location, "Location should match"
            assert retrieved.category == category, "Category should match"
            assert retrieved.description == description, "Description should match"
            assert retrieved.timestamp == timestamp, "Timestamp should match"
    
    @settings(max_examples=100)
    @given(
        location=valid_locations(),
        category=valid_categories(),
        description=valid_descriptions(),
        timestamp=valid_timestamps()
    )
    def test_complaint_coordinates_included(self, location, category, description, timestamp):
        """
        Property 5 (Coordinates): Retrieved complaints include coordinates
        
        For any valid complaint submitted, the retrieved complaint should include 
        location coordinates for map visualization.
        
        **Validates: Requirements 1.5 and 3.4**
        """
        processor = ComplaintProcessor()
        
        # Submit complaint
        result = processor.submit_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        assert result.success is True, "Valid complaint should be accepted"
        
        # Retrieve complaints
        all_complaints = processor.get_all_complaints()
        retrieved = next(c for c in all_complaints if c.complaint_id == result.complaint_id)
        
        # Verify coordinates are present and valid
        assert retrieved.coordinates is not None, "Coordinates should not be None"
        assert isinstance(retrieved.coordinates, tuple), "Coordinates should be a tuple"
        assert len(retrieved.coordinates) == 2, "Coordinates should have 2 elements (lat, lon)"
        
        lat, lon = retrieved.coordinates
        assert isinstance(lat, (int, float)), "Latitude should be numeric"
        assert isinstance(lon, (int, float)), "Longitude should be numeric"
        
        # Verify coordinates match the location
        expected_coordinates = BENGALURU_LOCATIONS[location]
        assert retrieved.coordinates == expected_coordinates, \
            f"Coordinates should match location: expected {expected_coordinates}, got {retrieved.coordinates}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
