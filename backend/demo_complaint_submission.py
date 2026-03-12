"""
UrbanGuard AI System - Complaint Submission Demo
Demonstrates the complaint submission and retrieval functionality.
"""
from datetime import datetime, timedelta
from complaint_processor import ComplaintProcessor
from storage import storage


def demo_complaint_submission():
    """Demonstrate complaint submission and retrieval."""
    print("=" * 70)
    print("UrbanGuard AI - Complaint Submission Demo")
    print("=" * 70)
    print()
    
    # Clear storage for clean demo
    storage.clear_all()
    
    processor = ComplaintProcessor()
    
    # Demo 1: Submit valid complaints
    print("1. Submitting Valid Complaints")
    print("-" * 70)
    
    complaints_data = [
        {
            "location": "Koramangala",
            "category": "pothole",
            "description": "Large pothole on main road causing traffic issues",
            "timestamp": datetime.now() - timedelta(hours=2)
        },
        {
            "location": "Indiranagar",
            "category": "flooding",
            "description": "Severe waterlogging after heavy rain",
            "timestamp": datetime.now() - timedelta(hours=1)
        },
        {
            "location": "Whitefield",
            "category": "traffic",
            "description": "Heavy traffic congestion during peak hours",
            "timestamp": datetime.now()
        }
    ]
    
    for data in complaints_data:
        result = processor.submit_complaint(**data)
        if result.success:
            print(f"✓ Complaint submitted successfully")
            print(f"  ID: {result.complaint_id}")
            print(f"  Location: {data['location']}")
            print(f"  Category: {data['category']}")
            print(f"  Description: {data['description'][:50]}...")
            print()
        else:
            print(f"✗ Failed: {result.error_message}")
            print()
    
    # Demo 2: Submit invalid complaint
    print("\n2. Submitting Invalid Complaint (Invalid Location)")
    print("-" * 70)
    
    result = processor.submit_complaint(
        location="InvalidCity",
        category="pothole",
        description="Test complaint",
        timestamp=datetime.now()
    )
    
    if result.success:
        print(f"✓ Complaint submitted: {result.complaint_id}")
    else:
        print(f"✗ Validation failed: {result.error_message}")
    
    # Demo 3: Submit invalid complaint (invalid category)
    print("\n3. Submitting Invalid Complaint (Invalid Category)")
    print("-" * 70)
    
    result = processor.submit_complaint(
        location="Koramangala",
        category="invalid_category",
        description="Test complaint",
        timestamp=datetime.now()
    )
    
    if result.success:
        print(f"✓ Complaint submitted: {result.complaint_id}")
    else:
        print(f"✗ Validation failed: {result.error_message}")
    
    # Demo 4: Retrieve all complaints
    print("\n4. Retrieving All Complaints (Sorted by Timestamp Descending)")
    print("-" * 70)
    
    all_complaints = processor.get_all_complaints()
    print(f"Total complaints in storage: {len(all_complaints)}")
    print()
    
    for i, complaint in enumerate(all_complaints, 1):
        print(f"Complaint #{i}")
        print(f"  ID: {complaint.complaint_id}")
        print(f"  Location: {complaint.location}")
        print(f"  Coordinates: {complaint.coordinates}")
        print(f"  Category: {complaint.category}")
        print(f"  Description: {complaint.description}")
        print(f"  Timestamp: {complaint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Confidence: {complaint.classification_confidence}")
        print()
    
    # Demo 5: Performance test
    print("\n5. Performance Test")
    print("-" * 70)
    
    import time
    
    # Test invalid complaint response time
    start = time.time()
    result = processor.submit_complaint(
        location="InvalidLocation",
        category="pothole",
        description="Test",
        timestamp=datetime.now()
    )
    invalid_time = (time.time() - start) * 1000
    
    print(f"Invalid complaint response time: {invalid_time:.2f}ms")
    print(f"Requirement: < 100ms - {'✓ PASS' if invalid_time < 100 else '✗ FAIL'}")
    print()
    
    # Test valid complaint response time
    start = time.time()
    result = processor.submit_complaint(
        location="Koramangala",
        category="pothole",
        description="Performance test complaint",
        timestamp=datetime.now()
    )
    valid_time = (time.time() - start) * 1000
    
    print(f"Valid complaint response time: {valid_time:.2f}ms")
    print(f"Requirement: < 500ms - {'✓ PASS' if valid_time < 500 else '✗ FAIL'}")
    print()
    
    # Test retrieval performance
    start = time.time()
    complaints = processor.get_all_complaints()
    retrieval_time = (time.time() - start) * 1000
    
    print(f"Retrieval time for {len(complaints)} complaints: {retrieval_time:.2f}ms")
    print(f"Requirement: < 200ms for up to 1000 complaints - {'✓ PASS' if retrieval_time < 200 else '✗ FAIL'}")
    
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo_complaint_submission()
