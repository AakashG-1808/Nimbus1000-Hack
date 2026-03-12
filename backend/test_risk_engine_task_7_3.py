"""
Test for Task 7.3: Risk level classification and zone filtering
"""
from datetime import datetime
from risk_engine import RiskEngine
from models import Cluster, Complaint, RiskLevel, WeatherData, TrafficData, CongestionLevel


def test_risk_level_classification():
    """Test that risk levels are correctly classified"""
    engine = RiskEngine()
    
    # Test LOW risk (0-33)
    assert engine.classify_risk_level(0) == RiskLevel.LOW
    assert engine.classify_risk_level(15) == RiskLevel.LOW
    assert engine.classify_risk_level(33) == RiskLevel.LOW
    
    # Test MEDIUM risk (34-66)
    assert engine.classify_risk_level(34) == RiskLevel.MEDIUM
    assert engine.classify_risk_level(50) == RiskLevel.MEDIUM
    assert engine.classify_risk_level(66) == RiskLevel.MEDIUM
    
    # Test HIGH risk (67-100)
    assert engine.classify_risk_level(67) == RiskLevel.HIGH
    assert engine.classify_risk_level(85) == RiskLevel.HIGH
    assert engine.classify_risk_level(100) == RiskLevel.HIGH
    
    print("✓ Risk level classification works correctly")


def test_zone_filtering():
    """Test that zones are filtered by risk_score > 20"""
    engine = RiskEngine()
    
    # Create test clusters with different densities
    low_density_cluster = Cluster(
        complaints=[
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test",
                timestamp=datetime.now(),
                coordinates=(12.9352, 77.6245)
            )
        ],
        center_coordinates=(12.9352, 77.6245),
        radius_meters=500.0,
        density_per_km2=2.0,  # Low density -> score ~8
        is_high_density=False,
        time_window_hours=24
    )
    
    high_density_cluster = Cluster(
        complaints=[
            Complaint(
                location="Indiranagar",
                category="flooding",
                description="Test",
                timestamp=datetime.now(),
                coordinates=(12.9716, 77.6412)
            ) for _ in range(6)
        ],
        center_coordinates=(12.9716, 77.6412),
        radius_meters=500.0,
        density_per_km2=7.0,  # High density -> score >= 20
        is_high_density=True,
        time_window_hours=24
    )
    
    # Create risk zones
    low_risk_zone = engine.create_risk_zone_from_cluster(low_density_cluster)
    high_risk_zone = engine.create_risk_zone_from_cluster(high_density_cluster)
    
    print(f"Low density zone score: {low_risk_zone.risk_score}")
    print(f"High density zone score: {high_risk_zone.risk_score}")
    
    # Verify low risk zone is below threshold
    assert low_risk_zone.risk_score < 20, f"Expected score < 20, got {low_risk_zone.risk_score}"
    
    # Verify high risk zone is above threshold
    assert high_risk_zone.risk_score >= 20, f"Expected score >= 20, got {high_risk_zone.risk_score}"
    
    # Test filtering
    engine._risk_zones_cache = [low_risk_zone, high_risk_zone]
    filtered_zones = engine.get_filtered_risk_zones(min_score=20.0)
    
    assert len(filtered_zones) == 1, f"Expected 1 zone, got {len(filtered_zones)}"
    assert filtered_zones[0].zone_id == high_risk_zone.zone_id
    
    print("✓ Zone filtering works correctly (risk_score > 20)")


def test_recalculation_interval():
    """Test that recalculation interval is set to 15 minutes (900 seconds)"""
    engine = RiskEngine()
    
    assert engine.RECALCULATION_INTERVAL == 900, \
        f"Expected 900 seconds (15 minutes), got {engine.RECALCULATION_INTERVAL}"
    
    print("✓ Recalculation interval is 15 minutes (900 seconds)")


def test_min_risk_score_threshold():
    """Test that minimum risk score threshold is 20"""
    engine = RiskEngine()
    
    assert engine.MIN_RISK_SCORE_THRESHOLD == 20.0, \
        f"Expected 20.0, got {engine.MIN_RISK_SCORE_THRESHOLD}"
    
    print("✓ Minimum risk score threshold is 20.0")


if __name__ == "__main__":
    print("Testing Task 7.3: Risk level classification and zone filtering\n")
    
    test_risk_level_classification()
    test_zone_filtering()
    test_recalculation_interval()
    test_min_risk_score_threshold()
    
    print("\n✅ All tests passed!")
