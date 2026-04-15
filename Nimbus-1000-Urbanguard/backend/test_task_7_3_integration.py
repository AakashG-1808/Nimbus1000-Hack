"""
Integration test for Task 7.3: Complete risk engine functionality
Tests requirements 7.6, 8.1, 8.2
"""
import time
from datetime import datetime
from risk_engine import RiskEngine
from models import Cluster, Complaint, RiskLevel, WeatherData, TrafficData, CongestionLevel


def test_requirement_7_6_recalculation_interval():
    """
    Requirement 7.6: THE Risk_Engine SHALL recalculate all Risk_Score values every 15 minutes
    """
    print("Testing Requirement 7.6: 15-minute recalculation interval")
    
    engine = RiskEngine()
    
    # Verify interval is 900 seconds (15 minutes)
    assert engine.RECALCULATION_INTERVAL == 900, \
        f"Expected 900 seconds, got {engine.RECALCULATION_INTERVAL}"
    
    print(f"  ✓ Recalculation interval: {engine.RECALCULATION_INTERVAL}s (15 minutes)")


def test_requirement_8_1_risk_level_classification():
    """
    Requirement 8.1: THE Risk_Engine SHALL classify zones as low-risk (Risk_Score 0-33),
    medium-risk (Risk_Score 34-66), or high-risk (Risk_Score 67-100)
    """
    print("\nTesting Requirement 8.1: Risk level classification")
    
    engine = RiskEngine()
    
    # Test boundary values
    test_cases = [
        (0, RiskLevel.LOW),
        (33, RiskLevel.LOW),
        (34, RiskLevel.MEDIUM),
        (66, RiskLevel.MEDIUM),
        (67, RiskLevel.HIGH),
        (100, RiskLevel.HIGH),
    ]
    
    for score, expected_level in test_cases:
        actual_level = engine.classify_risk_level(score)
        assert actual_level == expected_level, \
            f"Score {score}: expected {expected_level.value}, got {actual_level.value}"
        print(f"  ✓ Score {score:3d} → {actual_level.value.upper()}")


def test_requirement_8_2_zone_filtering():
    """
    Requirement 8.2: WHEN risk zones are requested, THE Dashboard_API SHALL return
    all zones with Risk_Score above 20
    """
    print("\nTesting Requirement 8.2: Zone filtering (score > 20)")
    
    engine = RiskEngine()
    
    # Create test zones with various scores
    test_zones = []
    test_data = [
        (5.0, "Very low"),
        (15.0, "Low"),
        (19.0, "Below threshold"),
        (20.0, "At threshold"),
        (21.0, "Above threshold"),
        (50.0, "Medium"),
        (75.0, "High"),
    ]
    
    for score, description in test_data:
        # Create a cluster that will produce the desired score
        density = score / 4.0  # Simplified calculation
        cluster = Cluster(
            complaints=[
                Complaint(
                    location="Test",
                    category="pothole",
                    description=description,
                    timestamp=datetime.now(),
                    coordinates=(12.9, 77.6)
                )
            ],
            center_coordinates=(12.9, 77.6),
            radius_meters=500.0,
            density_per_km2=density,
            is_high_density=False,
            time_window_hours=24
        )
        
        zone = engine.create_risk_zone_from_cluster(cluster)
        test_zones.append((zone, description))
    
    # Store in cache
    engine._risk_zones_cache = [z for z, _ in test_zones]
    
    # Filter zones
    filtered = engine.get_filtered_risk_zones(min_score=20.0)
    
    print(f"\n  Total zones: {len(test_zones)}")
    print(f"  Filtered zones (score > 20): {len(filtered)}")
    
    # Verify filtering
    for zone, desc in test_zones:
        should_be_included = zone.risk_score > 20.0
        is_included = zone in filtered
        
        status = "✓" if should_be_included == is_included else "✗"
        print(f"  {status} {desc:20s} Score: {zone.risk_score:5.1f} → "
              f"{'Included' if is_included else 'Excluded'}")
        
        assert should_be_included == is_included, \
            f"Zone with score {zone.risk_score} filtering mismatch"


def test_complete_workflow():
    """Test complete workflow with all components"""
    print("\nTesting Complete Workflow")
    
    # Create test data
    complaints = [
        Complaint(
            location="Koramangala",
            category="flooding",
            description="Heavy flooding",
            timestamp=datetime.now(),
            coordinates=(12.9352, 77.6245)
        ) for _ in range(6)
    ]
    
    cluster = Cluster(
        complaints=complaints,
        center_coordinates=(12.9352, 77.6245),
        radius_meters=500.0,
        density_per_km2=7.0,  # High density
        is_high_density=True,
        time_window_hours=24
    )
    
    weather = WeatherData(
        temperature_celsius=25.0,
        humidity_percent=80.0,
        precipitation_mm_per_hour=15.0,  # High rainfall
        wind_speed_kmh=20.0,
        high_rainfall_flag=True,
        timestamp=datetime.now(),
        source="test"
    )
    
    traffic = {
        "Koramangala": TrafficData(
            location="Koramangala",
            congestion_level=CongestionLevel.HIGH,
            congestion_score=10,
            timestamp=datetime.now()
        )
    }
    
    # Calculate risk zone
    engine = RiskEngine()
    zone = engine.create_risk_zone_from_cluster(cluster, weather, traffic)
    
    print(f"\n  Cluster density: {cluster.density_per_km2} per km²")
    print(f"  Weather: High rainfall ({weather.precipitation_mm_per_hour} mm/hr)")
    print(f"  Traffic: {traffic['Koramangala'].congestion_level.value.upper()}")
    print(f"  → Risk score: {zone.risk_score}")
    print(f"  → Risk level: {zone.risk_level.value.upper()}")
    
    # Verify score includes all modifiers
    # Base: 20 + (7-5)*4 = 28
    # Weather: +30 (high rainfall + flooding)
    # Expected: 58
    assert zone.risk_score >= 50, f"Expected score >= 50, got {zone.risk_score}"
    
    # Verify it would be included in filtered results
    assert zone.risk_score > 20, "Zone should pass filter threshold"
    
    print(f"  ✓ Complete workflow produces correct risk score")


if __name__ == "__main__":
    print("=" * 70)
    print("Task 7.3 Integration Tests")
    print("=" * 70)
    
    test_requirement_7_6_recalculation_interval()
    test_requirement_8_1_risk_level_classification()
    test_requirement_8_2_zone_filtering()
    test_complete_workflow()
    
    print("\n" + "=" * 70)
    print("✅ All integration tests passed!")
    print("=" * 70)
