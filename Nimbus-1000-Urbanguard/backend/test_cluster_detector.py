"""
Unit tests for Cluster Detector component
Tests Haversine distance, clustering, density calculation, and time filtering
"""
import pytest
import math
from datetime import datetime, timedelta
from cluster_detector import ClusterDetector
from models import Complaint


class TestHaversineDistance:
    """Test Haversine distance calculation"""
    
    def test_same_location_zero_distance(self):
        """Distance between identical coordinates should be zero"""
        detector = ClusterDetector()
        coord = (12.9352, 77.6245)  # Koramangala
        distance = detector.haversine_distance(coord, coord)
        assert distance == 0.0
    
    def test_known_distance_koramangala_to_indiranagar(self):
        """Test known distance between Koramangala and Indiranagar"""
        detector = ClusterDetector()
        koramangala = (12.9352, 77.6245)
        indiranagar = (12.9716, 77.6412)
        
        distance = detector.haversine_distance(koramangala, indiranagar)
        
        # Expected distance is approximately 4.4 km
        assert 4300 < distance < 4600, f"Expected ~4400m, got {distance}m"
    
    def test_distance_symmetry(self):
        """Distance from A to B should equal distance from B to A"""
        detector = ClusterDetector()
        coord1 = (12.9352, 77.6245)
        coord2 = (12.9716, 77.6412)
        
        distance1 = detector.haversine_distance(coord1, coord2)
        distance2 = detector.haversine_distance(coord2, coord1)
        
        assert abs(distance1 - distance2) < 0.01
    
    def test_short_distance_accuracy(self):
        """Test accuracy for short distances (within 500m)"""
        detector = ClusterDetector()
        # Two points approximately 400m apart
        coord1 = (12.9352, 77.6245)
        coord2 = (12.9388, 77.6245)  # ~400m north
        
        distance = detector.haversine_distance(coord1, coord2)
        
        # Should be approximately 400 meters
        assert 350 < distance < 450, f"Expected ~400m, got {distance}m"


class TestTimeWindowFiltering:
    """Test time-based complaint filtering"""
    
    def test_filter_recent_complaints(self):
        """Should include complaints within 24-hour window"""
        detector = ClusterDetector(time_window_hours=24)
        now = datetime.now()
        
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test",
                timestamp=now - timedelta(hours=12),
                coordinates=(12.9352, 77.6245)
            ),
            Complaint(
                location="Indiranagar",
                category="flooding",
                description="Test",
                timestamp=now - timedelta(hours=6),
                coordinates=(12.9716, 77.6412)
            )
        ]
        
        filtered = detector.filter_by_time_window(complaints, now)
        
        assert len(filtered) == 2
    
    def test_filter_old_complaints(self):
        """Should exclude complaints outside 24-hour window"""
        detector = ClusterDetector(time_window_hours=24)
        now = datetime.now()
        
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test",
                timestamp=now - timedelta(hours=30),
                coordinates=(12.9352, 77.6245)
            ),
            Complaint(
                location="Indiranagar",
                category="flooding",
                description="Test",
                timestamp=now - timedelta(hours=48),
                coordinates=(12.9716, 77.6412)
            )
        ]
        
        filtered = detector.filter_by_time_window(complaints, now)
        
        assert len(filtered) == 0
    
    def test_filter_mixed_complaints(self):
        """Should filter mixed old and recent complaints"""
        detector = ClusterDetector(time_window_hours=24)
        now = datetime.now()
        
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Recent",
                timestamp=now - timedelta(hours=12),
                coordinates=(12.9352, 77.6245)
            ),
            Complaint(
                location="Indiranagar",
                category="flooding",
                description="Old",
                timestamp=now - timedelta(hours=30),
                coordinates=(12.9716, 77.6412)
            ),
            Complaint(
                location="Whitefield",
                category="traffic",
                description="Recent",
                timestamp=now - timedelta(hours=6),
                coordinates=(12.9698, 77.7499)
            )
        ]
        
        filtered = detector.filter_by_time_window(complaints, now)
        
        assert len(filtered) == 2
        assert all(c.description == "Recent" for c in filtered)


class TestClusterCenterCalculation:
    """Test cluster center coordinate calculation"""
    
    def test_single_complaint_center(self):
        """Center of single complaint should be its coordinates"""
        detector = ClusterDetector()
        coord = (12.9352, 77.6245)
        
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test",
                timestamp=datetime.now(),
                coordinates=coord
            )
        ]
        
        center = detector.calculate_cluster_center(complaints)
        
        assert center == coord
    
    def test_two_complaints_midpoint(self):
        """Center of two complaints should be midpoint"""
        detector = ClusterDetector()
        coord1 = (12.9352, 77.6245)
        coord2 = (12.9716, 77.6412)
        
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test",
                timestamp=datetime.now(),
                coordinates=coord1
            ),
            Complaint(
                location="Indiranagar",
                category="flooding",
                description="Test",
                timestamp=datetime.now(),
                coordinates=coord2
            )
        ]
        
        center = detector.calculate_cluster_center(complaints)
        
        expected_lat = (coord1[0] + coord2[0]) / 2
        expected_lon = (coord1[1] + coord2[1]) / 2
        
        assert abs(center[0] - expected_lat) < 0.0001
        assert abs(center[1] - expected_lon) < 0.0001
    
    def test_empty_complaints_list(self):
        """Empty list should return (0, 0)"""
        detector = ClusterDetector()
        center = detector.calculate_cluster_center([])
        assert center == (0.0, 0.0)


class TestDensityCalculation:
    """Test complaint density calculation"""
    
    def test_density_calculation_500m_radius(self):
        """Test density for 500m radius cluster"""
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        # Create 5 complaints for density calculation
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
        
        from models import Cluster
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        density = detector.calculate_density(cluster)
        
        # Area = π * (0.5 km)² = π * 0.25 ≈ 0.785 km²
        # Density = 5 / 0.785 ≈ 6.37 complaints/km²
        expected_density = 5 / (math.pi * 0.25)
        
        assert abs(density - expected_density) < 0.01
    
    def test_density_scales_with_complaint_count(self):
        """Density should scale linearly with complaint count"""
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        from models import Cluster
        
        # Cluster with 5 complaints
        cluster1 = Cluster(
            complaints=[
                Complaint(
                    location="Koramangala",
                    category="pothole",
                    description=f"Test {i}",
                    timestamp=now,
                    coordinates=(12.9352, 77.6245)
                )
                for i in range(5)
            ],
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        # Cluster with 10 complaints
        cluster2 = Cluster(
            complaints=[
                Complaint(
                    location="Koramangala",
                    category="pothole",
                    description=f"Test {i}",
                    timestamp=now,
                    coordinates=(12.9352, 77.6245)
                )
                for i in range(10)
            ],
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        density1 = detector.calculate_density(cluster1)
        density2 = detector.calculate_density(cluster2)
        
        # Density should double
        assert abs(density2 - 2 * density1) < 0.01


class TestClusterDetection:
    """Test complete clustering algorithm"""
    
    def test_single_complaint_single_cluster(self):
        """Single complaint should create one cluster"""
        detector = ClusterDetector()
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
        
        clusters = detector.detect_clusters(complaints)
        
        assert len(clusters) == 1
        assert len(clusters[0].complaints) == 1
        assert clusters[0].is_high_density is False
    
    def test_nearby_complaints_same_cluster(self):
        """Complaints within 500m should be in same cluster"""
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        # Two complaints ~400m apart
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
        
        clusters = detector.detect_clusters(complaints)
        
        assert len(clusters) == 1
        assert len(clusters[0].complaints) == 2
    
    def test_distant_complaints_separate_clusters(self):
        """Complaints beyond 500m should be in separate clusters"""
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        # Koramangala and Indiranagar are ~4.7km apart
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test 1",
                timestamp=now,
                coordinates=(12.9352, 77.6245)
            ),
            Complaint(
                location="Indiranagar",
                category="flooding",
                description="Test 2",
                timestamp=now,
                coordinates=(12.9716, 77.6412)
            )
        ]
        
        clusters = detector.detect_clusters(complaints)
        
        assert len(clusters) == 2
        assert all(len(c.complaints) == 1 for c in clusters)
    
    def test_high_density_cluster_flagging(self):
        """Cluster with 5+ complaints should be flagged as high-density"""
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        # Create 6 complaints at same location
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
        
        clusters = detector.detect_clusters(complaints)
        
        assert len(clusters) == 1
        assert clusters[0].is_high_density is True
        assert len(clusters[0].complaints) == 6
    
    def test_low_density_cluster_not_flagged(self):
        """Cluster with <5 complaints should not be flagged"""
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        # Create 4 complaints at same location
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now,
                coordinates=(12.9352, 77.6245)
            )
            for i in range(4)
        ]
        
        clusters = detector.detect_clusters(complaints)
        
        assert len(clusters) == 1
        assert clusters[0].is_high_density is False
    
    def test_time_window_filtering_in_clustering(self):
        """Clustering should only consider complaints within time window"""
        detector = ClusterDetector(radius_meters=500, time_window_hours=24)
        now = datetime.now()
        
        complaints = [
            # Recent complaint
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Recent",
                timestamp=now - timedelta(hours=12),
                coordinates=(12.9352, 77.6245)
            ),
            # Old complaint at same location
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Old",
                timestamp=now - timedelta(hours=30),
                coordinates=(12.9352, 77.6245)
            )
        ]
        
        clusters = detector.detect_clusters(complaints)
        
        # Should only cluster the recent complaint
        assert len(clusters) == 1
        assert len(clusters[0].complaints) == 1
        assert clusters[0].complaints[0].description == "Recent"
    
    def test_empty_complaints_list(self):
        """Empty complaints list should return empty clusters"""
        detector = ClusterDetector()
        clusters = detector.detect_clusters([])
        assert len(clusters) == 0
    
    def test_cluster_center_calculation(self):
        """Cluster center should be calculated correctly"""
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        coord1 = (12.9352, 77.6245)
        coord2 = (12.9388, 77.6245)
        
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test 1",
                timestamp=now,
                coordinates=coord1
            ),
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test 2",
                timestamp=now,
                coordinates=coord2
            )
        ]
        
        clusters = detector.detect_clusters(complaints)
        
        expected_lat = (coord1[0] + coord2[0]) / 2
        expected_lon = (coord1[1] + coord2[1]) / 2
        
        assert len(clusters) == 1
        assert abs(clusters[0].center_coordinates[0] - expected_lat) < 0.0001
        assert abs(clusters[0].center_coordinates[1] - expected_lon) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
