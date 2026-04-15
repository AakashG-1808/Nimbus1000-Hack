"""
UrbanGuard AI System - Complaint Submission Unit Tests
Unit tests for complaint submission and storage functionality.
"""
import pytest
from datetime import datetime
from complaint_processor import ComplaintProcessor, ComplaintResult
from storage import storage
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    storage.clear_all()
    yield
    storage.clear_all()


class TestComplaintSubmission:
    """Unit tests for complaint submission functionality."""
    
    def test_submit_valid_complaint_success(self):
        """Test submitting a valid complaint returns success"""
        processor = ComplaintProcessor()
        
        result = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="Large pothole on main road",
            timestamp=datetime.now()
        )
        
        assert result.success is True
        assert result.complaint_id is not None
        assert result.error_message is None
        assert len(result.complaint_id) > 0
    
    def test_submit_complaint_generates_unique_id(self):
        """Test that each complaint gets a unique UUID"""
        processor = ComplaintProcessor()
        
        result1 = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="First complaint",
            timestamp=datetime.now()
        )
        
        result2 = processor.submit_complaint(
            location="Indiranagar",
            category="flooding",
            description="Second complaint",
            timestamp=datetime.now()
        )
        
        assert result1.success is True
        assert result2.success is True
        assert result1.complaint_id != result2.complaint_id
    
    def test_submit_complaint_stores_in_storage(self):
        """Test that submitted complaints are stored"""
        processor = ComplaintProcessor()
        
        result = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="Test complaint",
            timestamp=datetime.now()
        )
        
        assert result.success is True
        
        # Verify complaint is in storage
        complaints = storage.get_all_complaints()
        assert len(complaints) == 1
        assert complaints[0].complaint_id == result.complaint_id
    
    def test_submit_complaint_includes_coordinates(self):
        """Test that submitted complaints include coordinates from location"""
        processor = ComplaintProcessor()
        location = "Koramangala"
        expected_coords = BENGALURU_LOCATIONS[location]
        
        result = processor.submit_complaint(
            location=location,
            category="pothole",
            description="Test complaint",
            timestamp=datetime.now()
        )
        
        assert result.success is True
        
        # Verify complaint has correct coordinates
        complaints = storage.get_all_complaints()
        assert len(complaints) == 1
        assert complaints[0].coordinates == expected_coords
    
    def test_submit_complaint_with_invalid_location(self):
        """Test submitting complaint with invalid location returns error"""
        processor = ComplaintProcessor()
        
        result = processor.submit_complaint(
            location="InvalidCity",
            category="pothole",
            description="Test complaint",
            timestamp=datetime.now()
        )
        
        assert result.success is False
        assert result.complaint_id is None
        assert result.error_message is not None
        assert "Invalid location" in result.error_message
    
    def test_submit_complaint_with_invalid_category(self):
        """Test submitting complaint with invalid category returns error"""
        processor = ComplaintProcessor()
        
        result = processor.submit_complaint(
            location="Koramangala",
            category="invalid_category",
            description="Test complaint",
            timestamp=datetime.now()
        )
        
        assert result.success is False
        assert result.complaint_id is None
        assert result.error_message is not None
        assert "Invalid category" in result.error_message
    
    def test_submit_complaint_with_empty_description(self):
        """Test submitting complaint with empty description returns error"""
        processor = ComplaintProcessor()
        
        result = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="",
            timestamp=datetime.now()
        )
        
        assert result.success is False
        assert result.complaint_id is None
        assert result.error_message is not None
        assert "description" in result.error_message.lower()
    
    def test_submit_complaint_with_none_timestamp(self):
        """Test submitting complaint with None timestamp returns error"""
        processor = ComplaintProcessor()
        
        result = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="Test complaint",
            timestamp=None
        )
        
        assert result.success is False
        assert result.complaint_id is None
        assert result.error_message is not None
        assert "timestamp" in result.error_message.lower()
    
    def test_submit_multiple_complaints(self):
        """Test submitting multiple complaints"""
        processor = ComplaintProcessor()
        
        # Submit 3 complaints
        for i in range(3):
            result = processor.submit_complaint(
                location="Koramangala",
                category="pothole",
                description=f"Complaint {i}",
                timestamp=datetime.now()
            )
            assert result.success is True
        
        # Verify all are stored
        complaints = storage.get_all_complaints()
        assert len(complaints) == 3


class TestGetAllComplaints:
    """Unit tests for retrieving all complaints."""
    
    def test_get_all_complaints_empty(self):
        """Test getting complaints when storage is empty"""
        processor = ComplaintProcessor()
        complaints = processor.get_all_complaints()
        assert complaints == []
    
    def test_get_all_complaints_returns_stored_complaints(self):
        """Test getting all complaints returns stored complaints"""
        processor = ComplaintProcessor()
        
        # Submit 2 complaints
        result1 = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="First complaint",
            timestamp=datetime.now()
        )
        
        result2 = processor.submit_complaint(
            location="Indiranagar",
            category="flooding",
            description="Second complaint",
            timestamp=datetime.now()
        )
        
        # Get all complaints
        complaints = processor.get_all_complaints()
        
        assert len(complaints) == 2
        complaint_ids = [c.complaint_id for c in complaints]
        assert result1.complaint_id in complaint_ids
        assert result2.complaint_id in complaint_ids
    
    def test_get_all_complaints_sorted_by_timestamp_descending(self):
        """Test that complaints are sorted by timestamp descending (most recent first)"""
        processor = ComplaintProcessor()
        
        # Submit complaints with different timestamps
        from datetime import timedelta
        now = datetime.now()
        
        result1 = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="Oldest complaint",
            timestamp=now - timedelta(hours=2)
        )
        
        result2 = processor.submit_complaint(
            location="Indiranagar",
            category="flooding",
            description="Middle complaint",
            timestamp=now - timedelta(hours=1)
        )
        
        result3 = processor.submit_complaint(
            location="Whitefield",
            category="traffic",
            description="Newest complaint",
            timestamp=now
        )
        
        # Get all complaints
        complaints = processor.get_all_complaints()
        
        assert len(complaints) == 3
        # Most recent should be first
        assert complaints[0].complaint_id == result3.complaint_id
        assert complaints[1].complaint_id == result2.complaint_id
        assert complaints[2].complaint_id == result1.complaint_id
    
    def test_get_all_complaints_includes_coordinates(self):
        """Test that retrieved complaints include coordinates"""
        processor = ComplaintProcessor()
        
        result = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="Test complaint",
            timestamp=datetime.now()
        )
        
        complaints = processor.get_all_complaints()
        assert len(complaints) == 1
        assert complaints[0].coordinates is not None
        assert len(complaints[0].coordinates) == 2  # (lat, lon)
        assert isinstance(complaints[0].coordinates[0], float)
        assert isinstance(complaints[0].coordinates[1], float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
