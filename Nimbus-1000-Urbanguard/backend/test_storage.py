"""
Test script to verify in-memory storage and simulated data initialization
"""
from storage import InMemoryStorage
from simulated_data import initialize_storage_with_simulated_data, generate_clustered_complaints
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES


def test_storage_initialization():
    """Test that storage initializes with 40+ complaints"""
    storage = InMemoryStorage()
    count = initialize_storage_with_simulated_data(storage)
    
    print(f"✓ Initialized storage with {count} complaints")
    assert count >= 40, f"Expected at least 40 complaints, got {count}"
    
    # Verify complaints are stored
    complaints = storage.get_all_complaints()
    assert len(complaints) == count, f"Expected {count} complaints in storage, got {len(complaints)}"
    print(f"✓ All {count} complaints stored successfully")
    
    return storage


def test_complaint_properties(storage):
    """Test that complaints have valid properties"""
    complaints = storage.get_all_complaints()
    
    for complaint in complaints:
        # Check location is valid
        assert complaint.location in BENGALURU_LOCATIONS, \
            f"Invalid location: {complaint.location}"
        
        # Check category is valid
        assert complaint.category in COMPLAINT_CATEGORIES, \
            f"Invalid category: {complaint.category}"
        
        # Check coordinates match location
        expected_coords = BENGALURU_LOCATIONS[complaint.location]
        assert complaint.coordinates == expected_coords, \
            f"Coordinates mismatch for {complaint.location}"
        
        # Check description is not empty
        assert len(complaint.description) > 0, "Empty description"
        
        # Check confidence is in valid range
        assert 0.0 <= complaint.classification_confidence <= 1.0, \
            f"Invalid confidence: {complaint.classification_confidence}"
    
    print(f"✓ All complaints have valid properties")


def test_complaint_sorting(storage):
    """Test that complaints are sorted by timestamp descending"""
    complaints = storage.get_all_complaints()
    
    for i in range(len(complaints) - 1):
        assert complaints[i].timestamp >= complaints[i + 1].timestamp, \
            "Complaints not sorted by timestamp descending"
    
    print(f"✓ Complaints sorted correctly by timestamp")


def test_location_distribution(storage):
    """Test that complaints are distributed across multiple locations"""
    complaints = storage.get_all_complaints()
    locations = set(c.location for c in complaints)
    
    print(f"✓ Complaints distributed across {len(locations)} different locations")
    assert len(locations) >= 10, f"Expected complaints in at least 10 locations, got {len(locations)}"


def test_category_distribution(storage):
    """Test that complaints cover multiple categories"""
    complaints = storage.get_all_complaints()
    categories = set(c.category for c in complaints)
    
    print(f"✓ Complaints cover {len(categories)} different categories")
    assert len(categories) >= 5, f"Expected at least 5 categories, got {len(categories)}"


def test_clustered_complaints():
    """Test generation of clustered complaints"""
    location = "Koramangala"
    category = "pothole"
    count = 5
    
    complaints = generate_clustered_complaints(location, category, count)
    
    assert len(complaints) == count, f"Expected {count} complaints, got {len(complaints)}"
    
    # All should be at same location
    for complaint in complaints:
        assert complaint.location == location, f"Expected {location}, got {complaint.location}"
        assert complaint.category == category, f"Expected {category}, got {complaint.category}"
    
    print(f"✓ Generated {count} clustered complaints at {location}")


def test_storage_thread_safety():
    """Test that storage operations are thread-safe"""
    from threading import Thread
    from models import Complaint
    from datetime import datetime
    
    storage = InMemoryStorage()
    
    def add_complaints():
        for i in range(10):
            complaint = Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test complaint {i}",
                timestamp=datetime.now(),
                coordinates=(12.9352, 77.6245)
            )
            storage.add_complaint(complaint)
    
    # Create multiple threads
    threads = [Thread(target=add_complaints) for _ in range(5)]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Should have 50 complaints (5 threads × 10 complaints)
    assert storage.get_complaint_count() == 50, \
        f"Expected 50 complaints, got {storage.get_complaint_count()}"
    
    print(f"✓ Storage is thread-safe")


if __name__ == "__main__":
    print("Testing in-memory storage and simulated data...\n")
    
    # Test storage initialization
    storage = test_storage_initialization()
    
    # Test complaint properties
    test_complaint_properties(storage)
    
    # Test sorting
    test_complaint_sorting(storage)
    
    # Test distribution
    test_location_distribution(storage)
    test_category_distribution(storage)
    
    # Test clustered complaints
    test_clustered_complaints()
    
    # Test thread safety
    test_storage_thread_safety()
    
    print("\n✅ All tests passed!")
