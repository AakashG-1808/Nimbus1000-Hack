"""
Script to view sample simulated complaints
"""
from storage import InMemoryStorage
from simulated_data import initialize_storage_with_simulated_data
from collections import Counter


def display_sample_complaints():
    """Display sample complaints and statistics"""
    storage = InMemoryStorage()
    count = initialize_storage_with_simulated_data(storage)
    
    print(f"{'='*80}")
    print(f"UrbanGuard AI System - Simulated Data Sample")
    print(f"{'='*80}\n")
    
    complaints = storage.get_all_complaints()
    
    # Display statistics
    print(f"Total Complaints: {count}")
    print(f"Locations: {len(set(c.location for c in complaints))}")
    print(f"Categories: {len(set(c.category for c in complaints))}\n")
    
    # Category distribution
    print("Category Distribution:")
    category_counts = Counter(c.category for c in complaints)
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:15s}: {count:2d} complaints")
    
    print()
    
    # Location distribution (top 10)
    print("Top 10 Locations:")
    location_counts = Counter(c.location for c in complaints)
    for location, count in location_counts.most_common(10):
        print(f"  {location:25s}: {count:2d} complaints")
    
    print(f"\n{'='*80}")
    print("Sample Complaints (5 most recent):")
    print(f"{'='*80}\n")
    
    # Display 5 most recent complaints
    for i, complaint in enumerate(complaints[:5], 1):
        print(f"Complaint #{i}")
        print(f"  ID: {complaint.complaint_id}")
        print(f"  Location: {complaint.location}")
        print(f"  Category: {complaint.category}")
        print(f"  Description: {complaint.description}")
        print(f"  Timestamp: {complaint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Coordinates: {complaint.coordinates}")
        print(f"  Confidence: {complaint.classification_confidence:.2f}")
        print()


if __name__ == "__main__":
    display_sample_complaints()
