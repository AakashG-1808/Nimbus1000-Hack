"""
Unit tests for Cluster Detector scheduler functionality
Tests 15-minute recalculation scheduler
"""
import pytest
import time
from datetime import datetime
from cluster_detector import ClusterDetector
from models import Complaint


class TestClusterScheduler:
    """Test cluster recalculation scheduler"""
    
    def test_scheduler_starts_and_stops(self):
        """Scheduler should start and stop cleanly"""
        complaints = []
        
        def get_complaints():
            return complaints
        
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=get_complaints
        )
        
        # Start scheduler
        detector.start_scheduler()
        assert detector._scheduler_running is True
        assert detector._scheduler_thread is not None
        
        # Stop scheduler
        detector.stop_scheduler()
        assert detector._scheduler_running is False
    
    def test_scheduler_auto_start(self):
        """Scheduler should auto-start when auto_start=True"""
        complaints = []
        
        def get_complaints():
            return complaints
        
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=True,
            get_complaints_callback=get_complaints
        )
        
        assert detector._scheduler_running is True
        
        # Cleanup
        detector.stop_scheduler()
    
    def test_scheduler_recalculates_on_start(self):
        """Scheduler should recalculate clusters immediately on start"""
        now = datetime.now()
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test",
                timestamp=now,
                coordinates=(12.9352, 77.6245)
            )
        ]
        
        def get_complaints():
            return complaints
        
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=get_complaints
        )
        
        # Start scheduler
        detector.start_scheduler()
        
        # Give it a moment to recalculate
        time.sleep(0.5)
        
        # Check cached clusters
        cached_clusters = detector.get_cached_clusters()
        assert len(cached_clusters) == 1
        assert len(cached_clusters[0].complaints) == 1
        
        # Cleanup
        detector.stop_scheduler()
    
    def test_recalculate_clusters_updates_cache(self):
        """recalculate_clusters should update the cache"""
        now = datetime.now()
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test 1",
                timestamp=now,
                coordinates=(12.9352, 77.6245)
            ),
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test 2",
                timestamp=now,
                coordinates=(12.9388, 77.6245)  # ~400m north
            )
        ]
        
        def get_complaints():
            return complaints
        
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=get_complaints
        )
        
        # Initially no cached clusters
        assert len(detector.get_cached_clusters()) == 0
        
        # Recalculate
        clusters = detector.recalculate_clusters()
        
        # Should have 1 cluster with 2 complaints
        assert len(clusters) == 1
        assert len(clusters[0].complaints) == 2
        
        # Cache should be updated
        cached_clusters = detector.get_cached_clusters()
        assert len(cached_clusters) == 1
        assert len(cached_clusters[0].complaints) == 2
    
    def test_high_density_flagging_in_recalculation(self):
        """Recalculation should correctly flag high-density clusters"""
        now = datetime.now()
        
        # Create 6 complaints at same location (high-density)
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now,
                coordinates=(12.9352, 77.6245)
            )
            for i in range(6)
        ]
        
        def get_complaints():
            return complaints
        
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=get_complaints
        )
        
        # Recalculate
        clusters = detector.recalculate_clusters()
        
        # Should have 1 high-density cluster
        assert len(clusters) == 1
        assert clusters[0].is_high_density is True
        assert len(clusters[0].complaints) == 6
    
    def test_density_calculation_in_recalculation(self):
        """Recalculation should calculate density correctly"""
        now = datetime.now()
        
        # Create 5 complaints at same location
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now,
                coordinates=(12.9352, 77.6245)
            )
            for i in range(5)
        ]
        
        def get_complaints():
            return complaints
        
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=get_complaints
        )
        
        # Recalculate
        clusters = detector.recalculate_clusters()
        
        # Check density calculation
        assert len(clusters) == 1
        
        # Area = π * (0.5 km)² = π * 0.25 ≈ 0.785 km²
        # Density = 5 / 0.785 ≈ 6.37 complaints/km²
        import math
        expected_density = 5 / (math.pi * 0.25)
        
        assert abs(clusters[0].density_per_km2 - expected_density) < 0.01
    
    def test_recalculate_without_callback_raises_error(self):
        """Recalculation without callback should raise RuntimeError"""
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=None
        )
        
        with pytest.raises(RuntimeError, match="no get_complaints_callback configured"):
            detector.recalculate_clusters()
    
    def test_start_scheduler_without_callback_logs_error(self):
        """Starting scheduler without callback should log error and not start"""
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=None
        )
        
        # Try to start scheduler
        detector.start_scheduler()
        
        # Should not be running
        assert detector._scheduler_running is False
    
    def test_get_cached_clusters_returns_copy(self):
        """get_cached_clusters should return a copy, not the original"""
        now = datetime.now()
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test",
                timestamp=now,
                coordinates=(12.9352, 77.6245)
            )
        ]
        
        def get_complaints():
            return complaints
        
        detector = ClusterDetector(
            radius_meters=500,
            time_window_hours=24,
            auto_start=False,
            get_complaints_callback=get_complaints
        )
        
        # Recalculate
        detector.recalculate_clusters()
        
        # Get cached clusters
        cached1 = detector.get_cached_clusters()
        cached2 = detector.get_cached_clusters()
        
        # Should be different list objects
        assert cached1 is not cached2
        
        # But should have same content
        assert len(cached1) == len(cached2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
