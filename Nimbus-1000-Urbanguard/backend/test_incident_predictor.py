"""
Unit tests for Incident Predictor - Task 8.1
Tests incident prediction logic with various scenarios
"""
import pytest
from datetime import datetime
from models import RiskZone, RiskLevel, WeatherData, TrafficData, CongestionLevel
from incident_predictor import IncidentPredictor, get_incident_predictor


class TestIncidentPredictor:
    """Unit tests for IncidentPredictor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.predictor = IncidentPredictor()
        
        # Create test risk zones
        self.high_risk_flooding_zone = RiskZone(
            zone_id="zone-flood",
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            risk_score=75.0,
            risk_level=RiskLevel.HIGH,
            complaint_count=8,
            dominant_category="flooding",
            last_updated=datetime.now()
        )
        
        self.very_high_risk_traffic_zone = RiskZone(
            zone_id="zone-traffic",
            center_coordinates=(12.9716, 77.6412),
            radius_meters=500.0,
            risk_score=88.0,
            risk_level=RiskLevel.HIGH,
            complaint_count=12,
            dominant_category="traffic",
            last_updated=datetime.now()
        )
        
        self.medium_risk_zone = RiskZone(
            zone_id="zone-medium",
            center_coordinates=(12.9698, 77.7499),
            radius_meters=500.0,
            risk_score=65.0,
            risk_level=RiskLevel.MEDIUM,
            complaint_count=5,
            dominant_category="pothole",
            last_updated=datetime.now()
        )
        
        self.high_risk_pothole_zone = RiskZone(
            zone_id="zone-pothole",
            center_coordinates=(12.8456, 77.6603),
            radius_meters=500.0,
            risk_score=72.0,
            risk_level=RiskLevel.HIGH,
            complaint_count=6,
            dominant_category="pothole",
            last_updated=datetime.now()
        )
        
        # Create weather data
        self.high_rainfall_weather = WeatherData(
            temperature_celsius=28.0,
            humidity_percent=85.0,
            precipitation_mm_per_hour=15.0,
            wind_speed_kmh=25.0,
            high_rainfall_flag=True,
            timestamp=datetime.now(),
            source="test"
        )
        
        self.normal_weather = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=10.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="test"
        )
        
        # Create traffic data
        self.high_traffic_data = {
            "Koramangala": TrafficData(
                location="Koramangala",
                congestion_level=CongestionLevel.HIGH,
                congestion_score=10,
                timestamp=datetime.now()
            ),
            "Indiranagar": TrafficData(
                location="Indiranagar",
                congestion_level=CongestionLevel.HIGH,
                congestion_score=10,
                timestamp=datetime.now()
            )
        }
        
        self.low_traffic_data = {
            "Koramangala": TrafficData(
                location="Koramangala",
                congestion_level=CongestionLevel.LOW,
                congestion_score=1,
                timestamp=datetime.now()
            )
        }
    
    def test_predict_incidents_only_high_risk_zones(self):
        """Test that predictions are only generated for zones with risk_score > 70"""
        zones = [
            self.high_risk_flooding_zone,
            self.very_high_risk_traffic_zone,
            self.medium_risk_zone,  # score = 65, should not generate prediction
            self.high_risk_pothole_zone
        ]
        
        predictions = self.predictor.predict_incidents(zones)
        
        # Should generate 3 predictions (excluding medium risk zone)
        assert len(predictions) == 3
        
        # Verify all predictions are for high-risk zones
        predicted_zone_ids = {pred.zone_id for pred in predictions}
        assert "zone-flood" in predicted_zone_ids
        assert "zone-traffic" in predicted_zone_ids
        assert "zone-pothole" in predicted_zone_ids
        assert "zone-medium" not in predicted_zone_ids
    
    def test_predict_incidents_no_high_risk_zones(self):
        """Test that no predictions are generated when all zones have risk_score <= 70"""
        zones = [self.medium_risk_zone]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 0
    
    def test_incident_type_matches_dominant_category(self):
        """Test that incident type is based on dominant complaint category"""
        zones = [self.high_risk_pothole_zone]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert predictions[0].incident_type == "road_damage"  # pothole → road_damage
    
    def test_flooding_incident_with_high_rainfall(self):
        """Test special rule: High rainfall + flooding complaints → flooding incident"""
        zones = [self.high_risk_flooding_zone]
        
        predictions = self.predictor.predict_incidents(
            zones,
            weather=self.high_rainfall_weather
        )
        
        assert len(predictions) == 1
        assert predictions[0].incident_type == "flooding"
        assert "high_rainfall" in predictions[0].contributing_factors
    
    def test_flooding_incident_without_high_rainfall(self):
        """Test that flooding is still predicted without high rainfall"""
        zones = [self.high_risk_flooding_zone]
        
        predictions = self.predictor.predict_incidents(
            zones,
            weather=self.normal_weather
        )
        
        assert len(predictions) == 1
        assert predictions[0].incident_type == "flooding"
        assert "high_rainfall" not in predictions[0].contributing_factors
    
    def test_traffic_gridlock_with_high_traffic(self):
        """Test special rule: High traffic + traffic complaints → gridlock incident"""
        zones = [self.very_high_risk_traffic_zone]
        
        predictions = self.predictor.predict_incidents(
            zones,
            traffic_data=self.high_traffic_data
        )
        
        assert len(predictions) == 1
        assert predictions[0].incident_type == "traffic_gridlock"
        assert "high_traffic_congestion" in predictions[0].contributing_factors
    
    def test_traffic_congestion_without_high_traffic(self):
        """Test that traffic congestion is predicted without high traffic"""
        zones = [self.very_high_risk_traffic_zone]
        
        predictions = self.predictor.predict_incidents(
            zones,
            traffic_data=self.low_traffic_data
        )
        
        assert len(predictions) == 1
        assert predictions[0].incident_type == "traffic_congestion"
        assert "high_traffic_congestion" not in predictions[0].contributing_factors
    
    def test_time_window_next_6_hours(self):
        """Test that risk_score > 85 results in 'next 6 hours' time window"""
        zones = [self.very_high_risk_traffic_zone]  # score = 88
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert predictions[0].time_window == "next 6 hours"
    
    def test_time_window_next_24_hours(self):
        """Test that risk_score 70-85 results in 'next 24 hours' time window"""
        zones = [self.high_risk_flooding_zone]  # score = 75
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert predictions[0].time_window == "next 24 hours"
    
    def test_contributing_factors_include_complaint_density(self):
        """Test that contributing factors always include high_complaint_density"""
        zones = [self.high_risk_pothole_zone]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert "high_complaint_density" in predictions[0].contributing_factors
    
    def test_contributing_factors_include_dominant_category(self):
        """Test that contributing factors include dominant category"""
        zones = [self.high_risk_pothole_zone]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert "pothole_complaints" in predictions[0].contributing_factors
    
    def test_contributing_factors_with_weather_and_traffic(self):
        """Test that contributing factors include weather and traffic when provided"""
        zones = [self.very_high_risk_traffic_zone]
        
        predictions = self.predictor.predict_incidents(
            zones,
            weather=self.high_rainfall_weather,
            traffic_data=self.high_traffic_data
        )
        
        assert len(predictions) == 1
        factors = predictions[0].contributing_factors
        assert "high_complaint_density" in factors
        assert "high_rainfall" in factors
        assert "high_traffic_congestion" in factors
        assert "traffic_complaints" in factors
    
    def test_prediction_includes_zone_id(self):
        """Test that prediction includes the zone_id"""
        zones = [self.high_risk_flooding_zone]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert predictions[0].zone_id == "zone-flood"
    
    def test_prediction_includes_risk_score(self):
        """Test that prediction includes the risk_score"""
        zones = [self.high_risk_flooding_zone]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert predictions[0].risk_score == 75.0
    
    def test_prediction_has_unique_id(self):
        """Test that each prediction has a unique prediction_id"""
        zones = [
            self.high_risk_flooding_zone,
            self.very_high_risk_traffic_zone,
            self.high_risk_pothole_zone
        ]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 3
        prediction_ids = [pred.prediction_id for pred in predictions]
        assert len(set(prediction_ids)) == 3  # All unique
    
    def test_prediction_has_created_at_timestamp(self):
        """Test that each prediction has a created_at timestamp"""
        zones = [self.high_risk_flooding_zone]
        
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == 1
        assert isinstance(predictions[0].created_at, datetime)
    
    def test_category_mapping_to_incident_types(self):
        """Test that all categories map to appropriate incident types"""
        category_mappings = {
            "pothole": "road_damage",
            "flooding": "flooding",
            "traffic": "traffic_congestion",
            "garbage": "waste_accumulation",
            "streetlight": "lighting_failure",
            "water_supply": "water_shortage",
            "noise": "noise_pollution",
            "construction": "construction_hazard"
        }
        
        for category, expected_type in category_mappings.items():
            zone = RiskZone(
                zone_id=f"zone-{category}",
                center_coordinates=(12.9352, 77.6245),
                radius_meters=500.0,
                risk_score=75.0,
                risk_level=RiskLevel.HIGH,
                complaint_count=8,
                dominant_category=category,
                last_updated=datetime.now()
            )
            
            predictions = self.predictor.predict_incidents([zone])
            
            assert len(predictions) == 1
            assert predictions[0].incident_type == expected_type


class TestIncidentPredictorSingleton:
    """Test the global incident predictor singleton"""
    
    def test_get_incident_predictor_returns_instance(self):
        """Test that get_incident_predictor returns an IncidentPredictor instance"""
        predictor = get_incident_predictor()
        assert isinstance(predictor, IncidentPredictor)
    
    def test_get_incident_predictor_returns_same_instance(self):
        """Test that get_incident_predictor returns the same instance"""
        predictor1 = get_incident_predictor()
        predictor2 = get_incident_predictor()
        assert predictor1 is predictor2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
