"""
Property-Based Tests for Risk Engine
Tests for Task 7.4: Property tests for risk calculation using Hypothesis

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2**

Properties tested:
- Property 19: Risk Score Calculation Uses All Factors
- Property 20: Risk Score Bounds
- Property 21: High Complaint Density Score Increase
- Property 22: High Rainfall Flood Risk Increase
- Property 23: High Traffic Congestion Risk Increase
- Property 24: Risk Level Classification
- Property 25: Risk Zone Filtering
"""
import pytest
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
from risk_engine import RiskEngine
from models import (
    Cluster, Complaint, WeatherData, TrafficData,
    CongestionLevel, RiskLevel
)


# ============================================================================
# Strategy Helpers
# ============================================================================

@st.composite
def complaint_strategy(draw, category=None, location=None):
    """Generate a valid Complaint."""
    categories = Complaint.CATEGORIES
    locations = ["Koramangala", "Indiranagar", "Whitefield", "Electronic City", 
                 "Jayanagar", "Malleshwaram", "HSR Layout", "BTM Layout"]
    
    return Complaint(
        location=location if location else draw(st.sampled_from(locations)),
        category=category if category else draw(st.sampled_from(categories)),
        description=draw(st.text(min_size=1, max_size=100)),
        timestamp=datetime.now(),
        coordinates=(
            draw(st.floats(min_value=12.8, max_value=13.2)),
            draw(st.floats(min_value=77.4, max_value=77.8))
        )
    )


@st.composite
def cluster_strategy(draw, min_complaints=1, max_complaints=20, category=None, location=None):
    """Generate a valid Cluster with specified constraints."""
    complaint_count = draw(st.integers(min_value=min_complaints, max_value=max_complaints))
    complaints = [draw(complaint_strategy(category=category, location=location)) 
                  for _ in range(complaint_count)]
    
    # Density: 0 to 30 complaints per km²
    density = draw(st.floats(min_value=0.0, max_value=30.0))
    
    return Cluster(
        complaints=complaints,
        center_coordinates=(
            draw(st.floats(min_value=12.8, max_value=13.2)),
            draw(st.floats(min_value=77.4, max_value=77.8))
        ),
        radius_meters=500.0,
        density_per_km2=density,
        is_high_density=density >= 5.0,
        time_window_hours=24
    )


@st.composite
def weather_strategy(draw, high_rainfall=None):
    """Generate valid WeatherData."""
    precipitation = draw(st.floats(min_value=0.0, max_value=100.0))
    
    if high_rainfall is not None:
        high_rainfall_flag = high_rainfall
        if high_rainfall:
            precipitation = draw(st.floats(min_value=10.1, max_value=100.0))
        else:
            precipitation = draw(st.floats(min_value=0.0, max_value=10.0))
    else:
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
def traffic_strategy(draw, location, congestion_level=None):
    """Generate valid TrafficData for a location."""
    if congestion_level is None:
        congestion_level = draw(st.sampled_from([
            CongestionLevel.LOW,
            CongestionLevel.MEDIUM,
            CongestionLevel.HIGH
        ]))
    
    score_mapping = {
        CongestionLevel.LOW: 1,
        CongestionLevel.MEDIUM: 5,
        CongestionLevel.HIGH: 10
    }
    
    return TrafficData(
        location=location,
        congestion_level=congestion_level,
        congestion_score=score_mapping[congestion_level],
        timestamp=datetime.now()
    )


# ============================================================================
# Property 19: Risk Score Calculation Uses All Factors
# **Validates: Requirements 7.1**
# ============================================================================

@given(
    cluster=cluster_strategy(),
    weather=weather_strategy(),
    location=st.sampled_from(["Koramangala", "Indiranagar", "Whitefield"])
)
@settings(max_examples=100)
def test_property_19_risk_score_uses_all_factors(cluster, weather, location):
    """
    Property 19: Risk Score Calculation Uses All Factors
    
    For any zone, the Risk_Engine should calculate the Risk_Score using 
    complaint density, weather conditions, and traffic congestion 
    (all three factors should influence the score).
    
    **Validates: Requirements 7.1**
    """
    engine = RiskEngine()
    
    # Create traffic data
    traffic_data = {
        location: TrafficData(
            location=location,
            congestion_level=CongestionLevel.HIGH,
            congestion_score=10,
            timestamp=datetime.now()
        )
    }
    
    # Calculate score with no modifiers
    score_base = engine.calculate_risk_score(cluster, weather=None, traffic_data=None)
    
    # Calculate score with weather only
    score_with_weather = engine.calculate_risk_score(cluster, weather=weather, traffic_data=None)
    
    # Calculate score with traffic only
    score_with_traffic = engine.calculate_risk_score(cluster, weather=None, traffic_data=traffic_data)
    
    # Calculate score with all factors
    score_all = engine.calculate_risk_score(cluster, weather=weather, traffic_data=traffic_data)
    
    # All scores should be valid (0-100)
    assert 0.0 <= score_base <= 100.0
    assert 0.0 <= score_with_weather <= 100.0
    assert 0.0 <= score_with_traffic <= 100.0
    assert 0.0 <= score_all <= 100.0
    
    # Base score should depend on density
    expected_base = engine.calculate_base_score(cluster.density_per_km2)
    assert score_base == expected_base


# ============================================================================
# Property 20: Risk Score Bounds
# **Validates: Requirements 7.2**
# ============================================================================

@given(
    cluster=cluster_strategy(),
    weather=weather_strategy(),
    location=st.sampled_from(["Koramangala", "Indiranagar", "Whitefield"])
)
@settings(max_examples=100)
def test_property_20_risk_score_bounds(cluster, weather, location):
    """
    Property 20: Risk Score Bounds
    
    For any zone, the Risk_Engine should produce a Risk_Score value 
    between 0 and 100 (inclusive).
    
    **Validates: Requirements 7.2**
    """
    engine = RiskEngine()
    
    # Create traffic data with random congestion
    traffic_data = {
        location: TrafficData(
            location=location,
            congestion_level=CongestionLevel.HIGH,
            congestion_score=10,
            timestamp=datetime.now()
        )
    }
    
    # Calculate risk score with all factors
    score = engine.calculate_risk_score(cluster, weather=weather, traffic_data=traffic_data)
    
    # Score must be bounded 0-100
    assert 0.0 <= score <= 100.0, f"Score {score} out of bounds for density {cluster.density_per_km2}"


@given(density=st.floats(min_value=-100.0, max_value=1000.0))
@settings(max_examples=100)
def test_property_20_base_score_bounds(density):
    """
    Property 20: Risk Score Bounds (Base Score)
    
    For any complaint density value, the base score calculation 
    should produce a value between 0 and 100.
    
    **Validates: Requirements 7.2**
    """
    engine = RiskEngine()
    
    score = engine.calculate_base_score(density)
    
    # Score must always be bounded 0-100, even with extreme inputs
    assert 0.0 <= score <= 100.0, f"Base score {score} out of bounds for density {density}"


# ============================================================================
# Property 21: High Complaint Density Score Increase
# **Validates: Requirements 7.3**
# ============================================================================

@given(
    low_density=st.floats(min_value=0.0, max_value=4.9),
    high_density=st.floats(min_value=5.0, max_value=30.0)
)
@settings(max_examples=100)
def test_property_21_high_density_score_increase(low_density, high_density):
    """
    Property 21: High Complaint Density Score Increase
    
    For any zone, if complaint density exceeds 5 complaints per square kilometer, 
    the Risk_Engine should increase the Risk_Score by at least 20 points compared 
    to a zone with lower density (all other factors equal).
    
    **Validates: Requirements 7.3**
    """
    engine = RiskEngine()
    
    # Calculate scores for low and high density
    score_low = engine.calculate_base_score(low_density)
    score_high = engine.calculate_base_score(high_density)
    
    # High density should add at least 20 points
    # For density >= 5, we get 20 base points plus additional
    # For density < 5, we get density * 4
    assert score_high >= 20.0, f"High density score {score_high} should be >= 20"
    assert score_low < 20.0, f"Low density score {score_low} should be < 20"
    
    # The difference should be at least 20 - (low_density * 4)
    min_difference = 20.0 - score_low
    actual_difference = score_high - score_low
    assert actual_difference >= min_difference, \
        f"Difference {actual_difference} should be >= {min_difference}"


# ============================================================================
# Property 22: High Rainfall Flood Risk Increase
# **Validates: Requirements 7.4**
# ============================================================================

@given(
    density=st.floats(min_value=0.0, max_value=10.0),
    complaint_count=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
def test_property_22_high_rainfall_flood_risk_increase(density, complaint_count):
    """
    Property 22: High Rainfall Flood Risk Increase
    
    For any zone with flood-related complaints, if high rainfall conditions 
    are detected, the Risk_Engine should increase the Risk_Score by at least 
    30 points compared to the same zone without high rainfall.
    
    **Validates: Requirements 7.4**
    """
    engine = RiskEngine()
    
    # Create cluster with flooding complaints
    complaints = [
        Complaint(
            location="Koramangala",
            category="flooding",
            description=f"Flood complaint {i}",
            timestamp=datetime.now(),
            coordinates=(12.9352, 77.6245)
        )
        for i in range(complaint_count)
    ]
    
    cluster = Cluster(
        complaints=complaints,
        center_coordinates=(12.9352, 77.6245),
        radius_meters=500.0,
        density_per_km2=density,
        is_high_density=density >= 5.0,
        time_window_hours=24
    )
    
    # Weather without high rainfall
    weather_normal = WeatherData(
        temperature_celsius=25.0,
        humidity_percent=60.0,
        precipitation_mm_per_hour=5.0,
        wind_speed_kmh=10.0,
        high_rainfall_flag=False,
        timestamp=datetime.now(),
        source="test"
    )
    
    # Weather with high rainfall
    weather_high_rain = WeatherData(
        temperature_celsius=25.0,
        humidity_percent=80.0,
        precipitation_mm_per_hour=20.0,
        wind_speed_kmh=15.0,
        high_rainfall_flag=True,
        timestamp=datetime.now(),
        source="test"
    )
    
    # Calculate scores
    score_normal = engine.calculate_risk_score(cluster, weather=weather_normal)
    score_high_rain = engine.calculate_risk_score(cluster, weather=weather_high_rain)
    
    # High rainfall should add exactly 30 points (or capped at 100)
    expected_increase = min(30.0, 100.0 - score_normal)
    actual_increase = score_high_rain - score_normal
    
    # Use approximate equality to handle floating-point precision
    assert abs(actual_increase - expected_increase) < 0.01, \
        f"High rainfall should add {expected_increase} points, got {actual_increase}"


# ============================================================================
# Property 23: High Traffic Congestion Risk Increase
# **Validates: Requirements 7.5**
# ============================================================================

@given(
    density=st.floats(min_value=0.0, max_value=10.0),
    complaint_count=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
def test_property_23_high_traffic_risk_increase(density, complaint_count):
    """
    Property 23: High Traffic Congestion Risk Increase
    
    For any zone with traffic-related complaints, if traffic congestion is high, 
    the Risk_Engine should increase the Risk_Score by at least 15 points compared 
    to the same zone with low traffic.
    
    **Validates: Requirements 7.5**
    """
    engine = RiskEngine()
    
    location = "Koramangala"
    
    # Create cluster with traffic complaints
    complaints = [
        Complaint(
            location=location,
            category="traffic",
            description=f"Traffic complaint {i}",
            timestamp=datetime.now(),
            coordinates=(12.9352, 77.6245)
        )
        for i in range(complaint_count)
    ]
    
    cluster = Cluster(
        complaints=complaints,
        center_coordinates=(12.9352, 77.6245),
        radius_meters=500.0,
        density_per_km2=density,
        is_high_density=density >= 5.0,
        time_window_hours=24
    )
    
    # Traffic data with low congestion
    traffic_low = {
        location: TrafficData(
            location=location,
            congestion_level=CongestionLevel.LOW,
            congestion_score=1,
            timestamp=datetime.now()
        )
    }
    
    # Traffic data with high congestion
    traffic_high = {
        location: TrafficData(
            location=location,
            congestion_level=CongestionLevel.HIGH,
            congestion_score=10,
            timestamp=datetime.now()
        )
    }
    
    # Calculate scores
    score_low_traffic = engine.calculate_risk_score(cluster, traffic_data=traffic_low)
    score_high_traffic = engine.calculate_risk_score(cluster, traffic_data=traffic_high)
    
    # High traffic should add exactly 15 points (or capped at 100)
    expected_increase = min(15.0, 100.0 - score_low_traffic)
    actual_increase = score_high_traffic - score_low_traffic
    
    # Use approximate equality to handle floating-point precision
    assert abs(actual_increase - expected_increase) < 0.01, \
        f"High traffic should add {expected_increase} points, got {actual_increase}"


# ============================================================================
# Property 24: Risk Level Classification
# **Validates: Requirements 8.1**
# ============================================================================

@given(score=st.floats(min_value=0.0, max_value=100.0))
@settings(max_examples=100)
def test_property_24_risk_level_classification(score):
    """
    Property 24: Risk Level Classification
    
    For any Risk_Score value, the Risk_Engine should classify it as: 
    low-risk (0-33), medium-risk (34-66), or high-risk (67-100).
    
    **Validates: Requirements 8.1**
    """
    engine = RiskEngine()
    
    risk_level = engine.classify_risk_level(score)
    
    # Verify correct classification
    if score <= 33:
        assert risk_level == RiskLevel.LOW, \
            f"Score {score} should be LOW, got {risk_level}"
    elif score <= 66:
        assert risk_level == RiskLevel.MEDIUM, \
            f"Score {score} should be MEDIUM, got {risk_level}"
    else:
        assert risk_level == RiskLevel.HIGH, \
            f"Score {score} should be HIGH, got {risk_level}"


# ============================================================================
# Property 25: Risk Zone Filtering
# **Validates: Requirements 8.2**
# ============================================================================

@given(
    clusters=st.lists(
        cluster_strategy(min_complaints=1, max_complaints=5),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100)
def test_property_25_risk_zone_filtering(clusters):
    """
    Property 25: Risk Zone Filtering
    
    For any request for risk zones, the Dashboard_API should return only 
    zones with Risk_Score above 20.
    
    **Validates: Requirements 8.2**
    """
    engine = RiskEngine()
    
    # Create risk zones from clusters
    risk_zones = []
    for cluster in clusters:
        risk_zone = engine.create_risk_zone_from_cluster(cluster)
        risk_zones.append(risk_zone)
    
    # Update cache
    engine._risk_zones_cache = risk_zones
    
    # Get filtered zones (score > 20)
    filtered_zones = engine.get_filtered_risk_zones(min_score=20.0)
    
    # Verify all filtered zones have score > 20
    for zone in filtered_zones:
        assert zone.risk_score > 20.0, \
            f"Filtered zone has score {zone.risk_score} <= 20"
    
    # Verify no zones with score > 20 are excluded
    high_score_zones = [z for z in risk_zones if z.risk_score > 20.0]
    assert len(filtered_zones) == len(high_score_zones), \
        f"Expected {len(high_score_zones)} zones, got {len(filtered_zones)}"
    
    # Verify all zones with score <= 20 are excluded
    for zone in risk_zones:
        if zone.risk_score <= 20.0:
            assert zone not in filtered_zones, \
                f"Zone with score {zone.risk_score} should be filtered out"


# ============================================================================
# Additional Property Tests
# ============================================================================

@given(
    cluster=cluster_strategy(),
    weather=weather_strategy(),
    location=st.sampled_from(["Koramangala", "Indiranagar"])
)
@settings(max_examples=100)
def test_property_score_monotonicity_with_modifiers(cluster, weather, location):
    """
    Additional property: Adding modifiers should never decrease the score.
    
    This ensures that weather and traffic modifiers only add risk, never reduce it.
    """
    engine = RiskEngine()
    
    traffic_data = {
        location: TrafficData(
            location=location,
            congestion_level=CongestionLevel.HIGH,
            congestion_score=10,
            timestamp=datetime.now()
        )
    }
    
    # Calculate scores with increasing modifiers
    score_base = engine.calculate_risk_score(cluster)
    score_weather = engine.calculate_risk_score(cluster, weather=weather)
    score_traffic = engine.calculate_risk_score(cluster, traffic_data=traffic_data)
    score_all = engine.calculate_risk_score(cluster, weather=weather, traffic_data=traffic_data)
    
    # Base score should be <= score with any modifiers (unless capped at 100)
    if score_base < 100.0:
        assert score_weather >= score_base or score_weather == 100.0
        assert score_traffic >= score_base or score_traffic == 100.0
        assert score_all >= score_base or score_all == 100.0


@given(cluster=cluster_strategy())
@settings(max_examples=100)
def test_property_risk_zone_creation_consistency(cluster):
    """
    Additional property: Creating a risk zone should preserve cluster properties.
    
    This ensures that risk zone creation doesn't lose information.
    """
    engine = RiskEngine()
    
    risk_zone = engine.create_risk_zone_from_cluster(cluster)
    
    # Verify properties are preserved
    assert risk_zone.center_coordinates == cluster.center_coordinates
    assert risk_zone.radius_meters == cluster.radius_meters
    assert risk_zone.complaint_count == len(cluster.complaints)
    
    # Verify risk score is valid
    assert 0.0 <= risk_zone.risk_score <= 100.0
    
    # Verify risk level matches score
    expected_level = engine.classify_risk_level(risk_zone.risk_score)
    assert risk_zone.risk_level == expected_level


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
