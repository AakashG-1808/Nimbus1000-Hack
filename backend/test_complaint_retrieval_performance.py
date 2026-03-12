"""
Performance tests for complaint retrieval functionality.
Tests requirement 3.3: < 200ms response time for 1000 complaints
"""
import time
from datetime import datetime, timedelta
from complaint_processor import ComplaintProcessor
from storage import storage


def test_retrieval_performance_with_1000_complaints():
    """
    Test that retrieving complaints meets performance requirement.
    Requirement 3.3: Should return within 200ms for up to 1000 complaints
    """
    # Clear storage
    storage.clear_all()
    
    processor = ComplaintProcessor()
    
    # Submit 1000 complaints
    print(f"\nSubmitting 1000 complaints...")
    start_submit = time.time()
    
    locations = ["Koramangala", "Indiranagar", "Whitefield", "Electronic City", "Jayanagar"]
    categories = ["pothole", "flooding", "traffic", "garbage"]
    
    for i in range(1000):
        processor.submit_complaint(
            location=locations[i % len(locations)],
            category=categories[i % len(categories)],
            description=f"Test complaint {i}",
            timestamp=datetime.now() - timedelta(seconds=i)
        )
    
    submit_time = (time.time() - start_submit) * 1000
    print(f"Submission time for 1000 complaints: {submit_time:.2f}ms")
    
    # Measure retrieval time (run multiple times for accuracy)
    retrieval_times = []
    for run in range(5):
        start_time = time.time()
        complaints = processor.get_all_complaints()
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        retrieval_times.append(response_time_ms)
    
    avg_retrieval_time = sum(retrieval_times) / len(retrieval_times)
    max_retrieval_time = max(retrieval_times)
    min_retrieval_time = min(retrieval_times)
    
    print(f"\nRetrieval performance (1000 complaints):")
    print(f"  Average: {avg_retrieval_time:.2f}ms")
    print(f"  Min: {min_retrieval_time:.2f}ms")
    print(f"  Max: {max_retrieval_time:.2f}ms")
    
    # Verify correctness
    assert len(complaints) == 1000, f"Expected 1000 complaints, got {len(complaints)}"
    
    # Verify sorting (most recent first)
    for i in range(len(complaints) - 1):
        assert complaints[i].timestamp >= complaints[i + 1].timestamp, \
            f"Complaints not sorted correctly at index {i}"
    
    # Verify coordinates are included
    for complaint in complaints:
        assert complaint.coordinates is not None, "Complaint missing coordinates"
        assert len(complaint.coordinates) == 2, "Coordinates should be (lat, lon) tuple"
    
    # Verify performance requirement
    assert max_retrieval_time < 200, \
        f"Max retrieval time {max_retrieval_time:.2f}ms exceeds 200ms requirement"
    
    print(f"\n✓ Performance requirement met: {max_retrieval_time:.2f}ms < 200ms")
    
    # Clean up
    storage.clear_all()


if __name__ == "__main__":
    test_retrieval_performance_with_1000_complaints()
