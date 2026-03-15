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
    HIGH_DENSITY_BONUS = 50  # points at threshold (density=5 → score=50)
    
    # Risk level classification thresholds
    LOW_RISK_MAX = 33
    MEDIUM_RISK_MAX = 66
    
    # Recalculation interval: 15 minutes (900 seconds)
    RECALCULATION_INTERVAL = 900
    
    # Minimum risk score for API filtering
    MIN_RISK_SCORE_THRESHOLD = 10.0
    
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

        # Cache for AI-generated prediction explanations keyed by zone_id+incident_type
        self._explanation_cache: dict = {}
        self._explanation_lock = Lock()
        
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
        """
        # Scale: density of 5/km² → 50 points, 10/km² → 75, 20/km² → 100
        if complaint_density >= self.HIGH_DENSITY_THRESHOLD:
            base_score = self.HIGH_DENSITY_BONUS
            excess_density = complaint_density - self.HIGH_DENSITY_THRESHOLD
            base_score += excess_density * 5
        else:
            # Linear scale up to threshold: 0 → 0, 5 → 50
            base_score = complaint_density * (self.HIGH_DENSITY_BONUS / self.HIGH_DENSITY_THRESHOLD)

        return max(0.0, min(100.0, base_score))
    
    def calculate_risk_score(
        self,
        cluster: Cluster,
        weather: Optional[WeatherData] = None,
        traffic_data: Optional[dict] = None
    ) -> float:
        """
        Calculate comprehensive risk score for a zone.
        Incorporates BBMP historical pattern insights when available.
        """
        # Calculate base score from complaint density
        base_score = self.calculate_base_score(cluster.density_per_km2)
        risk_score = base_score

        # Apply weather modifier
        if weather:
            risk_score += self._calculate_weather_modifier(cluster, weather)

        # Apply traffic modifier
        if traffic_data:
            risk_score += self._calculate_traffic_modifier(cluster, traffic_data)

        # Apply BBMP historical boosts (if Bedrock analysis has completed)
        try:
            from bbmp_data_loader import get_bbmp_insights
            insights = get_bbmp_insights()
            if insights:
                # Location-level boost for chronic hotspots
                boosts = insights.get("hotspot_risk_boosts", {})
                weights = insights.get("category_weights", {})

                # Find the dominant location in this cluster
                location_counts = {}
                for c in cluster.complaints:
                    location_counts[c.location] = location_counts.get(c.location, 0) + 1
                if location_counts:
                    dominant_location = max(location_counts, key=location_counts.get)
                    boost = boosts.get(dominant_location, 0)
                    if boost:
                        risk_score += boost
                        logger.debug(f"BBMP hotspot boost +{boost} for {dominant_location}")

                # Category weight multiplier on the base score
                dominant_cat = self._get_dominant_category(cluster.complaints)
                weight = weights.get(dominant_cat, 1.0)
                if weight != 1.0:
                    risk_score = base_score * weight + (risk_score - base_score)
                    logger.debug(f"BBMP category weight ×{weight} for {dominant_cat}")
        except Exception:
            pass  # Never let insights failure break scoring

        return max(0.0, min(100.0, risk_score))
    
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

        # Fire SNS alerts for any new HIGH risk zones
        try:
            from sns_notifier import notify_high_risk_zone
            from models import RiskLevel
            for zone in risk_zones:
                if zone.risk_level == RiskLevel.HIGH:
                    notify_high_risk_zone(zone)
        except Exception as e:
            logger.warning(f"SNS notification failed: {e}")

        # Kick off background explanation generation (non-blocking)
        Thread(target=self._generate_explanations_background, args=(risk_zones,), daemon=True).start()
        
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
    
    def get_explanation(self, zone_id: str, incident_type: str) -> Optional[str]:
        """Return cached AI explanation for a prediction, or None if not ready yet."""
        key = f"{zone_id}:{incident_type}"
        with self._explanation_lock:
            return self._explanation_cache.get(key)

    def _generate_explanations_background(self, zones: List[RiskZone]) -> None:
        """Generate Bedrock explanations for all zones in a background thread."""
        try:
            from ai_classifier import AIClassifier
            from incident_predictor import get_incident_predictor
            from weather_integrator import get_weather_integrator
            from traffic_analyzer import get_traffic_analyzer

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
            predictor = get_incident_predictor()
            weather = get_weather_integrator().fetch_weather_data()
            traffic = get_traffic_analyzer().get_all_traffic_data()
            predictions = predictor.predict_incidents(zones, weather, traffic)

            for pred in predictions:
                zone = next((z for z in zones if z.zone_id == pred.zone_id), None)
                if not zone:
                    continue
                lat, lng = zone.center_coordinates
                area_name = nearest_area(lat, lng)
                key = f"{pred.zone_id}:{pred.incident_type}"
                explanation = classifier.explain_prediction(
                    incident_type=pred.incident_type,
                    area_name=area_name,
                    risk_score=pred.risk_score,
                    dominant_category=zone.dominant_category,
                    complaint_count=zone.complaint_count,
                    contributing_factors=pred.contributing_factors,
                    time_window=pred.time_window,
                )
                with self._explanation_lock:
                    self._explanation_cache[key] = explanation
                logger.info(f"Cached explanation for {area_name} / {pred.incident_type}")
        except Exception as e:
            logger.warning(f"Background explanation generation failed: {e}")

    def get_cached_risk_zones(self) -> List[RiskZone]:
        """
        Get the most recently calculated risk zones from cache.
        Triggers a fresh calculation if cache is empty (startup race condition).

        Returns:
            List of cached risk zones
        """
        with self._cache_lock:
            cache = list(self._risk_zones_cache)

        if not cache:
            try:
                cache = self.calculate_all_risk_zones()
            except Exception as e:
                logger.warning(f"On-demand risk zone calculation failed: {e}")
                cache = []

        return cache
    
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
            cache = list(self._risk_zones_cache)

        # If cache is empty (startup race), trigger a fresh calculation now
        if not cache:
            try:
                cache = self.calculate_all_risk_zones()
            except Exception as e:
                logger.warning(f"On-demand risk zone calculation failed: {e}")
                cache = []

        return [zone for zone in cache if zone.risk_score > min_score]
    
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
