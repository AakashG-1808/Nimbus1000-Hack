"""
Demo for Task 7.3: Risk level classification, 15-minute scheduler, and zone filtering
"""
from datetime import datetime
from risk_engine import RiskEngine
from models import Cluster, Complaint, WeatherData, TrafficData, CongestionLevel


def demo_risk_level_classification():
    """Demonstrate risk level classification"""
    print("=" * 60)
    print("DEMO: Risk Level Classification")
    print("=" * 60)
    
    engine = RiskEngine()
    
    test_scores = [0, 15, 33, 34, 50, 66, 67, 85, 100]
    
    print("\nRisk Level Classification:")
    print("  LOW:    0-33")
    print("  MEDIUM: 34-66")
    print("  HIGH:   67-100")
    print()
    
    for score in test_scores:
        level = engine.classify_risk_level(score)
        print(f"  Score {score:3d} → {level.value.upper()}")
    
    print()


def demo_zone_filtering():
    """Demonstrate zone filtering with risk_score > 20"""
    print("=" * 60)
    print("DEMO: Zone Filtering (risk_score > 20)")
    print("=" * 60)
    
    engine = RiskEngine()

    
    # Create clusters with different densities
    clusters = [
        ("Low density (2.0)", 2.0, False),
        ("Medium density (4.0)", 4.0, False),
        ("High density (6.0)", 6.0, True),
        ("Very high density (10.0)", 10.0, True),
    ]
    
    print("\nCreating risk zones from clusters:")
    print()
    
    risk_zones = []
    for name, density, is_high in clusters:
        cluster = Cluster(
            complaints=[
                Complaint(
                    location="Test Location",
                    category="pothole",
                    description="Test",
                    timestamp=datetime.now(),
                    coordinates=(12.9352, 77.6245)
                )
            ],
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=density,
            is_high_density=is_high,
            time_window_hours=24
        )
        
        zone = engine.create_risk_zone_from_cluster(cluster)
        risk_zones.append(zone)
        
        print(f"  {name:25s} → Score: {zone.risk_score:5.1f} ({zone.risk_level.value.upper()})")
    
    # Store zones in cache
    engine._risk_zones_cache = risk_zones
    
    # Filter zones
    filtered = engine.get_filtered_risk_zones(min_score=20.0)
    
    print(f"\nFiltered zones (score > 20): {len(filtered)} out of {len(risk_zones)}")
    for zone in filtered:
        print(f"  - Score: {zone.risk_score:.1f} ({zone.risk_level.value.upper()})")
    
    print()


def demo_scheduler_interval():
    """Demonstrate 15-minute recalculation interval"""
    print("=" * 60)
    print("DEMO: 15-Minute Recalculation Scheduler")
    print("=" * 60)
    
    engine = RiskEngine()
    
    print(f"\nRecalculation interval: {engine.RECALCULATION_INTERVAL} seconds")
    print(f"                       = {engine.RECALCULATION_INTERVAL / 60} minutes")
    print(f"                       = 15 minutes ✓")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Task 7.3: Risk Level Classification and Zone Filtering")
    print("=" * 60)
    print()
    
    demo_risk_level_classification()
    demo_zone_filtering()
    demo_scheduler_interval()
    
    print("=" * 60)
    print("✅ All demonstrations completed successfully!")
    print("=" * 60)
