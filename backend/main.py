"""
UrbanGuard AI System - FastAPI Backend
Main application entry point
"""
import time
import os
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Query, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import APIRouter
from storage import storage
from simulated_data import initialize_storage_with_simulated_data
from weather_integrator import get_weather_integrator
from traffic_analyzer import get_traffic_analyzer
from cluster_detector import get_cluster_detector
from risk_engine import get_risk_engine
from error_handling import RequestLogger, ErrorResponse, log_error
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES


load_dotenv()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# API Router setup
api_router = APIRouter(prefix="/api/v1")


# Initialize request logger
request_logger = RequestLogger(component="API")


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = ConnectionManager()


class ComplaintSubmission(BaseModel):
    """Request body for complaint submission."""
    location: str = Field(..., min_length=1, description="Bengaluru location name")
    category: str = Field(..., min_length=1, description="Complaint category")
    description: str = Field(..., min_length=1, description="Complaint description")
    timestamp: Optional[datetime] = Field(default=None, description="ISO 8601 timestamp")
    coordinates: Optional[dict] = Field(default=None, description="Precise lat/lng from geocoding")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Description cannot be empty")
        return value


class ComplaintSubmissionResponse(BaseModel):
    """Response payload for complaint submission."""
    success: bool = Field(..., description="Submission status")
    complaint_id: str = Field(..., description="Created complaint ID")
    message: str = Field(..., description="Result message")


class ComplaintCoordinates(BaseModel):
    """Latitude/longitude coordinates for complaint location."""
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")


class ComplaintResponse(BaseModel):
    """Complaint response payload returned by /complaints."""
    complaint_id: str = Field(..., description="Complaint ID")
    location: str = Field(..., description="Bengaluru location name")
    category: str = Field(..., description="Complaint category")
    description: str = Field(..., description="Complaint description")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    coordinates: ComplaintCoordinates
    classification_confidence: float = Field(..., description="Classification confidence")
    status: str = Field(default="open", description="open or resolved")
    resolved_at: Optional[str] = Field(default=None)
    expected_resolution_date: Optional[str] = Field(default=None)
    resolution_note: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)


class ResolveComplaintRequest(BaseModel):
    """Request body for resolving a complaint (admin only)."""
    expected_resolution_date: Optional[str] = Field(default=None, description="ISO date string")
    resolution_note: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    mark_resolved: bool = Field(default=False)


def get_cors_origins() -> list[str]:
    """Read allowed CORS origins from environment settings."""
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS")
    if not raw_origins:
        return ["http://localhost:3000"]

    if raw_origins.strip() == "*":
        return ["*"]

    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


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
        get_complaints_callback=lambda: [c for c in storage.get_all_complaints() if getattr(c, 'status', 'open') == 'open']
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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "message": "UrbanGuard AI System API",
        "complaint_count": storage.get_complaint_count(),
        "status": "running",
        "websocket": "/ws"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Verify Bedrock is truly usable by making a lightweight API call
    # boto3.client() and even credential checks pass even without Bedrock access
    bedrock_active = False
    try:
        import boto3, json as _json, os as _os
        from botocore.config import Config as _Config
        aws_region = _os.getenv("AWS_BEDROCK_REGION", _os.getenv("AWS_REGION", "ap-south-2"))
        model_id = _os.getenv("BEDROCK_MODEL_ID", "apac.anthropic.claude-3-5-sonnet-20241022-v2:0")
        bedrock_api_key = _os.getenv("BEDROCK_API_KEY")
        # Build request body based on model family
        if "anthropic" in model_id.lower():
            body = _json.dumps({"anthropic_version": "bedrock-2023-05-31", "max_tokens": 5,
                                "messages": [{"role": "user", "content": "hi"}]})
        else:
            # Amazon Nova and others
            body = _json.dumps({"messages": [{"role": "user", "content": [{"text": "hi"}]}]})

        if bedrock_api_key:
            import requests as _requests
            url = f"https://bedrock-runtime.{aws_region}.amazonaws.com/model/{model_id}/invoke"
            resp = _requests.post(url,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {bedrock_api_key}"},
                data=body, timeout=5)
            bedrock_active = resp.status_code == 200
        else:
            client = boto3.client(
                service_name='bedrock-runtime', region_name=aws_region,
                config=_Config(connect_timeout=2, read_timeout=5, retries={'max_attempts': 0})
            )
            client.invoke_model(modelId=model_id, body=body)
            bedrock_active = True
    except Exception:
        bedrock_active = False

    return {
        "status": "healthy",
        "complaints": storage.get_complaint_count(),
        "risk_zones": len(storage.get_all_risk_zones()),
        "reports": len(storage.get_all_reports()),
        "classification_engine": "bedrock" if bedrock_active else "keyword_fallback"
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================

class AuthRequest(BaseModel):
    """Request body for login/signup."""
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)
    role: Optional[str] = Field(default="citizen")


@api_router.post("/auth/signup")
async def auth_signup(auth_data: AuthRequest):
    """Register a new user account."""
    from auth_middleware import signup_user
    try:
        result = signup_user(auth_data.email, auth_data.password, auth_data.role or "citizen")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/auth/login")
async def auth_login(auth_data: AuthRequest):
    """Login with email and password."""
    from auth_middleware import login_user
    try:
        result = login_user(auth_data.email, auth_data.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@api_router.get("/auth/me")
async def auth_me(request: Request):
    """Get current user info from token."""
    from auth_middleware import get_user_from_request
    auth_header = request.headers.get("Authorization")
    user = get_user_from_request(auth_header)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"email": user["email"], "role": user["role"]}


async def get_current_user_dep(request: Request):
    """FastAPI Dependency for token authentication."""
    from auth_middleware import get_user_from_request
    auth_header = request.headers.get("Authorization")
    user = get_user_from_request(auth_header)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@api_router.get("/weather")
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


@api_router.get("/traffic")
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


@api_router.post(
    "/report-complaint",
    response_model=ComplaintSubmissionResponse,
    responses={
        400: {"description": "Validation error"},
        422: {"description": "Request body validation error"},
        401: {"description": "Not authenticated"}
    }
)
@limiter.limit("5/minute")
async def report_complaint(
    request: Request,
    complaint_data: ComplaintSubmission,
    current_user: dict = Depends(get_current_user_dep)
):
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
    from fastapi import HTTPException
    from complaint_processor import get_complaint_processor
    
    try:
        # Extract fields
        location = complaint_data.location
        category = complaint_data.category
        description = complaint_data.description
        timestamp = complaint_data.timestamp or datetime.now()

        # Use geocoded coordinates from frontend if provided, else fall back to fixed lookup
        incoming_coords = complaint_data.coordinates
        if incoming_coords and "lat" in incoming_coords and "lng" in incoming_coords:
            precise_coords = (float(incoming_coords["lat"]), float(incoming_coords["lng"]))
        else:
            precise_coords = None
        
        # Submit complaint
        complaint_processor = get_complaint_processor()
        result = complaint_processor.submit_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp,
            coordinates=precise_coords
        )
        
        if result.success:
            # Trigger immediate cluster + risk zone recalculation so the map updates right away
            try:
                from cluster_detector import get_cluster_detector
                from risk_engine import get_risk_engine
                cd = get_cluster_detector()
                cd.recalculate_clusters()
                re = get_risk_engine()
                re.calculate_all_risk_zones()
            except Exception:
                pass  # Don't fail the submission if recalculation fails

            # Broadcast new complaint via WebSocket
            try:
                coords = precise_coords or BENGALURU_LOCATIONS.get(location, (12.9716, 77.5946))
                await ws_manager.broadcast({
                    "type": "new_complaint",
                    "complaint": {
                        "complaint_id": result.complaint_id,
                        "location": location,
                        "category": category,
                        "description": description,
                        "timestamp": timestamp.isoformat(),
                        "coordinates": {
                            "latitude": coords[0],
                            "longitude": coords[1]
                        },
                        "classification_confidence": getattr(result, 'classification_confidence', 1.0)
                    }
                })
            except Exception:
                pass  # Don't fail the HTTP response if broadcast fails
            
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


@api_router.get(
    "/complaints",
    response_model=list[ComplaintResponse],
    responses={
        400: {"description": "Invalid filter or time range"}
    }
)
async def get_complaints(
    location: Optional[str] = Query(default=None, description="Filter by Bengaluru location"),
    category: Optional[str] = Query(default=None, description="Filter by complaint category"),
    since: Optional[datetime] = Query(default=None, description="Filter complaints since this timestamp"),
    until: Optional[datetime] = Query(default=None, description="Filter complaints until this timestamp"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: Optional[int] = Query(default=None, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    Get all complaints sorted by timestamp descending
    
    Returns:
        List of complaints with coordinates for map visualization
        
    Performance:
        < 200ms for up to 1000 complaints
        
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 17.2, 17.7
    """
    from complaint_processor import get_complaint_processor
    
    if location and location not in BENGALURU_LOCATIONS:
        raise HTTPException(status_code=400, detail=f"Invalid location: {location}")

    if category and category not in COMPLAINT_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    if since and until and since > until:
        raise HTTPException(status_code=400, detail="Invalid time range: since is after until")

    complaint_processor = get_complaint_processor()
    complaints = complaint_processor.get_filtered_complaints(
        location=location,
        category=category,
        since=since,
        until=until,
        offset=offset,
        limit=limit
    )
    
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
            "classification_confidence": c.classification_confidence,
            "status": getattr(c, "status", "open"),
            "resolved_at": c.resolved_at.isoformat() if getattr(c, "resolved_at", None) else None,
            "expected_resolution_date": c.expected_resolution_date.isoformat() if getattr(c, "expected_resolution_date", None) else None,
            "resolution_note": getattr(c, "resolution_note", None),
            "image_url": getattr(c, "image_url", None),
        }
        for c in complaints
    ]


@api_router.patch("/complaints/{complaint_id}/resolve")
async def resolve_complaint(
    complaint_id: str,
    resolve_data: ResolveComplaintRequest,
    current_user: dict = Depends(get_current_user_dep)
):
    """Admin-only: update resolution details on a complaint.
    
    When mark_resolved=True, also bulk-resolves all other open complaints
    at the same location AND same category so the map circle fully disappears.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from storage import storage
    resolved_ids = []
    resolved_at = datetime.now()

    with storage._lock:
        complaint = next((c for c in storage._complaints if c.complaint_id == complaint_id), None)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        # Parse optional date once
        parsed_date = None
        if resolve_data.expected_resolution_date:
            try:
                parsed_date = datetime.fromisoformat(resolve_data.expected_resolution_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")

        def _apply_details(c):
            if parsed_date is not None:
                c.expected_resolution_date = parsed_date
            if resolve_data.resolution_note is not None:
                c.resolution_note = resolve_data.resolution_note
            if resolve_data.image_url is not None:
                c.image_url = resolve_data.image_url

        _apply_details(complaint)

        if resolve_data.mark_resolved:
            complaint.status = "resolved"
            complaint.resolved_at = resolved_at
            resolved_ids.append(complaint_id)

            # Bulk-resolve all other open complaints at same location + category
            for c in storage._complaints:
                if (
                    c.complaint_id != complaint_id
                    and getattr(c, 'status', 'open') == 'open'
                    and c.location == complaint.location
                    and c.category == complaint.category
                ):
                    _apply_details(c)
                    c.status = "resolved"
                    c.resolved_at = resolved_at
                    resolved_ids.append(c.complaint_id)

    # Force immediate recalculation so the map updates right away
    if resolve_data.mark_resolved:
        try:
            from cluster_detector import get_cluster_detector
            from risk_engine import get_risk_engine
            cd = get_cluster_detector()
            cd.recalculate_clusters()
            re = get_risk_engine()
            re.calculate_all_risk_zones()
        except Exception:
            pass  # Don't fail the response if recalculation fails

    return {
        "success": True,
        "complaint_id": complaint_id,
        "status": complaint.status,
        "resolved_count": len(resolved_ids),
        "resolved_ids": resolved_ids,
    }


@api_router.get("/clusters")
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


@api_router.get("/risk-hotspots")
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
    risk_zones = risk_engine.get_filtered_risk_zones(min_score=10.0)
    
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


@api_router.get("/daily-report")
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


@api_router.get("/predictions")
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
    risk_zones = risk_engine.get_filtered_risk_zones()
    
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
    
    # Build a zone_id → zone lookup for enriching predictions
    zone_map = {z.zone_id: z for z in risk_zones}

    from ai_classifier import AIClassifier

    BENGALURU_AREAS = [
        {"name": "Koramangala", "lat": 12.9352, "lng": 77.6245},
        {"name": "Indiranagar", "lat": 12.9784, "lng": 77.6408},
        {"name": "Whitefield", "lat": 12.9698, "lng": 77.7499},
        {"name": "Electronic City", "lat": 12.8399, "lng": 77.6770},
        {"name": "Marathahalli", "lat": 12.9591, "lng": 77.6974},
        {"name": "HSR Layout", "lat": 12.9116, "lng": 77.6389},
        {"name": "BTM Layout", "lat": 12.9166, "lng": 77.6101},
        {"name": "Jayanagar", "lat": 12.9308, "lng": 77.5838},
        {"name": "Banashankari", "lat": 12.9255, "lng": 77.5468},
        {"name": "Rajajinagar", "lat": 12.9907, "lng": 77.5530},
        {"name": "Malleshwaram", "lat": 13.0035, "lng": 77.5710},
        {"name": "Hebbal", "lat": 13.0350, "lng": 77.5970},
        {"name": "Yelahanka", "lat": 13.1007, "lng": 77.5963},
        {"name": "Bannerghatta", "lat": 12.8635, "lng": 77.5975},
        {"name": "Vijayanagar", "lat": 12.9719, "lng": 77.5322},
        {"name": "Yeshwanthpur", "lat": 13.0280, "lng": 77.5390},
        {"name": "JP Nagar", "lat": 12.9063, "lng": 77.5857},
        {"name": "Bellandur", "lat": 12.9257, "lng": 77.6762},
        {"name": "KR Puram", "lat": 13.0050, "lng": 77.6960},
        {"name": "City Center", "lat": 12.9716, "lng": 77.5946},
    ]

    def nearest_area(lat, lng):
        return min(BENGALURU_AREAS, key=lambda a: (a["lat"]-lat)**2 + (a["lng"]-lng)**2)["name"]

    classifier = AIClassifier()

    result = []
    for pred in predictions:
        zone = zone_map.get(pred.zone_id)
        coords = None
        area_name = "Bengaluru"
        if zone:
            lat, lng = zone.center_coordinates[0], zone.center_coordinates[1]
            coords = {"latitude": lat, "longitude": lng}
            area_name = nearest_area(lat, lng)

        # Use cached Bedrock explanation if ready, else fast fallback
        key = f"{pred.zone_id}:{pred.incident_type}"
        explanation = (
            risk_engine.get_explanation(pred.zone_id, pred.incident_type)
            or classifier._fallback_explanation(
                pred.incident_type, area_name, pred.risk_score,
                zone.complaint_count if zone else 0, pred.time_window
            )
        )

        result.append({
            "prediction_id": pred.prediction_id,
            "zone_id": pred.zone_id,
            "incident_type": pred.incident_type,
            "risk_score": round(pred.risk_score, 2),
            "time_window": pred.time_window,
            "contributing_factors": pred.contributing_factors,
            "created_at": pred.created_at.isoformat(),
            "coordinates": coords,
            "area_name": area_name,
            "explanation": explanation,
        })

    return result

@api_router.get("/bbmp-insights")
async def get_bbmp_insights():
    """
    Get Bedrock-generated analysis of the BBMP historical dataset.
    Returns hotspot risk boosts, category weights, seasonal warnings, and a summary.
    Returns 404 if no BBMP data has been loaded.
    """
    from bbmp_data_loader import get_bbmp_insights as _get_insights
    insights = _get_insights()
    if insights is None:
        raise HTTPException(
            status_code=404,
            detail="BBMP dataset not loaded. Place a BBMP CSV in backend/data/ and restart."
        )
    return insights


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
