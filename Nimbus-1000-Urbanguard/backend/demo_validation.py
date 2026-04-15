"""
UrbanGuard AI System - Validation Demo
Demonstrates complaint validation logic
"""
from datetime import datetime
from complaint_processor import ComplaintProcessor


def demo_validation():
    """Demonstrates the complaint validation logic."""
    processor = ComplaintProcessor()
    
    print("=" * 70)
    print("UrbanGuard AI - Complaint Validation Demo")
    print("=" * 70)
    
    # Test 1: Valid complaint
    print("\n1. Testing VALID complaint:")
    print("   Location: Koramangala")
    print("   Category: pothole")
    print("   Description: Large pothole on main road")
    is_valid, error = processor.validate_complaint(
        location="Koramangala",
        category="pothole",
        description="Large pothole on main road",
        timestamp=datetime.now()
    )
    print(f"   Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    # Test 2: Invalid location
    print("\n2. Testing INVALID location:")
    print("   Location: Mumbai")
    print("   Category: pothole")
    is_valid, error = processor.validate_location("Mumbai")
    print(f"   Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    # Test 3: Invalid category
    print("\n3. Testing INVALID category:")
    print("   Location: Koramangala")
    print("   Category: invalid_type")
    is_valid, error = processor.validate_category("invalid_type")
    print(f"   Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    # Test 4: Missing description
    print("\n4. Testing MISSING description:")
    print("   Description: (empty)")
    is_valid, error = processor.validate_description("")
    print(f"   Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    # Test 5: Missing timestamp
    print("\n5. Testing MISSING timestamp:")
    print("   Timestamp: None")
    is_valid, error = processor.validate_timestamp(None)
    print(f"   Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    # Test 6: Coordinates retrieval
    print("\n6. Testing coordinates retrieval:")
    print("   Location: Koramangala")
    coords = processor.get_coordinates("Koramangala")
    print(f"   Coordinates: {coords}")
    print(f"   Latitude: {coords[0]}, Longitude: {coords[1]}")
    
    # Test 7: All supported categories
    print("\n7. All supported categories:")
    from constants import COMPLAINT_CATEGORIES
    for category in COMPLAINT_CATEGORIES:
        is_valid, _ = processor.validate_category(category)
        status = "✓" if is_valid else "✗"
        print(f"   {status} {category}")
    
    # Test 8: Sample of valid locations
    print("\n8. Sample of valid Bengaluru locations:")
    from constants import BENGALURU_LOCATIONS
    sample_locations = list(BENGALURU_LOCATIONS.keys())[:10]
    for location in sample_locations:
        coords = processor.get_coordinates(location)
        print(f"   ✓ {location}: {coords}")
    
    print("\n" + "=" * 70)
    print("Validation Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo_validation()
