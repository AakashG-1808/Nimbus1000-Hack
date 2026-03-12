"""
Demo script for Cluster Detector with 15-minute recalculation scheduler
Demonstrates density calculation, high-density flagging, and automatic recalculation
"""
import time
from datetime import datetime, timedelta
from cluster_detector import ClusterDetector
from models import Complaint
from constants import BENGALURU_LOCATIONS


def create_sample_complaints():
    """Create sample complaints for demonstration"""
    now = datetime.now()
    complaints = []
    
    # High-density cluster in Koramangala (6 complaints)
    print("\n📍 Creating high-density cluster in Koramangala (6 complaints)...")
    for i in range(6):
        complaint = Complaint(
            location="Koramangala",
            category="pothole",
            description=f"Pothole complaint {i+1}",
            timestamp=now - timedelta(hours=i),
            coordinates=BENGALURU_LOCATIONS["Koramangala"]
        )
        complaints.append(complaint)
    
    # Low-density cluster in Indiranagar (3 complaints)
    print("📍 Creating low-density cluster in Indiranagar (3 complaints)...")
    for i in range(3):
        complaint = Complaint(
            location="Indiranagar",
            category="flooding",
            description=f"Flooding complaint {i+1}",
            timestamp=now - timedelta(hours=i),
            coordinates=BENGALURU_LOCATIONS["Indiranagar"]
        )
        complaints.append(complaint)
    
    # Single complaint in Whitefield
    print("📍 Creating single complaint in Whitefield...")
    complaint = Complaint(
        location="Whitefield",
        category="traffic",
        description="Traffic congestion",
        timestamp=now,
        coordinates=BENGALURU_LOCATIONS["Whitefield"]
    )
    complaints.append(complaint)
    
    return complaints


def main():
    """Demonstrate cluster detector with scheduler"""
    print("=" * 70)
    print("🚀 Cluster Detector Scheduler Demo")
    print("=" * 70)
    
    # Create sample complaints
    complaints = create_sample_complaints()
    
    # Create callback function to retrieve complaints
    def get_complaints():
        return complaints
    
    # Initialize cluster detector with scheduler
    print("\n⚙️  Initializing ClusterDetector with 15-minute scheduler...")
    detector = ClusterDetector(
        radius_meters=500.0,
        time_window_hours=24,
        auto_start=True,
        get_complaints_callback=get_complaints
    )
    
    print(f"✓ Scheduler started (recalculation interval: {detector.RECALCULATION_INTERVAL}s)")
    
    # Wait for initial recalculation
    time.sleep(1)
    
    # Get cached clusters
    print("\n📊 Retrieving cached clusters...")
    clusters = detector.get_cached_clusters()
    
    print(f"\n✓ Found {len(clusters)} clusters:")
    print("-" * 70)
    
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i}:")
        print(f"  📍 Center: ({cluster.center_coordinates[0]:.4f}, {cluster.center_coordinates[1]:.4f})")
        print(f"  📏 Radius: {cluster.radius_meters}m")
        print(f"  📝 Complaints: {len(cluster.complaints)}")
        print(f"  📈 Density: {cluster.density_per_km2:.2f} complaints/km²")
        print(f"  🚨 High-density: {'YES' if cluster.is_high_density else 'NO'}")
        print(f"  ⏰ Time window: {cluster.time_window_hours}h")
        
        # Show complaint details
        print(f"  📋 Complaint details:")
        for complaint in cluster.complaints:
            print(f"     - {complaint.location}: {complaint.category} ({complaint.description})")
    
    print("\n" + "=" * 70)
    print("📊 Summary:")
    print("=" * 70)
    
    total_complaints = sum(len(c.complaints) for c in clusters)
    high_density_count = sum(1 for c in clusters if c.is_high_density)
    
    print(f"  Total clusters: {len(clusters)}")
    print(f"  Total complaints: {total_complaints}")
    print(f"  High-density clusters: {high_density_count}")
    print(f"  Low-density clusters: {len(clusters) - high_density_count}")
    
    # Demonstrate density calculation
    print("\n" + "=" * 70)
    print("🔬 Density Calculation Details:")
    print("=" * 70)
    
    for i, cluster in enumerate(clusters, 1):
        radius_km = cluster.radius_meters / 1000.0
        area_km2 = 3.14159 * (radius_km ** 2)
        print(f"\nCluster {i}:")
        print(f"  Radius: {cluster.radius_meters}m = {radius_km}km")
        print(f"  Area: π × {radius_km}² = {area_km2:.4f} km²")
        print(f"  Complaints: {len(cluster.complaints)}")
        print(f"  Density: {len(cluster.complaints)} / {area_km2:.4f} = {cluster.density_per_km2:.2f} complaints/km²")
        print(f"  High-density threshold: 5+ complaints → {cluster.is_high_density}")
    
    # Demonstrate scheduler behavior
    print("\n" + "=" * 70)
    print("⏰ Scheduler Behavior:")
    print("=" * 70)
    print(f"  Recalculation interval: {detector.RECALCULATION_INTERVAL}s (15 minutes)")
    print(f"  Scheduler running: {detector._scheduler_running}")
    print(f"  Next recalculation: in {detector.RECALCULATION_INTERVAL}s")
    print("\n  The scheduler will automatically recalculate clusters every 15 minutes")
    print("  to ensure risk zones are always up-to-date with the latest complaints.")
    
    # Stop scheduler
    print("\n🛑 Stopping scheduler...")
    detector.stop_scheduler()
    print("✓ Scheduler stopped")
    
    print("\n" + "=" * 70)
    print("✅ Demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
