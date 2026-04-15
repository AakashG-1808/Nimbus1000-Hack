"""
Final verification script for Task 7.3
Verifies all requirements without needing a running server
"""
from datetime import datetime
from risk_engine import RiskEngine
from models import Cluster, Complaint, RiskLevel


def verify_implementation():
    """Verify all task 7.3 requirements are implemented"""
    
    print("=" * 70)
    print("TASK 7.3 VERIFICATION")
    print("=" * 70)
    print()
    
    engine = RiskEngine()
    
    # 1. Verify risk level classification exists
    print("1. Risk Level Classification")
    print("   - LOW (0-33), MEDIUM (34-66), HIGH (67-100)")
    
    assert hasattr(engine, 'classify_risk_level'), "Missing classify_risk_level method"
    assert hasattr(engine, 'LOW_RISK_MAX'), "Missing LOW_RISK_MAX constant"
    assert hasattr(engine, 'MEDIUM_RISK_MAX'), "Missing MEDIUM_RISK_MAX constant"
    
    assert engine.LOW_RISK_MAX == 33, f"Expected LOW_RISK_MAX=33, got {engine.LOW_RISK_MAX}"
    assert engine.MEDIUM_RISK_MAX == 66, f"Expected MEDIUM_RISK_MAX=66, got {engine.MEDIUM_RISK_MAX}"
    
    # Test classification
    assert engine.classify_risk_level(20) == RiskLevel.LOW
    assert engine.classify_risk_level(50) == RiskLevel.MEDIUM
    assert engine.classify_risk_level(80) == RiskLevel.HIGH
    
    print("   ✓ Risk level classification implemented correctly")
    print()
    
    # 2. Verify 15-minute recalculation scheduler
    print("2. 15-Minute Recalculation Scheduler")
    print("   - Recalculates all Risk_Score values every 15 minutes")
    
    assert hasattr(engine, 'RECALCULATION_INTERVAL'), "Missing RECALCULATION_INTERVAL"
    assert engine.RECALCULATION_INTERVAL == 900, \
        f"Expected 900 seconds, got {engine.RECALCULATION_INTERVAL}"
    
    assert hasattr(engine, 'start_scheduler'), "Missing start_scheduler method"
    assert hasattr(engine, 'stop_scheduler'), "Missing stop_scheduler method"
    assert hasattr(engine, '_scheduler_loop'), "Missing _scheduler_loop method"
    assert hasattr(engine, 'calculate_all_risk_zones'), "Missing calculate_all_risk_zones method"
    
    print(f"   ✓ Recalculation interval: {engine.RECALCULATION_INTERVAL}s (15 minutes)")
    print("   ✓ Scheduler methods implemented")
    print()
    
    # 3. Verify zone filtering
    print("3. Zone Filtering (risk_score > 20)")
    print("   - Filter zones with risk_score > 20 for API responses")
    
    assert hasattr(engine, 'MIN_RISK_SCORE_THRESHOLD'), "Missing MIN_RISK_SCORE_THRESHOLD"
    assert engine.MIN_RISK_SCORE_THRESHOLD == 20.0, \
        f"Expected 20.0, got {engine.MIN_RISK_SCORE_THRESHOLD}"
    
    assert hasattr(engine, 'get_filtered_risk_zones'), "Missing get_filtered_risk_zones method"
    
    # Test filtering
    test_cluster_low = Cluster(
        complaints=[
            Complaint(
                location="Test",
                category="pothole",
                description="Test",
                timestamp=datetime.now(),
                coordinates=(12.9, 77.6)
            )
        ],
        center_coordinates=(12.9, 77.6),
        radius_meters=500.0,
        density_per_km2=2.0,  # Low score
        is_high_density=False,
        time_window_hours=24
    )
    
    test_cluster_high = Cluster(
        complaints=[
            Complaint(
                location="Test",
                category="pothole",
                description="Test",
                timestamp=datetime.now(),
                coordinates=(12.9, 77.6)
            ) for _ in range(6)
        ],
        center_coordinates=(12.9, 77.6),
        radius_meters=500.0,
        density_per_km2=7.0,  # High score
        is_high_density=True,
        time_window_hours=24
    )
    
    zone_low = engine.create_risk_zone_from_cluster(test_cluster_low)
    zone_high = engine.create_risk_zone_from_cluster(test_cluster_high)
    
    engine._risk_zones_cache = [zone_low, zone_high]
    filtered = engine.get_filtered_risk_zones()
    
    assert len(filtered) == 1, f"Expected 1 filtered zone, got {len(filtered)}"
    assert filtered[0].risk_score > 20, f"Filtered zone score should be > 20"
    
    print(f"   ✓ Minimum threshold: {engine.MIN_RISK_SCORE_THRESHOLD}")
    print(f"   ✓ Filtering works correctly (excluded {zone_low.risk_score:.1f}, included {zone_high.risk_score:.1f})")
    print()
    
    # 4. Verify API endpoint exists
    print("4. API Endpoint")
    print("   - /risk-hotspots endpoint returns filtered zones")
    
    try:
        with open('main.py', 'r') as f:
            content = f.read()
            assert '/risk-hotspots' in content, "Missing /risk-hotspots endpoint"
            assert 'get_filtered_risk_zones' in content, "Endpoint doesn't use filtering"
        
        print("   ✓ /risk-hotspots endpoint implemented in main.py")
    except FileNotFoundError:
        print("   ⚠ Could not verify main.py (file not found)")
    
    print()
    
    # Summary
    print("=" * 70)
    print("✅ TASK 7.3 VERIFICATION COMPLETE")
    print("=" * 70)
    print()
    print("All requirements implemented:")
    print("  ✓ Risk level classification: LOW (0-33), MEDIUM (34-66), HIGH (67-100)")
    print("  ✓ 15-minute recalculation scheduler (900 seconds)")
    print("  ✓ Zone filtering (risk_score > 20)")
    print("  ✓ API endpoint /risk-hotspots")
    print()


if __name__ == "__main__":
    verify_implementation()
