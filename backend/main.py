"""
UrbanGuard AI System - FastAPI Backend
Main application entry point
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from storage import storage
from simulated_data import initialize_storage_with_simulated_data
from weather_integrator import get_weather_integrator
from traffic_analyzer import get_traffic_analyzer
from cluster_detector import get_cluster_detector
from risk_engine import get_risk_engine
from error_handling import RequestLogger, ErrorResponse, log_error


# Initialize request logger
request_logger = RequestLogger(component="API")


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


# ============================================================================
# Middleware for Request Logging
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all HTTP requests with method, path, and response time.
    
    Validates: Requirement 20.4
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    # Log request
    request_logger.log_request(
        method=request.method,
        path=request.url.path,
        response_time_ms=response_time_ms,
        status_code=response.status_code,
        client_ip=request.client.host if request.client else None
    )
    
    return response


# ============================================================================
# Global Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with structured error responses.
    
    Validates: Requirement 20.5
    """
    log_error(
        component="API",
        message=f"HTTP {exc.status_code}: {exc.detail}",
        context={
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with graceful error responses.
    
    Validates: Requirement 20.3, 20.5
    """
    log_error(
        component="API",
        message=f"Unexpected error: {str(exc)}",
        error=exc,
        context={
            "method": request.method,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse.internal_error(
            "An unexpected error occurred. Please try again later."
        )
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


@app.post("/report-complaint")
async def report_complaint(complaint_data: dict):
    """
    Submit a new complaint
    
    Request body:
        {
            "location": str,
            "category": str,
            "description": str,
            "timestamp": str (ISO format)
        }
    
    Returns:
        {
            "success": bool,
            "complaint_id": str,
            "message": str
        }
        
    Performance:
        < 500ms for valid complaints
        < 100ms for invalid complaints (validation error)
        
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 17.1, 17.7, 20.5
    """
    from datetime import datetime
    from fastapi import HTTPException
    from complaint_processor import get_complaint_processor
    from error_handling import validate_required_fields, ErrorResponse
    
    try:
        # Validate required fields
        required_fields = ["location", "category", "description"]
        validation_error = validate_required_fields(complaint_data, required_fields)
        
        if validation_error:
            raise HTTPException(
                status_code=400,
                detail=validation_error
            )
        
        # Extract fields
        location = complaint_data.get("location")
        category = complaint_data.get("category")
        description = complaint_data.get("description")
        timestamp_str = complaint_data.get("timestamp")
        
        # Parse timestamp
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timestamp format: {str(e)}"
                )
        else:
            timestamp = datetime.now()
        
        # Submit complaint
        complaint_processor = get_complaint_processor()
        result = complaint_processor.submit_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        if result.success:
            return {
                "success": True,
                "complaint_id": result.complaint_id,
                "message": "Complaint submitted successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            component="API",
            message=f"Error submitting complaint: {str(e)}",
            error=e
        )
        raise HTTPException(status_code=500, detail="Failed to submit complaint")


@app.get("/complaints")
async def get_complaints():
    """
    Get all complaints sorted by timestamp descending
    
    Returns:
        List of complaints with coordinates for map visualization
        
    Performance:
        < 200ms for up to 1000 complaints
        
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 17.2, 17.7
    """
    from complaint_processor import get_complaint_processor
    
    complaint_processor = get_complaint_processor()
    complaints = complaint_processor.get_all_complaints()
    
    return [
        {
            "complaint_id": c.complaint_id,
            "location": c.location,
            "category": c.category,
            "description": c.description,
            "timestamp": c.timestamp.isoformat(),
            "coordinates": {
                "latitude": c.coordinates[0],
                "longitude": c.coordinates[1]
            },
            "classification_confidence": c.classification_confidence
        }
        for c in complaints
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


@app.get("/daily-report")
async def get_daily_report():
    """
    Get the most recent daily report
    
    Returns:
        DailyReport with statistics and AI-generated summary
        
    Performance:
        < 200ms
        
    Validates: Requirements 10.4, 10.5, 17.4
    """
    from report_generator import get_report_generator
    from fastapi import HTTPException
    
    report_generator = get_report_generator()
    report = report_generator.get_latest_report()
    
    if report is None:
        raise HTTPException(status_code=404, detail="No reports available")
    
    return {
        "report_id": report.report_id,
        "date": report.date.isoformat(),
        "total_complaints": report.total_complaints,
        "high_risk_zones": [
            {
                "zone_id": zone.zone_id,
                "center_coordinates": {
                    "latitude": zone.center_coordinates[0],
                    "longitude": zone.center_coordinates[1]
                },
                "risk_score": round(zone.risk_score, 2),
                "risk_level": zone.risk_level.value,
                "complaint_count": zone.complaint_count,
                "dominant_category": zone.dominant_category
            }
            for zone in report.high_risk_zones
        ],
        "predicted_incidents": [
            {
                "prediction_id": pred.prediction_id,
                "zone_id": pred.zone_id,
                "incident_type": pred.incident_type,
                "risk_score": round(pred.risk_score, 2),
                "time_window": pred.time_window,
                "contributing_factors": pred.contributing_factors
            }
            for pred in report.predicted_incidents
        ],
        "weather_summary": report.weather_summary,
        "ai_generated_summary": report.ai_generated_summary,
        "created_at": report.created_at.isoformat()
    }


@app.get("/predictions")
async def get_predictions():
    """
    Get current incident predictions for high-risk zones
    
    Returns:
        List of IncidentPrediction objects
        
    Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
    """
    from incident_predictor import get_incident_predictor
    from risk_engine import get_risk_engine
    from weather_integrator import get_weather_integrator
    from traffic_analyzer import get_traffic_analyzer
    
    # Get current risk zones
    risk_engine = get_risk_engine()
    risk_zones = risk_engine.get_cached_risk_zones()
    
    # Get weather and traffic data
    weather_integrator = get_weather_integrator()
    weather = weather_integrator.fetch_weather_data()
    
    traffic_analyzer = get_traffic_analyzer()
    traffic_data = traffic_analyzer.get_all_traffic_data()
    
    # Generate predictions
    incident_predictor = get_incident_predictor()
    predictions = incident_predictor.predict_incidents(
        risk_zones=risk_zones,
        weather=weather,
        traffic_data=traffic_data
    )
    
    return [
        {
            "prediction_id": pred.prediction_id,
            "zone_id": pred.zone_id,
            "incident_type": pred.incident_type,
            "risk_score": round(pred.risk_score, 2),
            "time_window": pred.time_window,
            "contributing_factors": pred.contributing_factors,
            "created_at": pred.created_at.isoformat()
        }
        for pred in predictions
    ]
