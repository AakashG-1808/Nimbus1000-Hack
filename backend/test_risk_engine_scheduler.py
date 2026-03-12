"""
Test for Task 7.3: Risk Engine scheduler and integration
"""
import time
from datetime import datetime
from risk_engine import get_risk_engine
from models import Cluster, Complaint, WeatherData, TrafficData, CongestionLevel, RiskZone


def test_scheduler_integration():
    """Test that the risk engine scheduler works with callbacks"""
    
    # Track calls
    clusters_called = []
    weather_called = []
    traffic_called = []
    zones_updated = []
    
    # Create test data
    test_cluster = Cluster(
        complaints=[
            Complaint(
                location="Koramangala",
                category="flooding",
                description="Heavy flooding",
                timestamp=datetime.now(),
                coordinates=(12.9352, 77.6245)
            ) for _ in range(6)
        ],
        center_coordinates=(12.9352, 77.6245),
        radius_meters=500.0,
        density_per_km2=7.0,
        is_high_density=True,
        time_window_hours=24
    )
    
    test_weather = WeatherData(
        temperature_celsius=25.0,
        humidity_percent=80.0,
        precipitation_mm_per_hour=15.0,  # High rainfall
        wind_speed_kmh=20.0,
        high_rainfall_flag=True,
        timestamp=datetime.now(),
        source="test"
    )
    
    test_traffic = {
        "Koramangala": TrafficData(
            location="Koramangala",
            congestion_level=CongestionLevel.HIGH,
            congestion_score=10,
            timestamp=datetime.now()
        )
    }
    
    # Define callbacks
    def get_clusters():
        clusters_called.append(True)
        return [test_cluster]
    
    def get_weather():
        weather_called.append(True)
        return test_weather
    
    def get_traffic():
        traffic_called.append(True)
        return test_traffic
    
    def update_zones(zones):
        zones_updated.append(zones)
    
    # Create risk engine with callbacks (but don't auto-start)
    engine = get_risk_engine(
        get_clusters_callback=get_clusters,
        get_weather_callback=get_weather,
        get_traffic_callback=get_traffic,
        update_risk_zones_callback=update_zones
    )
    
    # Manually trigger calculation
    risk_zones = engine.calculate_all_risk_zones()
    
    # Verify callbacks were called
    assert len(clusters_called) > 0, "Clusters callback not called"
    assert len(weather_called) > 0, "Weather callback not called"
    assert len(traffic_called) > 0, "Traffic callback not called"
    assert len(zones_updated) > 0, "Update zones callback not called"
    
    # Verify risk zones were calculated
    assert len(risk_zones) == 1, f"Expected 1 risk zone, got {len(risk_zones)}"
    
    # Verify the risk zone has high score due to:
    # - High density (7.0 > 5.0) -> +20 points
    # - High rainfall + flooding complaints -> +30 points
    # Total should be at least 50
    risk_zone = risk_zones[0]
    print(f"Risk zone score: {risk_zone.risk_score}")
    print(f"Risk zone level: {risk_zone.risk_level.value}")
    
    assert risk_zone.risk_score >= 50, \
        f"Expected score >= 50 (density + weather), got {risk_zone.risk_score}"
    
    # Verify filtering works
    filtered = engine.get_filtered_risk_zones(min_score=20.0)
    assert len(filtered) == 1, f"Expected 1 filtered zone, got {len(filtered)}"
    
    print("✓ Scheduler integration works correctly")
    print(f"✓ Risk score calculation includes all modifiers: {risk_zone.risk_score}")


def test_scheduler_start_stop():
    """Test that scheduler can be started and stopped"""
    
    def get_clusters():
        return []
    
    # Create engine without auto-start
    from risk_engine import RiskEngine
    engine = RiskEngine(
        auto_start=False,
        get_clusters_callback=get_clusters
    )
    
    # Verify not running
    assert not engine._scheduler_running, "Scheduler should not be running"
    
    # Start scheduler
    engine.start_scheduler()
    assert engine._scheduler_running, "Scheduler should be running"
    
    # Try to start again (should warn but not fail)
    engine.start_scheduler()
    assert engine._scheduler_running, "Scheduler should still be running"
    
    # Stop scheduler
    engine.stop_scheduler()
    assert not engine._scheduler_running, "Scheduler should be stopped"
    
    # Try to stop again (should not fail)
    engine.stop_scheduler()
    assert not engine._scheduler_running, "Scheduler should still be stopped"
    
    print("✓ Scheduler start/stop works correctly")


if __name__ == "__main__":
    print("Testing Task 7.3: Risk Engine scheduler and integration\n")
    
    test_scheduler_integration()
    test_scheduler_start_stop()
    
    print("\n✅ All scheduler tests passed!")
