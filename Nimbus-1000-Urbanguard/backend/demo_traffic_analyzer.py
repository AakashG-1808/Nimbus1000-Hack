"""
Demo script for Traffic Analyzer
Demonstrates traffic data generation and scheduling functionality
"""
import time
from datetime import datetime
from traffic_analyzer import get_traffic_analyzer
from models import CongestionLevel


def print_separator():
    """Print a visual separator"""
    print("\n" + "=" * 80 + "\n")


def demo_basic_functionality():
    """Demonstrate basic traffic data retrieval"""
    print("DEMO 1: Basic Traffic Data Retrieval")
    print_separator()
    
    analyzer = get_traffic_analyzer()
    
    # Get traffic data for specific locations
    locations = ["Koramangala", "Indiranagar", "Whitefield", "Electronic City"]
    
    print("Current traffic conditions:\n")
    for location in locations:
        traffic = analyzer.get_traffic_data(location)
        
        # Color code based on congestion level
        if traffic.congestion_level == CongestionLevel.LOW:
            status = "🟢 LOW"
        elif traffic.congestion_level == CongestionLevel.MEDIUM:
            status = "🟡 MEDIUM"
        else:
            status = "🔴 HIGH"
        
        print(f"  {location:20s} - {status:15s} (Score: {traffic.congestion_score:2d})")
    
    print(f"\nTimestamp: {traffic.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def demo_all_locations():
    """Demonstrate getting all traffic data at once"""
    print("DEMO 2: All Locations Traffic Data")
    print_separator()
    
    analyzer = get_traffic_analyzer()
    all_traffic = analyzer.get_all_traffic_data()
    
    # Count by congestion level
    low_count = sum(1 for t in all_traffic.values() if t.congestion_level == CongestionLevel.LOW)
    medium_count = sum(1 for t in all_traffic.values() if t.congestion_level == CongestionLevel.MEDIUM)
    high_count = sum(1 for t in all_traffic.values() if t.congestion_level == CongestionLevel.HIGH)
    
    print(f"Total locations monitored: {len(all_traffic)}")
    print(f"\nCongestion distribution:")
    print(f"  🟢 LOW:    {low_count:2d} locations ({low_count/len(all_traffic)*100:.1f}%)")
    print(f"  🟡 MEDIUM: {medium_count:2d} locations ({medium_count/len(all_traffic)*100:.1f}%)")
    print(f"  🔴 HIGH:   {high_count:2d} locations ({high_count/len(all_traffic)*100:.1f}%)")
    
    # Show high congestion areas
    high_congestion = [
        (loc, data) for loc, data in all_traffic.items()
        if data.congestion_level == CongestionLevel.HIGH
    ]
    
    if high_congestion:
        print(f"\n⚠️  High congestion areas:")
        for location, traffic in high_congestion[:5]:  # Show first 5
            print(f"  - {location} (Score: {traffic.congestion_score})")


def demo_score_mapping():
    """Demonstrate congestion score mapping"""
    print("DEMO 3: Congestion Score Mapping")
    print_separator()
    
    analyzer = get_traffic_analyzer()
    
    print("Congestion Level → Score Mapping:\n")
    print("  LOW    → Score 1  (Minimal traffic)")
    print("  MEDIUM → Score 5  (Moderate traffic)")
    print("  HIGH   → Score 10 (Heavy congestion)")
    
    print("\nExample locations with different levels:\n")
    
    all_traffic = analyzer.get_all_traffic_data()
    
    # Find examples of each level
    for level in [CongestionLevel.LOW, CongestionLevel.MEDIUM, CongestionLevel.HIGH]:
        example = next(
            (loc for loc, data in all_traffic.items() if data.congestion_level == level),
            None
        )
        if example:
            traffic = all_traffic[example]
            print(f"  {example:20s} - {level.value.upper():6s} (Score: {traffic.congestion_score})")


def demo_update_mechanism():
    """Demonstrate traffic data update"""
    print("DEMO 4: Traffic Data Update Mechanism")
    print_separator()
    
    analyzer = get_traffic_analyzer()
    
    # Get initial state
    location = "Koramangala"
    traffic_before = analyzer.get_traffic_data(location)
    
    print(f"Before update:")
    print(f"  Location: {traffic_before.location}")
    print(f"  Level: {traffic_before.congestion_level.value.upper()}")
    print(f"  Score: {traffic_before.congestion_score}")
    print(f"  Timestamp: {traffic_before.timestamp.strftime('%H:%M:%S')}")
    
    print("\nUpdating traffic data...")
    time.sleep(0.5)  # Small delay for visual effect
    
    analyzer.update_traffic_data()
    
    # Get updated state
    traffic_after = analyzer.get_traffic_data(location)
    
    print(f"\nAfter update:")
    print(f"  Location: {traffic_after.location}")
    print(f"  Level: {traffic_after.congestion_level.value.upper()}")
    print(f"  Score: {traffic_after.congestion_score}")
    print(f"  Timestamp: {traffic_after.timestamp.strftime('%H:%M:%S')}")
    
    if traffic_before.congestion_level != traffic_after.congestion_level:
        print(f"\n✓ Congestion level changed: {traffic_before.congestion_level.value} → {traffic_after.congestion_level.value}")
    else:
        print(f"\n✓ Congestion level remained: {traffic_after.congestion_level.value}")


def demo_performance():
    """Demonstrate response time performance"""
    print("DEMO 5: Performance Test")
    print_separator()
    
    analyzer = get_traffic_analyzer()
    
    print("Testing response time (requirement: < 50ms):\n")
    
    locations = ["Koramangala", "Indiranagar", "Whitefield", "HSR Layout", "BTM Layout"]
    
    for location in locations:
        start_time = time.time()
        traffic = analyzer.get_traffic_data(location)
        elapsed_ms = (time.time() - start_time) * 1000
        
        status = "✓" if elapsed_ms < 50 else "✗"
        print(f"  {status} {location:20s} - {elapsed_ms:.2f}ms")
    
    # Test get_all_traffic_data
    start_time = time.time()
    all_traffic = analyzer.get_all_traffic_data()
    elapsed_ms = (time.time() - start_time) * 1000
    
    status = "✓" if elapsed_ms < 50 else "✗"
    print(f"\n  {status} get_all_traffic_data() - {elapsed_ms:.2f}ms ({len(all_traffic)} locations)")


def demo_scheduler():
    """Demonstrate background scheduler"""
    print("DEMO 6: Background Scheduler")
    print_separator()
    
    print("Traffic Analyzer uses a background scheduler to update data every 10 minutes.")
    print("\nScheduler configuration:")
    print(f"  Update interval: 10 minutes (600 seconds)")
    print(f"  Auto-start: Enabled by default")
    print(f"  Thread: Daemon thread (non-blocking)")
    
    analyzer = get_traffic_analyzer()
    
    if analyzer._scheduler_running:
        print("\n✓ Scheduler is currently running")
        print("  Traffic data will be automatically refreshed every 10 minutes")
    else:
        print("\n✗ Scheduler is not running")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print(" " * 20 + "TRAFFIC ANALYZER DEMONSTRATION")
    print("=" * 80)
    
    try:
        demo_basic_functionality()
        time.sleep(1)
        
        demo_all_locations()
        time.sleep(1)
        
        demo_score_mapping()
        time.sleep(1)
        
        demo_update_mechanism()
        time.sleep(1)
        
        demo_performance()
        time.sleep(1)
        
        demo_scheduler()
        
        print_separator()
        print("✓ All demonstrations completed successfully!")
        print("\nKey Features:")
        print("  • Simulated traffic data for 40+ Bengaluru locations")
        print("  • Three congestion levels: LOW (1), MEDIUM (5), HIGH (10)")
        print("  • Background scheduler updates every 10 minutes")
        print("  • Response time < 50ms (cached data)")
        print("  • Thread-safe concurrent access")
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        raise


if __name__ == "__main__":
    main()
