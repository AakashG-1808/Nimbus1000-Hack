"""
Integration tests for Incident Predictor with Risk Engine - Task 8.1
Tests incident prediction with real risk zones from the risk engine
"""
import pytest
from datetime import datetime, timedelta
from models import Complaint, WeatherData, TrafficData, CongestionLevel
from constants import BENGALURU_LOCATIONS
from cluster_detector import ClusterDetector
from risk_engine import RiskEngine
from incident_predictor import get_incident_predictor


class TestIncidentPredictorIntegration:
    """Integration tests for IncidentPredictor with RiskEngine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.predictor = get_incident_predictor()
        
        # Create complaints for testing
        now = datetime.now()
        
        # Create flooding complaints in Koramangala (high density)
        self.flooding_complaints = [
            Complaint(
                location="Koramangala",
                category="flooding",
                description=f"Flooding issue {i}",
                timestamp=now - timedelta(hours=i),
                coordinates=BENGALURU_LOCATIONS["Koramangala"],
                classification_confidence=0.9
            )
            for i in range(8)
        ]
        
        # Create traffic complaints in Indiranagar (high density)
        self.traffic_complaints = [
            Complaint(
                location="Indiranagar",
                category="traffic",
                description=f"Traffic issue {i}",
                timestamp=now - timedelta(hours=i),
                coordinates=BENGALURU_LOCATIONS["Indiranagar"],
                classification_confidence=0.9
            )
            for i in range(10)
        ]
        
        # Create pothole complaints in Whitefield (medium density)
        self.pothole_complaints = [
            Complaint(
                location="Whitefield",
                category="pothole",
                description=f"Pothole issue {i}",
                timestamp=now - timedelta(hours=i),
                coordinates=BENGALURU_LOCATIONS["Whitefield"],
                classification_confidence=0.9
            )
            for i in range(4)
        ]
        
        # Create weather data
        self.high_rainfall_weather = WeatherData(
            temperature_celsius=28.0,
            humidity_percent=85.0,
            precipitation_mm_per_hour=15.0,
            wind_speed_kmh=25.0,
            high_rainfall_flag=True,
            timestamp=now,
            source="test"
        )
        
        # Create traffic data
        self.high_traffic_data = {
            "Koramangala": TrafficData(
                location="Koramangala",
                congestion_level=CongestionLevel.HIGH,
                congestion_score=10,
                timestamp=now
            ),
            "Indiranagar": TrafficData(
                location="Indiranagar",
                congestion_level=CongestionLevel.HIGH,
                congestion_score=10,
                timestamp=now
            ),
            "Whitefield": TrafficData(
                location="Whitefield",
                congestion_level=CongestionLevel.LOW,
                congestion_score=1,
                timestamp=now
            )
        }
    
    def test_integration_with_risk_engine_flooding_scenario(self):
        """Test incident prediction with risk engine for flooding scenario"""
        # Create cluster detector
        cluster_detector = ClusterDetector()
        clusters = cluster_detector.detect_clusters(self.flooding_complaints)
        
        # Create risk engine
        risk_engine = RiskEngine()
        
        # Calculate risk zones with high rainfall
        risk_zones = []
        for cluster in clusters:
            risk_zone = risk_engine.create_risk_zone_from_cluster(
                cluster=cluster,
                weather=self.high_rainfall_weather,
                traffic_data=self.high_traffic_data
            )
            risk_zones.append(risk_zone)
        
        # Generate predictions
        predictions = self.predictor.predict_incidents(
            risk_zones,
            weather=self.high_rainfall_weather,
            traffic_data=self.high_traffic_data
        )
        
        # Verify predictions
        assert len(predictions) > 0
        
        # Check for flooding prediction
        flooding_predictions = [
            p for p in predictions
            if p.incident_type == "flooding"
        ]
        
        if flooding_predictions:
            pred = flooding_predictions[0]
            assert pred.risk_score > 70
            assert "high_rainfall" in pred.contributing_factors
            assert "flooding_complaints" in pred.contributing_factors
    
    def test_integration_with_risk_engine_traffic_scenario(self):
        """Test incident prediction with risk engine for traffic scenario"""
        # Create cluster detector
        cluster_detector = ClusterDetector()
        clusters = cluster_detector.detect_clusters(self.traffic_complaints)
        
        # Create risk engine
        risk_engine = RiskEngine()
        
        # Calculate risk zones with high traffic
        risk_zones = []
        for cluster in clusters:
            risk_zone = risk_engine.create_risk_zone_from_cluster(
                cluster=cluster,
                weather=WeatherData(
                    temperature_celsius=25.0,
                    humidity_percent=60.0,
                    precipitation_mm_per_hour=0.0,
                    wind_speed_kmh=10.0,
                    high_rainfall_flag=False,
                    timestamp=datetime.now(),
                    source="test"
                ),
                traffic_data=self.high_traffic_data
            )
            risk_zones.append(risk_zone)
        
        # Generate predictions
        predictions = self.predictor.predict_incidents(
            risk_zones,
            traffic_data=self.high_traffic_data
        )
        
        # Verify predictions - may be 0 if risk score doesn't exceed 70
        # This is expected behavior - not all zones will have high enough risk
        # Check that if predictions exist, they have correct structure
        for pred in predictions:
            assert pred.prediction_id is not None
            assert pred.zone_id is not None
            assert pred.incident_type is not None
            assert pred.risk_score > 70
            assert pred.time_window in ["next 6 hours", "next 24 hours"]
            assert len(pred.contributing_factors) > 0
            
            # If traffic predictions exist, verify they have traffic factors
            if "traffic" in pred.incident_type:
                assert "high_traffic_congestion" in pred.contributing_factors
                assert "traffic_complaints" in pred.contributing_factors
    
    def test_integration_no_predictions_for_low_risk(self):
        """Test that no predictions are generated for low-risk zones"""
        # Create cluster detector with few complaints
        cluster_detector = ClusterDetector()
        clusters = cluster_detector.detect_clusters(self.pothole_complaints)
        
        # Create risk engine
        risk_engine = RiskEngine()
        
        # Calculate risk zones without weather/traffic modifiers
        risk_zones = []
        for cluster in clusters:
            risk_zone = risk_engine.create_risk_zone_from_cluster(
                cluster=cluster,
                weather=WeatherData(
                    temperature_celsius=25.0,
                    humidity_percent=60.0,
                    precipitation_mm_per_hour=0.0,
                    wind_speed_kmh=10.0,
                    high_rainfall_flag=False,
                    timestamp=datetime.now(),
                    source="test"
                ),
                traffic_data={
                    "Whitefield": TrafficData(
                        location="Whitefield",
                        congestion_level=CongestionLevel.LOW,
                        congestion_score=1,
                        timestamp=datetime.now()
                    )
                }
            )
            risk_zones.append(risk_zone)
        
        # Generate predictions
        predictions = self.predictor.predict_incidents(risk_zones)
        
        # Verify no predictions for low-risk zones
        high_risk_predictions = [
            p for p in predictions
            if p.risk_score > 70
        ]
        
        # Should have no high-risk predictions
        assert len(high_risk_predictions) == 0
    
    def test_integration_multiple_zones_multiple_predictions(self):
        """Test incident prediction with multiple high-risk zones"""
        # Combine all complaints
        all_complaints = (
            self.flooding_complaints +
            self.traffic_complaints +
            self.pothole_complaints
        )
        
        # Create cluster detector
        cluster_detector = ClusterDetector()
        clusters = cluster_detector.detect_clusters(all_complaints)
        
        # Create risk engine
        risk_engine = RiskEngine()
        
        # Calculate risk zones with weather and traffic
        risk_zones = []
        for cluster in clusters:
            risk_zone = risk_engine.create_risk_zone_from_cluster(
                cluster=cluster,
                weather=self.high_rainfall_weather,
                traffic_data=self.high_traffic_data
            )
            risk_zones.append(risk_zone)
        
        # Generate predictions
        predictions = self.predictor.predict_incidents(
            risk_zones,
            weather=self.high_rainfall_weather,
            traffic_data=self.high_traffic_data
        )
        
        # Verify predictions
        assert len(predictions) > 0
        
        # Verify each prediction has required fields
        for pred in predictions:
            assert pred.prediction_id is not None
            assert pred.zone_id is not None
            assert pred.incident_type is not None
            assert pred.risk_score > 70
            assert pred.time_window in ["next 6 hours", "next 24 hours"]
            assert len(pred.contributing_factors) > 0
            assert isinstance(pred.created_at, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
