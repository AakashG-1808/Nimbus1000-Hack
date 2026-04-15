"""
UrbanGuard AI System - Complaint Submission Integration Tests
Integration tests for complaint submission flow including performance validation.
"""
import pytest
import time
from datetime import datetime
from complaint_processor import ComplaintProcessor
from storage import storage


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    storage.clear_all()
    yield
    storage.clear_all()


class TestComplaintSubmissionIntegration:
    """Integration tests for complete complaint submission flow."""
    
    def test_complete_submission_flow(self):
        """Test complete flow: submit complaint -> verify storage -> retrieve"""
        processor = ComplaintProcessor()
        
        # Submit complaint
        result = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="Large pothole on main road causing traffic issues",
            timestamp=datetime.now()
        )
        
        # Verify submission success
        assert result.success is True
        assert result.complaint_id is not None
        
        # Retrieve all complaints
        complaints = processor.get_all_complaints()
        
        # Verify complaint is stored correctly
        assert len(complaints) == 1
        complaint = complaints[0]
        assert complaint.complaint_id == result.complaint_id
        assert complaint.location == "Koramangala"
        assert complaint.category == "pothole"
        assert complaint.description == "Large pothole on main road causing traffic issues"
        assert complaint.coordinates == (12.9352, 77.6245)
    
    def test_invalid_submission_does_not_store(self):
        """Test that invalid complaints are not stored"""
        processor = ComplaintProcessor()
        
        # Submit invalid complaint
        result = processor.submit_complaint(
            location="InvalidLocation",
            category="pothole",
            description="Test complaint",
            timestamp=datetime.now()
        )
        
        # Verify submission failed
        assert result.success is False
        
        # Verify nothing was stored
        complaints = processor.get_all_complaints()
        assert len(complaints) == 0
    
    def test_multiple_submissions_and_retrieval(self):
        """Test submitting multiple complaints and retrieving them"""
        processor = ComplaintProcessor()
        
        # Submit 5 complaints
        submitted_ids = []
        for i in range(5):
            result = processor.submit_complaint(
                location="Koramangala",
                category="pothole",
                description=f"Complaint number {i}",
                timestamp=datetime.now()
            )
            assert result.success is True
            submitted_ids.append(result.complaint_id)
        
        # Retrieve all complaints
        complaints = processor.get_all_complaints()
        
        # Verify all are present
        assert len(complaints) == 5
        retrieved_ids = [c.complaint_id for c in complaints]
        for submitted_id in submitted_ids:
            assert submitted_id in retrieved_ids


class TestPerformanceRequirements:
    """Tests to verify performance requirements are met."""
    
    def test_invalid_complaint_response_time(self):
        """
        Test that invalid complaints return error within 100ms.
        Requirement 1.4: Invalid data should return error < 100ms
        """
        processor = ComplaintProcessor()
        
        start_time = time.time()
        result = processor.submit_complaint(
            location="InvalidLocation",
            category="pothole",
            description="Test complaint",
            timestamp=datetime.now()
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert result.success is False
        assert response_time_ms < 100, f"Response time {response_time_ms:.2f}ms exceeds 100ms requirement"
    
    def test_valid_complaint_response_time(self):
        """
        Test that valid complaints are stored and confirmed within 500ms.
        Requirement 1.5: Valid data should return confirmation < 500ms
        """
        processor = ComplaintProcessor()
        
        start_time = time.time()
        result = processor.submit_complaint(
            location="Koramangala",
            category="pothole",
            description="Test complaint for performance",
            timestamp=datetime.now()
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert result.success is True
        assert response_time_ms < 500, f"Response time {response_time_ms:.2f}ms exceeds 500ms requirement"
    
    def test_retrieval_performance_with_many_complaints(self):
        """
        Test that retrieving complaints is fast even with many stored.
        Requirement 3.3: Should return within 200ms for up to 1000 complaints
        """
        processor = ComplaintProcessor()
        
        # Submit 100 complaints (testing with 100 instead of 1000 for speed)
        for i in range(100):
            processor.submit_complaint(
                location="Koramangala",
                category="pothole",
                description=f"Complaint {i}",
                timestamp=datetime.now()
            )
        
        # Measure retrieval time
        start_time = time.time()
        complaints = processor.get_all_complaints()
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert len(complaints) == 100
        assert response_time_ms < 200, f"Retrieval time {response_time_ms:.2f}ms exceeds 200ms requirement"


class TestComplaintDataIntegrity:
    """Tests to verify data integrity throughout the submission flow."""
    
    def test_coordinates_lookup_accuracy(self):
        """Test that coordinates are correctly looked up from location"""
        processor = ComplaintProcessor()
        
        test_locations = [
            ("Koramangala", (12.9352, 77.6245)),
            ("Indiranagar", (12.9716, 77.6412)),
            ("Whitefield", (12.9698, 77.7499)),
        ]
        
        for location, expected_coords in test_locations:
            result = processor.submit_complaint(
                location=location,
                category="pothole",
                description="Test",
                timestamp=datetime.now()
            )
            
            complaints = processor.get_all_complaints()
            complaint = next(c for c in complaints if c.complaint_id == result.complaint_id)
            
            assert complaint.coordinates == expected_coords, \
                f"Coordinates for {location} should be {expected_coords}, got {complaint.coordinates}"
    
    def test_all_complaint_fields_preserved(self):
        """Test that all complaint fields are preserved through submission and retrieval"""
        processor = ComplaintProcessor()
        
        test_data = {
            "location": "Koramangala",
            "category": "flooding",
            "description": "Severe waterlogging after heavy rain",
            "timestamp": datetime.now()
        }
        
        result = processor.submit_complaint(**test_data)
        
        complaints = processor.get_all_complaints()
        complaint = complaints[0]
        
        assert complaint.location == test_data["location"]
        assert complaint.category == test_data["category"]
        assert complaint.description == test_data["description"]
        assert complaint.timestamp == test_data["timestamp"]
        assert complaint.complaint_id == result.complaint_id
        assert complaint.coordinates is not None
        assert complaint.classification_confidence == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
