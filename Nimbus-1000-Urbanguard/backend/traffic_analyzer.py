"""
UrbanGuard AI System - Traffic Analyzer
Processes traffic congestion data for Bengaluru locations
"""
import logging
import random
import time
from datetime import datetime
from threading import Thread, Lock
from typing import Dict, Optional

from models import TrafficData, CongestionLevel
from constants import BENGALURU_LOCATIONS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrafficAnalyzer:
    """
    Processes traffic congestion data for Bengaluru locations.
    
    Features:
    - Updates traffic data every 10 minutes via background scheduler
    - Assigns congestion levels (LOW, MEDIUM, HIGH) for all locations
    - Maps congestion levels to scores (low=1, medium=5, high=10)
    - Provides traffic data within 50ms from cache
    - Simulates realistic traffic patterns for development
    """
    
    # Update interval in seconds (10 minutes)
    UPDATE_INTERVAL = 10 * 60
    
    # Congestion score mapping
    CONGESTION_SCORES = {
        CongestionLevel.LOW: 1,
        CongestionLevel.MEDIUM: 5,
        CongestionLevel.HIGH: 10
    }
    
    def __init__(self, auto_start: bool = True):
        """
        Initialize Traffic Analyzer.
        
        Args:
            auto_start: Whether to start background scheduler automatically
        """
        # Cache for traffic data (location -> TrafficData)
        self._traffic_cache: Dict[str, TrafficData] = {}
        self._cache_lock = Lock()
        
        # Background scheduler state
        self._scheduler_thread: Optional[Thread] = None
        self._scheduler_running = False
        
        # Initialize traffic data for all locations
        self._initialize_traffic_data()
        
        if auto_start:
            self.start_scheduler()
    
    def _initialize_traffic_data(self) -> None:
        """
        Initializes traffic data for all Bengaluru locations.
        """
        logger.info("Initializing traffic data for all locations")
        
        with self._cache_lock:
            for location in BENGALURU_LOCATIONS.keys():
                # Generate initial random congestion level
                congestion_level = self._generate_congestion_level()
                congestion_score = self.CONGESTION_SCORES[congestion_level]
                
                self._traffic_cache[location] = TrafficData(
                    location=location,
                    congestion_level=congestion_level,
                    congestion_score=congestion_score,
                    timestamp=datetime.now()
                )
        
        logger.info(f"Initialized traffic data for {len(self._traffic_cache)} locations")
    
    def get_traffic_data(self, location: str) -> TrafficData:
        """
        Provides traffic congestion level for a location.
        
        Args:
            location: Bengaluru location identifier
            
        Returns:
            TrafficData with congestion level and score
            
        Raises:
            ValueError: If location is not in BENGALURU_LOCATIONS
            
        Performance:
            - < 50ms response time (returns cached data)
        """
        if location not in BENGALURU_LOCATIONS:
            raise ValueError(
                f"Invalid location: {location}. "
                f"Must be one of {len(BENGALURU_LOCATIONS)} predefined Bengaluru locations"
            )
        
        with self._cache_lock:
            traffic_data = self._traffic_cache.get(location)
            
            if not traffic_data:
                # Should not happen after initialization, but handle gracefully
                logger.warning(f"No traffic data found for {location}, generating new data")
                congestion_level = self._generate_congestion_level()
                congestion_score = self.CONGESTION_SCORES[congestion_level]
                
                traffic_data = TrafficData(
                    location=location,
                    congestion_level=congestion_level,
                    congestion_score=congestion_score,
                    timestamp=datetime.now()
                )
                self._traffic_cache[location] = traffic_data
            
            # Return a copy to prevent external modification
            return TrafficData(
                location=traffic_data.location,
                congestion_level=traffic_data.congestion_level,
                congestion_score=traffic_data.congestion_score,
                timestamp=traffic_data.timestamp
            )
    
    def get_all_traffic_data(self) -> Dict[str, TrafficData]:
        """
        Retrieves traffic data for all locations.
        
        Returns:
            Dictionary mapping location names to TrafficData
            
        Performance:
            - < 50ms response time
        """
        with self._cache_lock:
            # Return copies to prevent external modification
            return {
                location: TrafficData(
                    location=data.location,
                    congestion_level=data.congestion_level,
                    congestion_score=data.congestion_score,
                    timestamp=data.timestamp
                )
                for location, data in self._traffic_cache.items()
            }
    
    def update_traffic_data(self) -> None:
        """
        Updates traffic data for all locations (simulated).
        
        Generates new congestion levels for all Bengaluru locations.
        In production, this would integrate with real traffic APIs.
        """
        logger.info("Updating traffic data for all locations")
        
        updated_count = 0
        
        with self._cache_lock:
            for location in BENGALURU_LOCATIONS.keys():
                # Generate new congestion level
                congestion_level = self._generate_congestion_level()
                congestion_score = self.CONGESTION_SCORES[congestion_level]
                
                self._traffic_cache[location] = TrafficData(
                    location=location,
                    congestion_level=congestion_level,
                    congestion_score=congestion_score,
                    timestamp=datetime.now()
                )
                updated_count += 1
        
        logger.info(f"Updated traffic data for {updated_count} locations")
    
    def _generate_congestion_level(self) -> CongestionLevel:
        """
        Generates a simulated congestion level.
        
        Uses weighted random selection to simulate realistic traffic patterns:
        - LOW: 40% probability
        - MEDIUM: 40% probability
        - HIGH: 20% probability
        
        Returns:
            Random CongestionLevel
        """
        # Weighted random selection for realistic distribution
        rand = random.random()
        
        if rand < 0.40:
            return CongestionLevel.LOW
        elif rand < 0.80:
            return CongestionLevel.MEDIUM
        else:
            return CongestionLevel.HIGH
    
    def start_scheduler(self) -> None:
        """
        Starts background scheduler to update traffic data every 10 minutes.
        """
        if self._scheduler_running:
            logger.warning("Scheduler already running")
            return
        
        self._scheduler_running = True
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info(
            f"Started traffic data scheduler (update interval: {self.UPDATE_INTERVAL}s)"
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
        
        logger.info("Stopped traffic data scheduler")
    
    def _scheduler_loop(self) -> None:
        """
        Background scheduler loop that updates traffic data periodically.
        """
        # Continue updating at intervals
        while self._scheduler_running:
            time.sleep(self.UPDATE_INTERVAL)
            
            if not self._scheduler_running:
                break
            
            try:
                self.update_traffic_data()
            except Exception as e:
                logger.error(f"Scheduled traffic update failed: {e}")


# Global traffic analyzer instance
_traffic_analyzer: Optional[TrafficAnalyzer] = None


def get_traffic_analyzer() -> TrafficAnalyzer:
    """
    Gets or creates the global TrafficAnalyzer instance.
    
    Returns:
        TrafficAnalyzer singleton instance
    """
    global _traffic_analyzer
    
    if _traffic_analyzer is None:
        _traffic_analyzer = TrafficAnalyzer()
    
    return _traffic_analyzer
