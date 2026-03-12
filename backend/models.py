"""
UrbanGuard AI System - Data Models
Core data structures for complaints, risk zones, weather, traffic, predictions, and reports
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Tuple, Optional
from uuid import uuid4


class RiskLevel(Enum):
    """Risk level classification based on risk score"""
    LOW = "low"  # 0-33
    MEDIUM = "medium"  # 34-66
    HIGH = "high"  # 67-100


class CongestionLevel(Enum):
    """Traffic congestion level"""
    LOW = "low"  # score = 1
    MEDIUM = "medium"  # score = 5
    HIGH = "high"  # score = 10


@dataclass
class Complaint:
    """
    Citizen-submitted complaint about urban infrastructure issues.
    
    Attributes:
        complaint_id: Unique identifier (UUID)
        location: Must match predefined Bengaluru_Location
        category: One of 8 supported categories
        description: Free-text complaint details
        timestamp: Submission time
        coordinates: (latitude, longitude) tuple
        classification_confidence: AI classification confidence (0.0 - 1.0)
    """
    location: str
    category: str
    description: str
    timestamp: datetime
    coordinates: Tuple[float, float]
    complaint_id: str = field(default_factory=lambda: str(uuid4()))
    classification_confidence: float = 1.0
    
    # Supported categories
    CATEGORIES = [
        "pothole",
        "flooding",
        "traffic",
        "garbage",
        "streetlight",
        "water_supply",
        "noise",
        "construction"
    ]


@dataclass
class RiskZone:
    """
    Geographic area with calculated risk score.
    
    Attributes:
        zone_id: Unique identifier
        center_coordinates: (latitude, longitude) of zone center
        radius_meters: Zone radius (500m for clustering)
        risk_score: Calculated risk value (0-100)
        risk_level: Classification (LOW, MEDIUM, HIGH)
        complaint_count: Number of complaints in zone
        dominant_category: Most common complaint category
        last_updated: Last risk calculation timestamp
    """
    center_coordinates: Tuple[float, float]
    radius_meters: float
    risk_score: float
    risk_level: RiskLevel
    complaint_count: int
    dominant_category: str
    last_updated: datetime
    zone_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class WeatherData:
    """
    Weather conditions data from OpenWeatherMap API.
    
    Attributes:
        temperature_celsius: Temperature in Celsius
        humidity_percent: Relative humidity percentage
        precipitation_mm_per_hour: Rainfall in mm per hour
        wind_speed_kmh: Wind speed in km/h
        high_rainfall_flag: True if precipitation > 10mm/hr
        timestamp: Data retrieval timestamp
        source: Data source ("openweathermap" or "cache")
    """
    temperature_celsius: float
    humidity_percent: float
    precipitation_mm_per_hour: float
    wind_speed_kmh: float
    high_rainfall_flag: bool
    timestamp: datetime
    source: str = "openweathermap"


@dataclass
class TrafficData:
    """
    Traffic congestion data for a location.
    
    Attributes:
        location: Bengaluru location name
        congestion_level: Traffic congestion level (LOW, MEDIUM, HIGH)
        congestion_score: Numeric score (1, 5, or 10)
        timestamp: Data update timestamp
    """
    location: str
    congestion_level: CongestionLevel
    congestion_score: int
    timestamp: datetime


@dataclass
class IncidentPrediction:
    """
    Predicted urban incident for a high-risk zone.
    
    Attributes:
        prediction_id: Unique identifier
        zone_id: Associated risk zone ID
        incident_type: Type based on dominant complaint category
        risk_score: Zone risk score that triggered prediction
        time_window: Prediction timeframe ("next 6 hours" or "next 24 hours")
        contributing_factors: List of factors (e.g., ["high_rainfall", "complaint_density"])
        created_at: Prediction creation timestamp
    """
    zone_id: str
    incident_type: str
    risk_score: float
    time_window: str
    contributing_factors: List[str]
    created_at: datetime
    prediction_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class DailyReport:
    """
    Daily AI-generated civic risk report.
    
    Attributes:
        report_id: Unique identifier
        date: Report date
        total_complaints: Total complaint count
        high_risk_zones: List of high-risk zones
        predicted_incidents: List of incident predictions
        weather_summary: Weather conditions summary
        ai_generated_summary: Natural language risk pattern analysis
        created_at: Report creation timestamp
    """
    date: datetime
    total_complaints: int
    high_risk_zones: List[RiskZone]
    predicted_incidents: List[IncidentPrediction]
    weather_summary: str
    ai_generated_summary: str
    created_at: datetime
    report_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class Cluster:
    """
    Geographic cluster of complaints.
    
    Attributes:
        cluster_id: Unique identifier
        complaints: List of complaints in cluster
        center_coordinates: (latitude, longitude) of cluster center
        radius_meters: Cluster radius (500m)
        density_per_km2: Complaints per square kilometer
        is_high_density: True if 5+ complaints in 24h
        time_window_hours: Time window for clustering (24h)
    """
    complaints: List[Complaint]
    center_coordinates: Tuple[float, float]
    radius_meters: float
    density_per_km2: float
    is_high_density: bool
    time_window_hours: int
    cluster_id: str = field(default_factory=lambda: str(uuid4()))
