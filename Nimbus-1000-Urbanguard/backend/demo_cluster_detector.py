"""
Demo script for Cluster Detector
Demonstrates geographic clustering with sample Bengaluru complaints
"""
from datetime import datetime, timedelta
from cluster_detector import ClusterDetector
from models import Complaint
from constants import BENGALURU_LOCATIONS


def main():
    print("=" * 70)
    print("UrbanGuard AI - Cluster Detector Demo")
    print("=" * 70)
    print()
    
    # Create sample complaints in different areas
    now = datetime.now()
    
    complaints = [
        # Cluster 1: Koramangala area (5 complaints - high density)
        Complaint(
            location="Koramangala",
            category="pothole",
            description="Large pothole on main road",
            timestamp=now - timedelta(hours=2),
            coordinates=BENGALURU_LOCATIONS["Koramangala"]
        ),
        Complaint(
            location="Koramangala",
            category="pothole",
            description="Road damage near junction",
            timestamp=now - timedelta(hours=4),
            coordinates=(12.9360, 77.6250)  # ~100m from center
        ),
        Complaint(
            location="Koramangala",
            category="streetlight",
            description="Streetlight not working",
            timestamp=now - timedelta(hours=6),
            coordinates=(12.9345, 77.6240)  # ~100m from center
        ),
        Complaint(
            location="Koramangala",
            category="garbage",
            description="Garbage pile on street",
            timestamp=now - timedelta(hours=8),
            coordinates=(12.9355, 77.6255)  # ~100m from center
        ),
        Complaint(
            location="Koramangala",
            category="pothole",
            description="Another pothole nearby",
            timestamp=now - timedelta(hours=10),
            coordinates=(12.9348, 77.6248)  # ~100m from center
        ),
        
        # Cluster 2: Indiranagar area (3 complaints - low density)
        Complaint(
            location="Indiranagar",
            category="flooding",
            description="Water logging after rain",
            timestamp=now - timedelta(hours=3),
            coordinates=BENGALURU_LOCATIONS["Indiranagar"]
        ),
        Complaint(
            location="Indiranagar",
            category="flooding",
            description="Drainage overflow",
            timestamp=now - timedelta(hours=5),
            coordinates=(12.9720, 77.6420)  # ~100m from center
        ),
        Complaint(
            location="Indiranagar",
            category="traffic",
            description="Traffic congestion",
            timestamp=now - timedelta(hours=7),
            coordinates=(12.9710, 77.6405)  # ~100m from center
        ),
        
        # Isolated complaint: Whitefield (far from others)
        Complaint(
            location="Whitefield",
            category="traffic",
            description="Heavy traffic jam",
            timestamp=now - timedelta(hours=1),
            coordinates=BENGALURU_LOCATIONS["Whitefield"]
        ),
        
        # Old complaint (outside 24h window)
        Complaint(
            location="Koramangala",
            category="pothole",
            description="Old complaint - should be filtered",
            timestamp=now - timedelta(hours=30),
            coordinates=BENGALURU_LOCATIONS["Koramangala"]
        ),
    ]
    
    print(f"Total complaints: {len(complaints)}")
    print(f"Recent complaints (within 24h): {len([c for c in complaints if c.timestamp >= now - timedelta(hours=24)])}")
    print()
    
    # Initialize cluster detector
    detector = ClusterDetector(radius_meters=500, time_window_hours=24)
    
    print("Clustering Parameters:")
    print(f"  Radius: {detector.radius_meters}m")
    print(f"  Time Window: {detector.time_window_hours} hours")
    print(f"  High-Density Threshold: 5+ complaints")
    print()
    
    # Detect clusters
    print("Detecting clusters...")
    clusters = detector.detect_clusters(complaints)
    print(f"Found {len(clusters)} clusters")
    print()
    
    # Display cluster details
    for i, cluster in enumerate(clusters, 1):
        print(f"Cluster {i}:")
        print(f"  Center: ({cluster.center_coordinates[0]:.4f}, {cluster.center_coordinates[1]:.4f})")
        print(f"  Complaints: {len(cluster.complaints)}")
        print(f"  Density: {cluster.density_per_km2:.2f} complaints/km²")
        print(f"  High-Density: {'YES' if cluster.is_high_density else 'NO'}")
        print(f"  Radius: {cluster.radius_meters}m")
        print()
        
        # Show complaint details
        print("  Complaint Details:")
        for complaint in cluster.complaints:
            age_hours = (now - complaint.timestamp).total_seconds() / 3600
            print(f"    - {complaint.location}: {complaint.category} ({age_hours:.1f}h ago)")
            print(f"      \"{complaint.description}\"")
        print()
    
    # Demonstrate Haversine distance calculation
    print("=" * 70)
    print("Haversine Distance Examples:")
    print("=" * 70)
    print()
    
    koramangala = BENGALURU_LOCATIONS["Koramangala"]
    indiranagar = BENGALURU_LOCATIONS["Indiranagar"]
    whitefield = BENGALURU_LOCATIONS["Whitefield"]
    
    dist1 = detector.haversine_distance(koramangala, indiranagar)
    dist2 = detector.haversine_distance(koramangala, whitefield)
    dist3 = detector.haversine_distance(indiranagar, whitefield)
    
    print(f"Koramangala to Indiranagar: {dist1:.2f}m ({dist1/1000:.2f}km)")
    print(f"Koramangala to Whitefield: {dist2:.2f}m ({dist2/1000:.2f}km)")
    print(f"Indiranagar to Whitefield: {dist3:.2f}m ({dist3/1000:.2f}km)")
    print()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
