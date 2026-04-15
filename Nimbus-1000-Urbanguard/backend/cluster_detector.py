"""
UrbanGuard AI System - Cluster Detector
Identifies geographic clusters of complaints using Haversine distance calculation
"""
import math
import time
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Callable
from threading import Thread, Lock
from models import Complaint, Cluster

logger = logging.getLogger(__name__)


class ClusterDetector:
    """
    Detects geographic clusters of complaints within specified radius and time window.
    
    Uses Haversine formula to calculate distances between coordinates and groups
    complaints within 500 meters of each other.
    
    Features:
    - Recalculates clusters every 15 minutes via background scheduler
    - Calculates complaint density per square kilometer
    - Flags high-density clusters (5+ complaints in 24h)
    """
    
    # Recalculation interval: 15 minutes (900 seconds)
    RECALCULATION_INTERVAL = 900
    
    def __init__(
        self,
        radius_meters: float = 500.0,
        time_window_hours: int = 24,
        auto_start: bool = False,
        get_complaints_callback: Optional[Callable[[], List[Complaint]]] = None
    ):
        """
        Initialize ClusterDetector with clustering parameters.
        
        Args:
            radius_meters: Maximum distance for grouping complaints (default 500m)
            time_window_hours: Time window for filtering complaints (default 24h)
            auto_start: Whether to start background scheduler automatically
            get_complaints_callback: Callback function to retrieve complaints for recalculation
        """
        self.radius_meters = radius_meters
        self.time_window_hours = time_window_hours
        self.get_complaints_callback = get_complaints_callback
        
        # Cache for latest clusters
        self._clusters_cache: List[Cluster] = []
        self._cache_lock = Lock()
        
        # Background scheduler state
        self._scheduler_thread: Optional[Thread] = None
        self._scheduler_running = False
        
        if auto_start:
            self.start_scheduler()
    
    def haversine_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """
        Calculate the great-circle distance between two points on Earth.
        
        Uses the Haversine formula to compute distance between two geographic
        coordinates specified as (latitude, longitude) tuples.
        
        Args:
            coord1: First coordinate as (latitude, longitude) in degrees
            coord2: Second coordinate as (latitude, longitude) in degrees
            
        Returns:
            Distance in meters between the two coordinates
            
        Formula:
            a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
            c = 2 * atan2(√a, √(1-a))
            d = R * c
            
            where R is Earth's radius (6371 km)
        """
        # Earth's radius in meters
        R = 6371000
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def filter_by_time_window(
        self,
        complaints: List[Complaint],
        reference_time: datetime = None
    ) -> List[Complaint]:
        """
        Filter complaints to only include those within the time window.
        
        Args:
            complaints: List of all complaints
            reference_time: Reference time for filtering (default: current time)
            
        Returns:
            List of complaints within time_window_hours of reference_time
        """
        if reference_time is None:
            reference_time = datetime.now()
        
        cutoff_time = reference_time - timedelta(hours=self.time_window_hours)
        
        return [
            complaint for complaint in complaints
            if complaint.timestamp >= cutoff_time
        ]
    
    def calculate_cluster_center(
        self,
        complaints: List[Complaint]
    ) -> Tuple[float, float]:
        """
        Calculate the geographic center (centroid) of a cluster.
        
        Computes the mean latitude and longitude of all complaints in the cluster.
        
        Args:
            complaints: List of complaints in the cluster
            
        Returns:
            Center coordinates as (latitude, longitude) tuple
        """
        if not complaints:
            return (0.0, 0.0)
        
        total_lat = sum(complaint.coordinates[0] for complaint in complaints)
        total_lon = sum(complaint.coordinates[1] for complaint in complaints)
        
        count = len(complaints)
        center_lat = total_lat / count
        center_lon = total_lon / count
        
        return (center_lat, center_lon)
    
    def calculate_density(self, cluster: Cluster) -> float:
        """
        Calculate complaint density per square kilometer for a cluster.
        
        Args:
            cluster: Cluster with complaints and radius
            
        Returns:
            Density as complaints per square kilometer
            
        Formula:
            area = π * r²  (where r is radius in km)
            density = complaint_count / area
        """
        # Convert radius from meters to kilometers
        radius_km = cluster.radius_meters / 1000.0
        
        # Calculate area in square kilometers
        area_km2 = math.pi * (radius_km ** 2)
        
        # Calculate density
        complaint_count = len(cluster.complaints)
        density = complaint_count / area_km2 if area_km2 > 0 else 0.0
        
        return density
    
    def detect_clusters(
        self,
        complaints: List[Complaint],
        time_window_hours: int = None
    ) -> List[Cluster]:
        """
        Group complaints within radius into clusters.
        
        Uses a simple greedy clustering algorithm:
        1. Filter complaints by time window
        2. For each unassigned complaint, create a new cluster
        3. Add all nearby complaints (within radius) to the cluster
        4. Calculate cluster center, density, and high-density flag
        
        Args:
            complaints: All complaints to analyze
            time_window_hours: Override default time window (optional)
            
        Returns:
            List of clusters with density calculations and flags
            
        Logic:
            - Groups complaints within radius_meters of each other
            - Calculates density per square kilometer
            - Flags clusters with 5+ complaints as high-density
        """
        # Use instance time window if not overridden
        if time_window_hours is None:
            time_window_hours = self.time_window_hours
        
        # Filter complaints by time window
        recent_complaints = self.filter_by_time_window(complaints)
        
        if not recent_complaints:
            return []
        
        # Track which complaints have been assigned to clusters
        assigned = set()
        clusters = []
        
        for complaint in recent_complaints:
            # Skip if already assigned to a cluster
            if complaint.complaint_id in assigned:
                continue
            
            # Start a new cluster with this complaint
            cluster_complaints = [complaint]
            assigned.add(complaint.complaint_id)
            
            # Find all other complaints within radius
            for other_complaint in recent_complaints:
                if other_complaint.complaint_id in assigned:
                    continue
                
                distance = self.haversine_distance(
                    complaint.coordinates,
                    other_complaint.coordinates
                )
                
                if distance <= self.radius_meters:
                    cluster_complaints.append(other_complaint)
                    assigned.add(other_complaint.complaint_id)
            
            # Calculate cluster center
            center = self.calculate_cluster_center(cluster_complaints)
            
            # Create cluster object
            cluster = Cluster(
                complaints=cluster_complaints,
                center_coordinates=center,
                radius_meters=self.radius_meters,
                density_per_km2=0.0,  # Will be calculated next
                is_high_density=False,  # Will be determined next
                time_window_hours=time_window_hours
            )
            
            # Calculate density
            cluster.density_per_km2 = self.calculate_density(cluster)
            
            # Flag high-density clusters (5+ complaints)
            cluster.is_high_density = len(cluster_complaints) >= 5
            
            clusters.append(cluster)
        
        return clusters

    def get_cached_clusters(self) -> List[Cluster]:
        """
        Get the most recently calculated clusters from cache.
        
        Returns:
            List of cached clusters
        """
        with self._cache_lock:
            return self._clusters_cache.copy()
    
    def recalculate_clusters(self) -> List[Cluster]:
        """
        Recalculate clusters using the callback function.
        
        Returns:
            List of newly calculated clusters
            
        Raises:
            RuntimeError: If no get_complaints_callback is configured
        """
        if self.get_complaints_callback is None:
            raise RuntimeError(
                "Cannot recalculate clusters: no get_complaints_callback configured"
            )
        
        # Get all complaints via callback
        complaints = self.get_complaints_callback()
        
        # Detect clusters
        clusters = self.detect_clusters(complaints)
        
        # Update cache
        with self._cache_lock:
            self._clusters_cache = clusters
        
        logger.info(
            f"Recalculated clusters: {len(clusters)} clusters found, "
            f"{sum(1 for c in clusters if c.is_high_density)} high-density"
        )
        
        return clusters
    
    def start_scheduler(self) -> None:
        """
        Starts background scheduler to recalculate clusters every 15 minutes.
        
        Requires get_complaints_callback to be configured.
        """
        if self._scheduler_running:
            logger.warning("Scheduler already running")
            return
        
        if self.get_complaints_callback is None:
            logger.error(
                "Cannot start scheduler: no get_complaints_callback configured"
            )
            return
        
        self._scheduler_running = True
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info(
            f"Started cluster recalculation scheduler "
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
        
        logger.info("Stopped cluster recalculation scheduler")
    
    def _scheduler_loop(self) -> None:
        """
        Background scheduler loop that recalculates clusters periodically.
        """
        # Recalculate immediately on start
        try:
            self.recalculate_clusters()
        except Exception as e:
            logger.error(f"Error in initial cluster recalculation: {e}")
        
        # Continue recalculating at intervals
        while self._scheduler_running:
            time.sleep(self.RECALCULATION_INTERVAL)
            
            if not self._scheduler_running:
                break
            
            try:
                self.recalculate_clusters()
            except Exception as e:
                logger.error(f"Error in cluster recalculation: {e}")


# Singleton instance for global access
_cluster_detector_instance: Optional[ClusterDetector] = None


def get_cluster_detector(
    get_complaints_callback: Optional[Callable[[], List[Complaint]]] = None
) -> ClusterDetector:
    """
    Get or create the singleton ClusterDetector instance.
    
    Args:
        get_complaints_callback: Callback function to retrieve complaints (required on first call)
        
    Returns:
        ClusterDetector singleton instance
    """
    global _cluster_detector_instance
    
    if _cluster_detector_instance is None:
        _cluster_detector_instance = ClusterDetector(
            radius_meters=500.0,
            time_window_hours=24,
            auto_start=True,
            get_complaints_callback=get_complaints_callback
        )
    
    return _cluster_detector_instance
