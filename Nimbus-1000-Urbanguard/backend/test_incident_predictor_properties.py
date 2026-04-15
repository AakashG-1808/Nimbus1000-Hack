"""
Property-Based Tests for Incident Predictor
Tests for Task 8.3: Property tests for incident prediction using Hypothesis

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

Properties tested:
- Property 27: Incident Prediction for High-Risk Zones
- Property 28: Incident Type Matches Dominant Category
- Property 29: Flooding Incident Prediction
- Property 30: Traffic Gridlock Prediction
- Property 31: Incident Prediction Time Window Inclusion
"""
import pytest
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
from incident_predictor import IncidentPredictor
from models import (
    RiskZone, RiskLevel, WeatherData, TrafficData,
    CongestionLevel, Complaint
)


# ============================================================================
# Strategy Helpers
# ============================================================================

@st.composite
def risk_zone_strategy(draw, min_score=0.0, max_score=100.0, category=None):
    """Generate a valid RiskZone with specified constraints."""
    risk_score = draw(st.floats(min_value=min_score, max_value=max_score))
    
    # Determine risk level based on score
    if risk_score <= 33:
        risk_level = RiskLevel.LOW
    elif risk_score <= 66:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.HIGH
    
    # Select category
    categories = Complaint.CATEGORIES + ["mixed"]
    selected_category = category if category else draw(st.sampled_from(categories))
    
    return RiskZone(
        center_coordinates=(
            draw(st.floats(min_value=12.8, max_value=13.2)),
            draw(st.floats(min_value=77.4, max_value=77.8))
        ),
        radius_meters=500.0,
        risk_score=risk_score,
        risk_level=risk_level,
        complaint_count=draw(st.integers(min_value=1, max_value=50)),
        dominant_category=selected_category,
        last_updated=datetime.now()
    )


@st.composite
def weather_strategy(draw, high_rainfall=None):
    """Generate valid WeatherData."""
    if high_rainfall is True:
        precipitation = draw(st.floats(min_value=10.1, max_value=100.0))
        high_rainfall_flag = True
    elif high_rainfall is False:
        precipitation = draw(st.floats(min_value=0.0, max_value=10.0))
        high_rainfall_flag = False
    else:
        precipitation = draw(st.floats(min_value=0.0, max_value=100.0))
        high_rainfall_flag = precipitation > 10.0
    
    return WeatherData(
        temperature_celsius=draw(st.floats(min_value=15.0, max_value=40.0)),
        humidity_percent=draw(st.floats(min_value=20.0, max_value=100.0)),
        precipitation_mm_per_hour=precipitation,
        wind_speed_kmh=draw(st.floats(min_value=0.0, max_value=60.0)),
        high_rainfall_flag=high_rainfall_flag,
        timestamp=datetime.now(),
        source="test"
    )


@st.composite
def traffic_data_strategy(draw, high_congestion=None):
    """Generate valid traffic data dictionary."""
    locations = ["Koramangala", "Indiranagar", "Whitefield", "Electronic City"]
    traffic_data = {}
    
    for location in locations:
        if high_congestion is True:
            congestion_level = CongestionLevel.HIGH
            congestion_score = 10
        elif high_congestion is False:
            congestion_level = draw(st.sampled_from([CongestionLevel.LOW, CongestionLevel.MEDIUM]))
            congestion_score = 1 if congestion_level == CongestionLevel.LOW else 5
        else:
            congestion_level = draw(st.sampled_from([CongestionLevel.LOW, CongestionLevel.MEDIUM, CongestionLevel.HIGH]))
            congestion_score = {
                CongestionLevel.LOW: 1,
                CongestionLevel.MEDIUM: 5,
                CongestionLevel.HIGH: 10
            }[congestion_level]
        
        traffic_data[location] = TrafficData(
            location=location,
            congestion_level=congestion_level,
            congestion_score=congestion_score,
            timestamp=datetime.now()
        )
    
    return traffic_data


# ============================================================================
# Property Tests
# ============================================================================

class TestIncidentPredictorProperties:
    """Property-based tests for IncidentPredictor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.predictor = IncidentPredictor()
    
    # Feature: urbanguard-ai-system, Property 27: Incident Prediction for High-Risk Zones
    @given(
        high_risk_zones=st.lists(
            risk_zone_strategy(min_score=70.1, max_score=100.0),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_property_27_incident_prediction_for_high_risk_zones(self, high_risk_zones):
        """
        Property 27: For any zone with Risk_Score above 70, 
        the Incident_Predictor should generate an incident prediction.
        
        Validates: Requirement 9.1
        """
        # All zones have risk_score > 70
        for zone in high_risk_zones:
            assert zone.risk_score > 70.0
        
        # Generate predictions
        predictions = self.predictor.predict_incidents(high_risk_zones)
        
        # Should generate exactly one prediction per high-risk zone
        assert len(predictions) == len(high_risk_zones)
        
        # Each prediction should correspond to a zone
        predicted_zone_ids = {pred.zone_id for pred in predictions}
        zone_ids = {zone.zone_id for zone in high_risk_zones}
        assert predicted_zone_ids == zone_ids
    
    # Feature: urbanguard-ai-system, Property 27: No predictions for low-risk zones
    @given(
        low_risk_zones=st.lists(
            risk_zone_strategy(min_score=0.0, max_score=70.0),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_property_27_no_predictions_for_low_risk_zones(self, low_risk_zones):
        """
        Property 27 (inverse): For any zone with Risk_Score <= 70,
        the Incident_Predictor should NOT generate an incident prediction.
        
        Validates: Requirement 9.1
        """
        # All zones have risk_score <= 70
        for zone in low_risk_zones:
            assert zone.risk_score <= 70.0
        
        # Generate predictions
        predictions = self.predictor.predict_incidents(low_risk_zones)
        
        # Should generate no predictions
        assert len(predictions) == 0
    
    # Feature: urbanguard-ai-system, Property 28: Incident Type Matches Dominant Category
    @given(
        category=st.sampled_from(Complaint.CATEGORIES),
        risk_score=st.floats(min_value=70.1, max_value=100.0)
    )
    @settings(max_examples=100)
    def test_property_28_incident_type_matches_dominant_category(self, category, risk_score):
        """
        Property 28: For any zone with an incident prediction,
        the incident type should match the dominant complaint category in that zone.
        
        Validates: Requirement 9.2
        """
        # Create zone with specific category
        zone = RiskZone(
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            risk_score=risk_score,
            risk_level=RiskLevel.HIGH,
            complaint_count=10,
            dominant_category=category,
            last_updated=datetime.now()
        )
        
        # Generate prediction
        predictions = self.predictor.predict_incidents([zone])
        
        assert len(predictions) == 1
        prediction = predictions[0]
        
        # Map category to expected incident type
        category_mapping = {
            "pothole": "road_damage",
            "flooding": "flooding",
            "traffic": "traffic_congestion",
            "garbage": "waste_accumulation",
            "streetlight": "lighting_failure",
            "water_supply": "water_shortage",
            "noise": "noise_pollution",
            "construction": "construction_hazard"
        }
        
        expected_type = category_mapping.get(category, "infrastructure_issue")
        
        # Incident type should match (unless special rules apply)
        # For this test, we're not providing weather/traffic, so special rules won't trigger
        assert prediction.incident_type == expected_type
    
    # Feature: urbanguard-ai-system, Property 29: Flooding Incident Prediction
    @given(
        risk_score=st.floats(min_value=70.1, max_value=100.0),
        weather=weather_strategy(high_rainfall=True)
    )
    @settings(max_examples=100)
    def test_property_29_flooding_incident_prediction(self, risk_score, weather):
        """
        Property 29: For any zone, if high rainfall conditions and flooding complaints coincide,
        the Incident_Predictor should predict a flooding incident.
        
        Validates: Requirement 9.3
        """
        # Ensure high rainfall
        assert weather.high_rainfall_flag is True
        assert weather.precipitation_mm_per_hour > 10.0
        
        # Create zone with flooding complaints
        zone = RiskZone(
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            risk_score=risk_score,
            risk_level=RiskLevel.HIGH,
            complaint_count=10,
            dominant_category="flooding",
            last_updated=datetime.now()
        )
        
        # Generate prediction with high rainfall weather
        predictions = self.predictor.predict_incidents([zone], weather=weather)
        
        assert len(predictions) == 1
        prediction = predictions[0]
        
        # Should predict flooding incident
        assert prediction.incident_type == "flooding"
        
        # Should include high_rainfall in contributing factors
        assert "high_rainfall" in prediction.contributing_factors
    
    # Feature: urbanguard-ai-system, Property 30: Traffic Gridlock Prediction
    @given(
        risk_score=st.floats(min_value=70.1, max_value=100.0),
        traffic_data=traffic_data_strategy(high_congestion=True)
    )
    @settings(max_examples=100)
    def test_property_30_traffic_gridlock_prediction(self, risk_score, traffic_data):
        """
        Property 30: For any zone, if high traffic congestion and traffic complaints coincide,
        the Incident_Predictor should predict a traffic gridlock incident.
        
        Validates: Requirement 9.4
        """
        # Ensure high traffic congestion
        assert any(t.congestion_score == 10 for t in traffic_data.values())
        
        # Create zone with traffic complaints
        zone = RiskZone(
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            risk_score=risk_score,
            risk_level=RiskLevel.HIGH,
            complaint_count=10,
            dominant_category="traffic",
            last_updated=datetime.now()
        )
        
        # Generate prediction with high traffic
        predictions = self.predictor.predict_incidents([zone], traffic_data=traffic_data)
        
        assert len(predictions) == 1
        prediction = predictions[0]
        
        # Should predict traffic gridlock incident
        assert prediction.incident_type == "traffic_gridlock"
        
        # Should include high_traffic_congestion in contributing factors
        assert "high_traffic_congestion" in prediction.contributing_factors
    
    # Feature: urbanguard-ai-system, Property 31: Incident Prediction Time Window Inclusion
    @given(
        risk_score=st.floats(min_value=70.1, max_value=100.0)
    )
    @settings(max_examples=100)
    def test_property_31_time_window_inclusion(self, risk_score):
        """
        Property 31: For any incident prediction, it should include a predicted time window
        (either "next 6 hours" or "next 24 hours").
        
        Validates: Requirement 9.5
        """
        # Create zone with given risk score
        zone = RiskZone(
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            risk_score=risk_score,
            risk_level=RiskLevel.HIGH,
            complaint_count=10,
            dominant_category="pothole",
            last_updated=datetime.now()
        )
        
        # Generate prediction
        predictions = self.predictor.predict_incidents([zone])
        
        assert len(predictions) == 1
        prediction = predictions[0]
        
        # Should include time window
        assert prediction.time_window is not None
        assert prediction.time_window in ["next 6 hours", "next 24 hours"]
        
        # Time window should match risk score
        if risk_score > 85:
            assert prediction.time_window == "next 6 hours"
        else:
            assert prediction.time_window == "next 24 hours"
    
    # Feature: urbanguard-ai-system, Property 31: Time window correctness
    @given(
        zones=st.lists(
            risk_zone_strategy(min_score=70.1, max_score=100.0),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_property_31_time_window_correctness(self, zones):
        """
        Property 31 (extended): Time window should be correctly determined based on risk score.
        - "next 6 hours" for risk_score > 85
        - "next 24 hours" for risk_score 70-85
        
        Validates: Requirement 9.5
        """
        # Generate predictions
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == len(zones)
        
        # Check each prediction's time window
        for prediction in predictions:
            # Find corresponding zone
            zone = next(z for z in zones if z.zone_id == prediction.zone_id)
            
            # Verify time window matches risk score
            if zone.risk_score > 85:
                assert prediction.time_window == "next 6 hours", \
                    f"Zone with score {zone.risk_score} should have 'next 6 hours' time window"
            else:
                assert prediction.time_window == "next 24 hours", \
                    f"Zone with score {zone.risk_score} should have 'next 24 hours' time window"
    
    # Feature: urbanguard-ai-system, Additional property: Prediction completeness
    @given(
        zones=st.lists(
            risk_zone_strategy(min_score=70.1, max_score=100.0),
            min_size=1,
            max_size=5
        ),
        weather=weather_strategy(),
        traffic_data=traffic_data_strategy()
    )
    @settings(max_examples=100)
    def test_prediction_completeness(self, zones, weather, traffic_data):
        """
        Additional property: All predictions should have complete data structure.
        """
        predictions = self.predictor.predict_incidents(zones, weather=weather, traffic_data=traffic_data)
        
        assert len(predictions) == len(zones)
        
        for prediction in predictions:
            # Check all required fields are present
            assert prediction.prediction_id is not None
            assert prediction.zone_id is not None
            assert prediction.incident_type is not None
            assert prediction.risk_score is not None
            assert prediction.time_window is not None
            assert prediction.contributing_factors is not None
            assert prediction.created_at is not None
            
            # Check field types
            assert isinstance(prediction.prediction_id, str)
            assert isinstance(prediction.zone_id, str)
            assert isinstance(prediction.incident_type, str)
            assert isinstance(prediction.risk_score, float)
            assert isinstance(prediction.time_window, str)
            assert isinstance(prediction.contributing_factors, list)
            assert isinstance(prediction.created_at, datetime)
            
            # Check contributing factors is non-empty
            assert len(prediction.contributing_factors) > 0
    
    # Feature: urbanguard-ai-system, Additional property: Prediction uniqueness
    @given(
        zones=st.lists(
            risk_zone_strategy(min_score=70.1, max_score=100.0),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_prediction_uniqueness(self, zones):
        """
        Additional property: Each prediction should have a unique prediction_id.
        """
        predictions = self.predictor.predict_incidents(zones)
        
        assert len(predictions) == len(zones)
        
        # Check all prediction IDs are unique
        prediction_ids = [pred.prediction_id for pred in predictions]
        assert len(prediction_ids) == len(set(prediction_ids)), \
            "All prediction IDs should be unique"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
