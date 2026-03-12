"""
UrbanGuard AI System - FastAPI Backend
Main application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from storage import storage
from simulated_data import initialize_storage_with_simulated_data
from weather_integrator import get_weather_integrator
from traffic_analyzer import get_traffic_analyzer
from cluster_detector import get_cluster_detector
from risk_engine import get_risk_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize storage and start weather integrator and traffic analyzer on application startup"""
    # Initialize storage with simulated data
    complaint_count = initialize_storage_with_simulated_data(storage)
    print(f"✓ Initialized storage with {complaint_count} simulated complaints")
    
    # Start weather integrator background scheduler
    weather_integrator = get_weather_integrator()
    print(f"✓ Started weather integrator (fetch interval: {weather_integrator.FETCH_INTERVAL}s)")
    
    # Start traffic analyzer background scheduler
    traffic_analyzer = get_traffic_analyzer()
    print(f"✓ Started traffic analyzer (update interval: {traffic_analyzer.UPDATE_INTERVAL}s)")
    
    # Start cluster detector background scheduler
    cluster_detector = get_cluster_detector(
        get_complaints_callback=storage.get_all_complaints
    )
    print(f"✓ Started cluster detector (recalculation interval: {cluster_detector.RECALCULATION_INTERVAL}s)")
    
    # Start risk engine background scheduler
    risk_engine = get_risk_engine(
        get_clusters_callback=cluster_detector.get_cached_clusters,
        get_weather_callback=weather_integrator.fetch_weather_data,
        get_traffic_callback=traffic_analyzer.get_all_traffic_data,
        update_risk_zones_callback=storage.update_risk_zones
    )
    print(f"✓ Started risk engine (recalculation interval: {risk_engine.RECALCULATION_INTERVAL}s)")
    
    yield
    
    # Cleanup on shutdown
    weather_integrator.stop_scheduler()
    print("✓ Stopped weather integrator")
    
    traffic_analyzer.stop_scheduler()
    print("✓ Stopped traffic analyzer")
    
    cluster_detector.stop_scheduler()
    print("✓ Stopped cluster detector")
    
    risk_engine.stop_scheduler()
    print("✓ Stopped risk engine")


app = FastAPI(
    title="UrbanGuard AI System", 
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "UrbanGuard AI System API",
        "complaint_count": storage.get_complaint_count(),
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "complaints": storage.get_complaint_count(),
        "risk_zones": len(storage.get_all_risk_zones()),
        "reports": len(storage.get_all_reports())
    }


@app.get("/weather")
async def get_weather():
    """
    Get current weather data
    
    Returns:
        WeatherData with temperature, humidity, precipitation, wind speed
        
    Performance:
        < 100ms (returns cached data)
    """
    weather_integrator = get_weather_integrator()
    weather = weather_integrator.fetch_weather_data()
    
    return {
        "temperature_celsius": weather.temperature_celsius,
        "humidity_percent": weather.humidity_percent,
        "precipitation_mm_per_hour": weather.precipitation_mm_per_hour,
        "wind_speed_kmh": weather.wind_speed_kmh,
        "high_rainfall_flag": weather.high_rainfall_flag,
        "timestamp": weather.timestamp.isoformat(),
        "source": weather.source
    }


@app.get("/traffic")
async def get_traffic():
    """
    Get traffic congestion data for all locations
    
    Returns:
        List of TrafficData with location, congestion level, and score
        
    Performance:
        < 100ms (returns cached data)
    """
    traffic_analyzer = get_traffic_analyzer()
    all_traffic = traffic_analyzer.get_all_traffic_data()
    
    return [
        {
            "location": traffic.location,
            "congestion_level": traffic.congestion_level.value,
            "congestion_score": traffic.congestion_score,
            "timestamp": traffic.timestamp.isoformat()
        }
        for traffic in all_traffic.values()
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.get("/clusters")
async def get_clusters():
    """
    Get current complaint clusters
    
    Returns:
        List of clusters with density calculations and high-density flags
        
    Performance:
        < 100ms (returns cached data)
    """
    cluster_detector = get_cluster_detector()
    clusters = cluster_detector.get_cached_clusters()
    
    return [
        {
            "cluster_id": cluster.cluster_id,
            "center_coordinates": {
                "latitude": cluster.center_coordinates[0],
                "longitude": cluster.center_coordinates[1]
            },
            "radius_meters": cluster.radius_meters,
            "complaint_count": len(cluster.complaints),
            "density_per_km2": round(cluster.density_per_km2, 2),
            "is_high_density": cluster.is_high_density,
            "time_window_hours": cluster.time_window_hours,
            "complaints": [
                {
                    "complaint_id": c.complaint_id,
                    "location": c.location,
                    "category": c.category,
                    "description": c.description,
                    "timestamp": c.timestamp.isoformat()
                }
                for c in cluster.complaints
            ]
        }
        for cluster in clusters
    ]


@app.get("/risk-hotspots")
async def get_risk_hotspots():
    """
    Get risk zones with risk_score > 20
    
    Returns:
        List of RiskZone objects filtered by minimum score threshold
        
    Performance:
        < 300ms (returns cached data)
        
    Validates: Requirements 8.2, 8.3, 8.4
    """
    risk_engine = get_risk_engine()
    risk_zones = risk_engine.get_filtered_risk_zones(min_score=20.0)
    
    return [
        {
            "zone_id": zone.zone_id,
            "center_coordinates": {
                "latitude": zone.center_coordinates[0],
                "longitude": zone.center_coordinates[1]
            },
            "radius_meters": zone.radius_meters,
            "risk_score": round(zone.risk_score, 2),
            "risk_level": zone.risk_level.value,
            "complaint_count": zone.complaint_count,
            "dominant_category": zone.dominant_category,
            "last_updated": zone.last_updated.isoformat()
        }
        for zone in risk_zones
    ]
