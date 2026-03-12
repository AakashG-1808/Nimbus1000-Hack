"""
UrbanGuard AI System - Risk Engine
Calculates risk scores for urban zones based on complaint density, weather, and traffic
"""
import logging
import time
from datetime import datetime
from typing import List, Optional, Callable
from threading import Thread, Lock
from models import (
    RiskZone, RiskLevel, Cluster, Complaint,
    WeatherData, TrafficData
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Calculates risk scores (0-100) for urban zones.
    
    Risk scoring combines:
    - Base score from complaint density (5+ per km² → +20 points)
    - Weather modifiers (high rainfall → +30 points for flood-related)
    - Traffic modifiers (high congestion → +15 points for traffic-related)
    
    Features:
    - Recalculates all zones every 15 minutes
    - Classifies risk levels: LOW (0-33), MEDIUM (34-66), HIGH (67-100)
    - Ensures all scores are bounded 0-100
    - Filters zones with risk_score > 20 for API responses
    """
    
    # Risk score thresholds
    HIGH_DENSITY_THRESHOLD = 5.0  # complaints per km²
    HIGH_DENSITY_BONUS = 20  # points added for high density
    
    # Risk level classification thresholds
    LOW_RISK_MAX = 33
    MEDIUM_RISK_MAX = 66
    
    # Recalculation interval: 15 minutes (900 seconds)
    RECALCULATION_INTERVAL = 900
    
    # Minimum risk score for API filtering
    MIN_RISK_SCORE_THRESHOLD = 20.0
    
    def __init__(
        self,
        auto_start: bool = False,
        get_clusters_callback: Optional[Callable[[], List[Cluster]]] = None,
        get_weather_callback: Optional[Callable[[], WeatherData]] = None,
        get_traffic_callback: Optional[Callable[[], dict]] = None,
        update_risk_zones_callback: Optional[Callable[[List[RiskZone]], None]] = None
    ):
        """
        Initialize Risk Engine.
        
        Args:
            auto_start: Whether to start background scheduler automatically
            get_clusters_callback: Callback to retrieve current clusters
            get_weather_callback: Callback to retrieve current weather data
            get_traffic_callback: Callback to retrieve traffic data dict
            update_risk_zones_callback: Callback to update storage with new risk zones
        """
        self.get_clusters_callback = get_clusters_callback
        self.get_weather_callback = get_weather_callback
        self.get_traffic_callback = get_traffic_callback
        self.update_risk_zones_callback = update_risk_zones_callback
        
        # Cache for latest risk zones
        self._risk_zones_cache: List[RiskZone] = []
        self._cache_lock = Lock()
        
        # Background scheduler state
        self._scheduler_thread: Optional[Thread] = None
        self._scheduler_running = False
        
        if auto_start:
            self.start_scheduler()
    
    def calculate_base_score(
        self,
        complaint_density: float
    ) -> float:
        """
        Calculate base risk score from complaint density.
        
        Args:
            complaint_density: Complaints per square kilometer
            
        Returns:
            Base score (0-100)
            
        Logic:
            - If density >= 5 per km²: add 20 points
            - Otherwise: density * 4 (scales linearly up to threshold)
            - Capped at 100
            
        Validates: Requirements 7.1, 7.2, 7.3
        """
        if complaint_density >= self.HIGH_DENSITY_THRESHOLD:
            # High density: add bonus points
            base_score = self.HIGH_DENSITY_BONUS
            # Add additional points for density above threshold
            excess_density = complaint_density - self.HIGH_DENSITY_THRESHOLD
            base_score += excess_density * 4
        else:
            # Below threshold: scale linearly
            base_score = complaint_density * 4
        
        # Ensure bounded 0-100
        base_score = max(0.0, min(100.0, base_score))
        
        return base_score
    
    def calculate_risk_score(
        self,
        cluster: Cluster,
        weather: Optional[WeatherData] = None,
        traffic_data: Optional[dict] = None
    ) -> float:
        """
        Calculate comprehensive risk score for a zone.
        
        Args:
            cluster: Cluster with complaints and density
            weather: Current weather conditions (optional)
            traffic_data: Traffic data dict (location -> TrafficData) (optional)
            
        Returns:
            Risk score (0-100)
            
        Scoring Logic:
            - Base: Complaint density (5+ per km² → +20 points)
            - Weather: High rainfall (>10mm/hr) → +30 points for flood-related
            - Traffic: High congestion → +15 points for traffic-related
            
        Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Calculate base score from complaint density
        base_score = self.calculate_base_score(cluster.density_per_km2)
        
        # Start with base score
        risk_score = base_score
        
        # Apply weather modifier (if weather data provided)
        if weather:
            weather_modifier = self._calculate_weather_modifier(cluster, weather)
            risk_score += weather_modifier
        
        # Apply traffic modifier (if traffic data provided)
        if traffic_data:
            traffic_modifier = self._calculate_traffic_modifier(cluster, traffic_data)
            risk_score += traffic_modifier
        
        # Ensure bounded 0-100
        risk_score = max(0.0, min(100.0, risk_score))
        
        logger.debug(
            f"Risk score calculated: base={base_score:.1f}, "
            f"final={risk_score:.1f} for cluster {cluster.cluster_id}"
        )
        
        return risk_score
    
    def _calculate_weather_modifier(
        self,
        cluster: Cluster,
        weather: WeatherData
    ) -> float:
        """
        Calculate weather-based risk modifier.
        
        Args:
            cluster: Cluster with complaints
            weather: Current weather conditions
            
        Returns:
            Weather modifier points (0-30)
            
        Logic:
            - High rainfall + flooding complaints → +30 points
            
        Validates: Requirement 7.4
        """
        modifier = 0.0
        
        # Check for high rainfall conditions
        if weather.high_rainfall_flag:
            # Check if cluster has flood-related complaints
            flood_complaints = [
                c for c in cluster.complaints
                if c.category == "flooding"
            ]
            
            if flood_complaints:
                modifier += 30.0
                logger.info(
                    f"High rainfall + {len(flood_complaints)} flooding complaints: "
                    f"+30 points for cluster {cluster.cluster_id}"
                )
        
        return modifier
    
    def _calculate_traffic_modifier(
        self,
        cluster: Cluster,
        traffic_data: dict
    ) -> float:
        """
        Calculate traffic-based risk modifier.
        
        Args:
            cluster: Cluster with complaints
            traffic_data: Traffic data dict (location -> TrafficData)
            
        Returns:
            Traffic modifier points (0-15)
            
        Logic:
            - High traffic congestion + traffic complaints → +15 points
            
        Validates: Requirement 7.5
        """
        modifier = 0.0
        
        # Check if cluster has traffic-related complaints
        traffic_complaints = [
            c for c in cluster.complaints
            if c.category == "traffic"
        ]
        
        if not traffic_complaints:
            return modifier
        
        # Check traffic congestion for complaint locations
        high_congestion_found = False
        
        for complaint in traffic_complaints:
            location = complaint.location
            
            if location in traffic_data:
                traffic = traffic_data[location]
                
                # Check for high congestion (score = 10)
                if traffic.congestion_score == 10:
                    high_congestion_found = True
                    break
        
        if high_congestion_found:
            modifier += 15.0
            logger.info(
                f"High traffic congestion + {len(traffic_complaints)} traffic complaints: "
                f"+15 points for cluster {cluster.cluster_id}"
            )
        
        return modifier
    
    def classify_risk_level(self, score: float) -> RiskLevel:
        """
        Classify risk level based on score.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            RiskLevel classification
            
        Classification:
            - LOW: 0-33
            - MEDIUM: 34-66
            - HIGH: 67-100
            
        Validates: Requirement 8.1
        """
        if score <= self.LOW_RISK_MAX:
            return RiskLevel.LOW
        elif score <= self.MEDIUM_RISK_MAX:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def create_risk_zone_from_cluster(
        self,
        cluster: Cluster,
        weather: Optional[WeatherData] = None,
        traffic_data: Optional[dict] = None
    ) -> RiskZone:
        """
        Create a RiskZone from a Cluster with calculated risk score.
        
        Args:
            cluster: Cluster to convert
            weather: Current weather conditions (optional)
            traffic_data: Traffic data dict (optional)
            
        Returns:
            RiskZone with calculated risk score and level
        """
        # Calculate risk score
        risk_score = self.calculate_risk_score(cluster, weather, traffic_data)
        
        # Classify risk level
        risk_level = self.classify_risk_level(risk_score)
        
        # Determine dominant category
        dominant_category = self._get_dominant_category(cluster.complaints)
        
        # Create RiskZone
        risk_zone = RiskZone(
            center_coordinates=cluster.center_coordinates,
            radius_meters=cluster.radius_meters,
            risk_score=risk_score,
            risk_level=risk_level,
            complaint_count=len(cluster.complaints),
            dominant_category=dominant_category,
            last_updated=datetime.now()
        )
        
        return risk_zone
    
    def _get_dominant_category(self, complaints: List[Complaint]) -> str:
        """
        Determine the dominant complaint category in a list.
        
        Args:
            complaints: List of complaints
            
        Returns:
            Most common category, or "mixed" if empty
        """
        if not complaints:
            return "mixed"
        
        # Count categories
        category_counts = {}
        for complaint in complaints:
            category = complaint.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Find most common
        dominant_category = max(category_counts, key=category_counts.get)
        
        return dominant_category
    
    def calculate_all_risk_zones(self) -> List[RiskZone]:
        """
        Calculate risk zones for all current clusters.
        
        Uses callbacks to retrieve clusters, weather, and traffic data,
        then calculates risk scores for each cluster.
        
        Returns:
            List of RiskZone objects with calculated scores
            
        Raises:
            RuntimeError: If required callbacks are not configured
        """
        if self.get_clusters_callback is None:
            raise RuntimeError(
                "Cannot calculate risk zones: no get_clusters_callback configured"
            )
        
        # Get current clusters
        clusters = self.get_clusters_callback()
        
        if not clusters:
            logger.info("No clusters found, returning empty risk zones list")
            return []
        
        # Get weather data (optional)
        weather = None
        if self.get_weather_callback:
            try:
                weather = self.get_weather_callback()
            except Exception as e:
                logger.warning(f"Failed to get weather data: {e}")
        
        # Get traffic data (optional)
        traffic_data = None
        if self.get_traffic_callback:
            try:
                traffic_data = self.get_traffic_callback()
            except Exception as e:
                logger.warning(f"Failed to get traffic data: {e}")
        
        # Calculate risk zones for each cluster
        risk_zones = []
        for cluster in clusters:
            risk_zone = self.create_risk_zone_from_cluster(
                cluster,
                weather=weather,
                traffic_data=traffic_data
            )
            risk_zones.append(risk_zone)
        
        # Update cache
        with self._cache_lock:
            self._risk_zones_cache = risk_zones
        
        # Update storage if callback provided
        if self.update_risk_zones_callback:
            try:
                self.update_risk_zones_callback(risk_zones)
            except Exception as e:
                logger.error(f"Failed to update risk zones in storage: {e}")
        
        logger.info(
            f"Calculated {len(risk_zones)} risk zones: "
            f"{sum(1 for z in risk_zones if z.risk_level == RiskLevel.LOW)} low, "
            f"{sum(1 for z in risk_zones if z.risk_level == RiskLevel.MEDIUM)} medium, "
            f"{sum(1 for z in risk_zones if z.risk_level == RiskLevel.HIGH)} high"
        )
        
        return risk_zones
    
    def get_cached_risk_zones(self) -> List[RiskZone]:
        """
        Get the most recently calculated risk zones from cache.
        
        Returns:
            List of cached risk zones
        """
        with self._cache_lock:
            return self._risk_zones_cache.copy()
    
    def get_filtered_risk_zones(self, min_score: float = None) -> List[RiskZone]:
        """
        Get risk zones filtered by minimum score threshold.
        
        Args:
            min_score: Minimum risk score threshold (default: 20.0)
            
        Returns:
            List of risk zones with score > min_score (strictly greater than)
            
        Validates: Requirement 8.2
        """
        if min_score is None:
            min_score = self.MIN_RISK_SCORE_THRESHOLD
        
        with self._cache_lock:
            return [
                zone for zone in self._risk_zones_cache
                if zone.risk_score > min_score
            ]
    
    def start_scheduler(self) -> None:
        """
        Starts background scheduler to recalculate risk zones every 15 minutes.
        
        Requires get_clusters_callback to be configured.
        
        Validates: Requirement 7.6
        """
        if self._scheduler_running:
            logger.warning("Risk Engine scheduler already running")
            return
        
        if self.get_clusters_callback is None:
            logger.error(
                "Cannot start scheduler: no get_clusters_callback configured"
            )
            return
        
        self._scheduler_running = True
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info(
            f"Started risk zone recalculation scheduler "
            f"(interval: {self.RECALCULATION_INTERVAL}s)"
        )
    
    def stop_scheduler(self) -> None:
        """
        Stops background scheduler.
        """
        if not self._scheduler_running:
            return
        
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        logger.info("Stopped risk zone recalculation scheduler")
    
    def _scheduler_loop(self) -> None:
        """
        Background scheduler loop that recalculates risk zones periodically.
        """
        # Calculate immediately on start
        try:
            self.calculate_all_risk_zones()
        except Exception as e:
            logger.error(f"Error in initial risk zone calculation: {e}")
        
        # Continue recalculating at intervals
        while self._scheduler_running:
            time.sleep(self.RECALCULATION_INTERVAL)
            
            if not self._scheduler_running:
                break
            
            try:
                self.calculate_all_risk_zones()
            except Exception as e:
                logger.error(f"Error in risk zone recalculation: {e}")


# Global risk engine instance
_risk_engine: Optional[RiskEngine] = None


def get_risk_engine(
    get_clusters_callback: Optional[Callable[[], List[Cluster]]] = None,
    get_weather_callback: Optional[Callable[[], WeatherData]] = None,
    get_traffic_callback: Optional[Callable[[], dict]] = None,
    update_risk_zones_callback: Optional[Callable[[List[RiskZone]], None]] = None
) -> RiskEngine:
    """
    Gets or creates the global RiskEngine instance.
    
    Args:
        get_clusters_callback: Callback to retrieve current clusters (required on first call)
        get_weather_callback: Callback to retrieve weather data (optional)
        get_traffic_callback: Callback to retrieve traffic data (optional)
        update_risk_zones_callback: Callback to update storage (optional)
    
    Returns:
        RiskEngine singleton instance
    """
    global _risk_engine
    
    if _risk_engine is None:
        _risk_engine = RiskEngine(
            auto_start=True,
            get_clusters_callback=get_clusters_callback,
            get_weather_callback=get_weather_callback,
            get_traffic_callback=get_traffic_callback,
            update_risk_zones_callback=update_risk_zones_callback
        )
    
    return _risk_engine
