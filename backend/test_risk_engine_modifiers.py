"""
Unit tests for Risk Engine - Weather and Traffic Modifiers
Tests for Task 7.2: Weather and traffic modifiers implementation
"""
import pytest
from datetime import datetime
from risk_engine import RiskEngine
from models import (
    Cluster, Complaint, WeatherData, TrafficData,
    CongestionLevel, RiskLevel
)


class TestWeatherModifier:
    """Tests for weather-based risk modifiers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def create_cluster(
        self,
        complaint_count: int,
        density: float,
        category: str = "pothole",
        location: str = "Koramangala"
    ) -> Cluster:
        """Helper to create a test cluster."""
        complaints = []
        for i in range(complaint_count):
            complaint = Complaint(
                location=location,
                category=category,
                description=f"Test complaint {i}",
                timestamp=datetime.now(),
                coordinates=(12.9352, 77.6245)
            )
            complaints.append(complaint)
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=density,
            is_high_density=density >= 5.0,
            time_window_hours=24
        )
        
        return cluster
    
    def create_weather_data(
        self,
        precipitation: float = 0.0,
        high_rainfall: bool = False
    ) -> WeatherData:
        """Helper to create weather data."""
        return WeatherData(
            temperature_celsius=25.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=precipitation,
            wind_speed_kmh=10.0,
            high_rainfall_flag=high_rainfall,
            timestamp=datetime.now(),
            source="test"
        )
    
    def test_no_weather_modifier_without_high_rainfall(self):
        """Test that normal weather conditions add no modifier."""
        cluster = self.create_cluster(
            complaint_count=3,
            density=3.0,
            category="flooding"
        )
        
        # Normal weather (no high rainfall)
        weather = self.create_weather_data(precipitation=5.0, high_rainfall=False)
        
        score = self.engine.calculate_risk_score(cluster, weather=weather)
        
        # Expected: base score only (3.0 * 4 = 12)
        assert score == 12.0
    
    def test_no_weather_modifier_without_flood_complaints(self):
        """Test that high rainfall without flood complaints adds no modifier."""
        cluster = self.create_cluster(
            complaint_count=3,
            density=3.0,
            category="pothole"  # Not flooding
        )
        
        # High rainfall
        weather = self.create_weather_data(precipitation=15.0, high_rainfall=True)
        
        score = self.engine.calculate_risk_score(cluster, weather=weather)
        
        # Expected: base score only (3.0 * 4 = 12)
        assert score == 12.0
    
    def test_weather_modifier_adds_30_points_for_high_rainfall_and_floods(self):
        """Test that high rainfall + flood complaints adds 30 points."""
        cluster = self.create_cluster(
            complaint_count=3,
            density=3.0,
            category="flooding"
        )
        
        # High rainfall
        weather = self.create_weather_data(precipitation=15.0, high_rainfall=True)
        
        score = self.engine.calculate_risk_score(cluster, weather=weather)
        
        # Expected: base (3.0 * 4 = 12) + weather modifier (30) = 42
        assert score == 42.0
    
    def test_weather_modifier_with_mixed_complaints(self):
        """Test weather modifier with mixed complaint categories."""
        # Create cluster with mixed complaints including flooding
        complaints = [
            Complaint("Koramangala", "pothole", "Test 1", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "flooding", "Test 2", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "garbage", "Test 3", datetime.now(), (12.9352, 77.6245)),
        ]
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=3.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        # High rainfall
        weather = self.create_weather_data(precipitation=20.0, high_rainfall=True)
        
        score = self.engine.calculate_risk_score(cluster, weather=weather)
        
        # Expected: base (3.0 * 4 = 12) + weather modifier (30) = 42
        # Should add modifier because at least one flooding complaint exists
        assert score == 42.0
    
    def test_weather_modifier_with_high_density(self):
        """Test weather modifier combined with high density bonus."""
        cluster = self.create_cluster(
            complaint_count=6,
            density=6.0,
            category="flooding"
        )
        
        # High rainfall
        weather = self.create_weather_data(precipitation=25.0, high_rainfall=True)
        
        score = self.engine.calculate_risk_score(cluster, weather=weather)
        
        # Expected: base (20 + (6-5)*4 = 24) + weather modifier (30) = 54
        assert score == 54.0


class TestTrafficModifier:
    """Tests for traffic-based risk modifiers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def create_cluster(
        self,
        complaint_count: int,
        density: float,
        category: str = "pothole",
        location: str = "Koramangala"
    ) -> Cluster:
        """Helper to create a test cluster."""
        complaints = []
        for i in range(complaint_count):
            complaint = Complaint(
                location=location,
                category=category,
                description=f"Test complaint {i}",
                timestamp=datetime.now(),
                coordinates=(12.9352, 77.6245)
            )
            complaints.append(complaint)
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=density,
            is_high_density=density >= 5.0,
            time_window_hours=24
        )
        
        return cluster
    
    def create_traffic_data(
        self,
        location: str,
        congestion_level: CongestionLevel
    ) -> dict:
        """Helper to create traffic data dictionary."""
        score_mapping = {
            CongestionLevel.LOW: 1,
            CongestionLevel.MEDIUM: 5,
            CongestionLevel.HIGH: 10
        }
        
        traffic = TrafficData(
            location=location,
            congestion_level=congestion_level,
            congestion_score=score_mapping[congestion_level],
            timestamp=datetime.now()
        )
        
        return {location: traffic}
    
    def test_no_traffic_modifier_without_high_congestion(self):
        """Test that low/medium congestion adds no modifier."""
        cluster = self.create_cluster(
            complaint_count=3,
            density=3.0,
            category="traffic",
            location="Koramangala"
        )
        
        # Low congestion
        traffic_data = self.create_traffic_data("Koramangala", CongestionLevel.LOW)
        
        score = self.engine.calculate_risk_score(cluster, traffic_data=traffic_data)
        
        # Expected: base score only (3.0 * 4 = 12)
        assert score == 12.0
        
        # Medium congestion
        traffic_data = self.create_traffic_data("Koramangala", CongestionLevel.MEDIUM)
        
        score = self.engine.calculate_risk_score(cluster, traffic_data=traffic_data)
        
        # Expected: base score only (3.0 * 4 = 12)
        assert score == 12.0
    
    def test_no_traffic_modifier_without_traffic_complaints(self):
        """Test that high congestion without traffic complaints adds no modifier."""
        cluster = self.create_cluster(
            complaint_count=3,
            density=3.0,
            category="pothole",  # Not traffic
            location="Koramangala"
        )
        
        # High congestion
        traffic_data = self.create_traffic_data("Koramangala", CongestionLevel.HIGH)
        
        score = self.engine.calculate_risk_score(cluster, traffic_data=traffic_data)
        
        # Expected: base score only (3.0 * 4 = 12)
        assert score == 12.0
    
    def test_traffic_modifier_adds_15_points_for_high_congestion_and_traffic(self):
        """Test that high congestion + traffic complaints adds 15 points."""
        cluster = self.create_cluster(
            complaint_count=3,
            density=3.0,
            category="traffic",
            location="Koramangala"
        )
        
        # High congestion
        traffic_data = self.create_traffic_data("Koramangala", CongestionLevel.HIGH)
        
        score = self.engine.calculate_risk_score(cluster, traffic_data=traffic_data)
        
        # Expected: base (3.0 * 4 = 12) + traffic modifier (15) = 27
        assert score == 27.0
    
    def test_traffic_modifier_with_mixed_complaints(self):
        """Test traffic modifier with mixed complaint categories."""
        # Create cluster with mixed complaints including traffic
        complaints = [
            Complaint("Koramangala", "pothole", "Test 1", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "traffic", "Test 2", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "garbage", "Test 3", datetime.now(), (12.9352, 77.6245)),
        ]
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=3.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        # High congestion
        traffic_data = self.create_traffic_data("Koramangala", CongestionLevel.HIGH)
        
        score = self.engine.calculate_risk_score(cluster, traffic_data=traffic_data)
        
        # Expected: base (3.0 * 4 = 12) + traffic modifier (15) = 27
        # Should add modifier because at least one traffic complaint exists
        assert score == 27.0
    
    def test_traffic_modifier_with_high_density(self):
        """Test traffic modifier combined with high density bonus."""
        cluster = self.create_cluster(
            complaint_count=6,
            density=6.0,
            category="traffic",
            location="Koramangala"
        )
        
        # High congestion
        traffic_data = self.create_traffic_data("Koramangala", CongestionLevel.HIGH)
        
        score = self.engine.calculate_risk_score(cluster, traffic_data=traffic_data)
        
        # Expected: base (20 + (6-5)*4 = 24) + traffic modifier (15) = 39
        assert score == 39.0
    
    def test_traffic_modifier_with_multiple_locations(self):
        """Test traffic modifier with complaints from multiple locations."""
        # Create cluster with traffic complaints from different locations
        complaints = [
            Complaint("Koramangala", "traffic", "Test 1", datetime.now(), (12.9352, 77.6245)),
            Complaint("Indiranagar", "traffic", "Test 2", datetime.now(), (12.9716, 77.6412)),
        ]
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=2.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        # High congestion in Koramangala, low in Indiranagar
        traffic_data = {
            "Koramangala": TrafficData(
                location="Koramangala",
                congestion_level=CongestionLevel.HIGH,
                congestion_score=10,
                timestamp=datetime.now()
            ),
            "Indiranagar": TrafficData(
                location="Indiranagar",
                congestion_level=CongestionLevel.LOW,
                congestion_score=1,
                timestamp=datetime.now()
            )
        }
        
        score = self.engine.calculate_risk_score(cluster, traffic_data=traffic_data)
        
        # Expected: base (2.0 * 4 = 8) + traffic modifier (15) = 23
        # Should add modifier because at least one location has high congestion
        assert score == 23.0


class TestCombinedModifiers:
    """Tests for combined weather and traffic modifiers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def create_cluster(
        self,
        complaints: list
    ) -> Cluster:
        """Helper to create a cluster from complaint list."""
        density = len(complaints) / 0.785  # Approximate density for 500m radius
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=density,
            is_high_density=density >= 5.0,
            time_window_hours=24
        )
        
        return cluster
    
    def test_both_modifiers_applied(self):
        """Test that both weather and traffic modifiers can be applied together."""
        # Create cluster with both flooding and traffic complaints
        complaints = [
            Complaint("Koramangala", "flooding", "Test 1", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "traffic", "Test 2", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "pothole", "Test 3", datetime.now(), (12.9352, 77.6245)),
        ]
        
        cluster = self.create_cluster(complaints)
        
        # High rainfall
        weather = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=80.0,
            precipitation_mm_per_hour=20.0,
            wind_speed_kmh=15.0,
            high_rainfall_flag=True,
            timestamp=datetime.now(),
            source="test"
        )
        
        # High congestion
        traffic_data = {
            "Koramangala": TrafficData(
                location="Koramangala",
                congestion_level=CongestionLevel.HIGH,
                congestion_score=10,
                timestamp=datetime.now()
            )
        }
        
        score = self.engine.calculate_risk_score(
            cluster,
            weather=weather,
            traffic_data=traffic_data
        )
        
        # Expected: base (3.82 * 4 ≈ 15.28) + weather (30) + traffic (15) ≈ 60.28
        # Actual density: 3 / 0.785 ≈ 3.82
        assert 59.0 <= score <= 61.0  # Allow small floating point variance
    
    def test_score_capped_at_100_with_all_modifiers(self):
        """Test that final score is capped at 100 even with all modifiers."""
        # Create high-density cluster with both flooding and traffic
        complaints = []
        for i in range(20):
            category = "flooding" if i % 2 == 0 else "traffic"
            complaints.append(
                Complaint(
                    "Koramangala",
                    category,
                    f"Test {i}",
                    datetime.now(),
                    (12.9352, 77.6245)
                )
            )
        
        cluster = self.create_cluster(complaints)
        
        # High rainfall
        weather = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=90.0,
            precipitation_mm_per_hour=50.0,
            wind_speed_kmh=30.0,
            high_rainfall_flag=True,
            timestamp=datetime.now(),
            source="test"
        )
        
        # High congestion
        traffic_data = {
            "Koramangala": TrafficData(
                location="Koramangala",
                congestion_level=CongestionLevel.HIGH,
                congestion_score=10,
                timestamp=datetime.now()
            )
        }
        
        score = self.engine.calculate_risk_score(
            cluster,
            weather=weather,
            traffic_data=traffic_data
        )
        
        # Score should be capped at 100
        assert score == 100.0
    
    def test_no_modifiers_without_data(self):
        """Test that no modifiers are applied when weather/traffic data is None."""
        cluster = self.create_cluster([
            Complaint("Koramangala", "flooding", "Test 1", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "traffic", "Test 2", datetime.now(), (12.9352, 77.6245)),
        ])
        
        # Calculate without weather or traffic data
        score = self.engine.calculate_risk_score(cluster)
        
        # Expected: base score only (2.55 * 4 ≈ 10.2)
        # Actual density: 2 / 0.785 ≈ 2.55
        assert 9.0 <= score <= 11.0


class TestIntegrationWithWeatherAndTraffic:
    """Integration tests with Weather_Integrator and Traffic_Analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def test_risk_zone_creation_with_modifiers(self):
        """Test creating a RiskZone with weather and traffic modifiers."""
        # Create cluster with flooding complaints
        complaints = [
            Complaint("Koramangala", "flooding", "Test 1", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "flooding", "Test 2", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "flooding", "Test 3", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "flooding", "Test 4", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "flooding", "Test 5", datetime.now(), (12.9352, 77.6245)),
        ]
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=6.37,  # 5 / 0.785
            is_high_density=True,
            time_window_hours=24
        )
        
        # High rainfall
        weather = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=85.0,
            precipitation_mm_per_hour=15.0,
            wind_speed_kmh=20.0,
            high_rainfall_flag=True,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        # Create risk zone
        risk_zone = self.engine.create_risk_zone_from_cluster(
            cluster,
            weather=weather
        )
        
        # Verify risk zone properties
        assert risk_zone.complaint_count == 5
        assert risk_zone.dominant_category == "flooding"
        
        # Expected score: base (20 + (6.37-5)*4 ≈ 25.48) + weather (30) ≈ 55.48
        assert 54.0 <= risk_zone.risk_score <= 56.0
        assert risk_zone.risk_level == RiskLevel.MEDIUM  # 55 is in MEDIUM range (34-66)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
