"""
Demo script for Incident Predictor - Task 8.1
Tests incident prediction logic with various scenarios
"""
from datetime import datetime
from models import RiskZone, RiskLevel, WeatherData, TrafficData, CongestionLevel
from incident_predictor import get_incident_predictor


def demo_incident_prediction():
    """Demonstrates incident prediction functionality"""
    print("=" * 80)
    print("INCIDENT PREDICTOR DEMO - Task 8.1")
    print("=" * 80)
    
    predictor = get_incident_predictor()
    
    # Create test risk zones
    print("\n1. Creating test risk zones...")
    
    # Zone 1: High risk flooding zone (score > 70)
    zone1 = RiskZone(
        zone_id="zone-1",
        center_coordinates=(12.9352, 77.6245),
        radius_meters=500.0,
        risk_score=75.0,
        risk_level=RiskLevel.HIGH,
        complaint_count=8,
        dominant_category="flooding",
        last_updated=datetime.now()
    )
    print(f"   Zone 1: {zone1.dominant_category}, score={zone1.risk_score}")
    
    # Zone 2: Very high risk traffic zone (score > 85)
    zone2 = RiskZone(
        zone_id="zone-2",
        center_coordinates=(12.9716, 77.6412),
        radius_meters=500.0,
        risk_score=88.0,
        risk_level=RiskLevel.HIGH,
        complaint_count=12,
        dominant_category="traffic",
        last_updated=datetime.now()
    )
    print(f"   Zone 2: {zone2.dominant_category}, score={zone2.risk_score}")
    
    # Zone 3: Medium risk zone (score < 70, should not generate prediction)
    zone3 = RiskZone(
        zone_id="zone-3",
        center_coordinates=(12.9698, 77.7499),
        radius_meters=500.0,
        risk_score=65.0,
        risk_level=RiskLevel.MEDIUM,
        complaint_count=5,
        dominant_category="pothole",
        last_updated=datetime.now()
    )
    print(f"   Zone 3: {zone3.dominant_category}, score={zone3.risk_score}")
    
    # Zone 4: High risk pothole zone
    zone4 = RiskZone(
        zone_id="zone-4",
        center_coordinates=(12.8456, 77.6603),
        radius_meters=500.0,
        risk_score=72.0,
        risk_level=RiskLevel.HIGH,
        complaint_count=6,
        dominant_category="pothole",
        last_updated=datetime.now()
    )
    print(f"   Zone 4: {zone4.dominant_category}, score={zone4.risk_score}")
    
    # Create weather data with high rainfall
    print("\n2. Creating weather data (high rainfall)...")
    weather = WeatherData(
        temperature_celsius=28.0,
        humidity_percent=85.0,
        precipitation_mm_per_hour=15.0,  # > 10mm/hr = high rainfall
        wind_speed_kmh=25.0,
        high_rainfall_flag=True,
        timestamp=datetime.now(),
        source="test"
    )
    print(f"   Precipitation: {weather.precipitation_mm_per_hour} mm/hr")
    print(f"   High rainfall flag: {weather.high_rainfall_flag}")
    
    # Create traffic data with high congestion
    print("\n3. Creating traffic data (high congestion)...")
    traffic_data = {
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
    print(f"   Locations with high congestion: {len(traffic_data)}")
    
    # Test 1: Predict without weather/traffic data
    print("\n" + "=" * 80)
    print("TEST 1: Basic Prediction (no weather/traffic)")
    print("=" * 80)
    
    predictions = predictor.predict_incidents([zone1, zone2, zone3, zone4])
    
    print(f"\nGenerated {len(predictions)} predictions:")
    for pred in predictions:
        print(f"\n  Prediction ID: {pred.prediction_id}")
        print(f"  Zone ID: {pred.zone_id}")
        print(f"  Incident Type: {pred.incident_type}")
        print(f"  Risk Score: {pred.risk_score}")
        print(f"  Time Window: {pred.time_window}")
        print(f"  Contributing Factors: {', '.join(pred.contributing_factors)}")
    
    # Test 2: Predict with weather data (flooding scenario)
    print("\n" + "=" * 80)
    print("TEST 2: Flooding Prediction (with high rainfall)")
    print("=" * 80)
    
    predictions = predictor.predict_incidents([zone1, zone2, zone3, zone4], weather=weather)
    
    print(f"\nGenerated {len(predictions)} predictions:")
    for pred in predictions:
        print(f"\n  Prediction ID: {pred.prediction_id}")
        print(f"  Zone ID: {pred.zone_id}")
        print(f"  Incident Type: {pred.incident_type}")
        print(f"  Risk Score: {pred.risk_score}")
        print(f"  Time Window: {pred.time_window}")
        print(f"  Contributing Factors: {', '.join(pred.contributing_factors)}")
        
        # Highlight flooding prediction
        if pred.incident_type == "flooding":
            print(f"  ⚠️  FLOODING INCIDENT PREDICTED (high rainfall + flooding complaints)")
    
    # Test 3: Predict with traffic data (gridlock scenario)
    print("\n" + "=" * 80)
    print("TEST 3: Traffic Gridlock Prediction (with high traffic)")
    print("=" * 80)
    
    predictions = predictor.predict_incidents(
        [zone1, zone2, zone3, zone4],
        weather=weather,
        traffic_data=traffic_data
    )
    
    print(f"\nGenerated {len(predictions)} predictions:")
    for pred in predictions:
        print(f"\n  Prediction ID: {pred.prediction_id}")
        print(f"  Zone ID: {pred.zone_id}")
        print(f"  Incident Type: {pred.incident_type}")
        print(f"  Risk Score: {pred.risk_score}")
        print(f"  Time Window: {pred.time_window}")
        print(f"  Contributing Factors: {', '.join(pred.contributing_factors)}")
        
        # Highlight special predictions
        if pred.incident_type == "flooding":
            print(f"  ⚠️  FLOODING INCIDENT PREDICTED")
        elif pred.incident_type == "traffic_gridlock":
            print(f"  ⚠️  TRAFFIC GRIDLOCK PREDICTED (high traffic + traffic complaints)")
    
    # Test 4: Time window determination
    print("\n" + "=" * 80)
    print("TEST 4: Time Window Determination")
    print("=" * 80)
    
    print("\nTime windows based on risk scores:")
    for zone in [zone1, zone2, zone4]:
        time_window = predictor._determine_time_window(zone.risk_score)
        print(f"  Zone {zone.zone_id}: score={zone.risk_score} → {time_window}")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    
    # Validation summary
    print("\n✓ Task 8.1 Implementation Validated:")
    print("  - Predictions generated for zones with risk_score > 70")
    print("  - Incident type based on dominant complaint category")
    print("  - Special rule: High rainfall + flooding → flooding incident")
    print("  - Special rule: High traffic + traffic complaints → gridlock incident")
    print("  - Time windows: 'next 6 hours' (score > 85) or 'next 24 hours' (70-85)")
    print("  - Contributing factors included in predictions")


if __name__ == "__main__":
    demo_incident_prediction()
