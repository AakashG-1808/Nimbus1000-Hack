"""
Integration test for Cluster Detector with Storage
Tests clustering with complaints from storage system
"""
import pytest
from datetime import datetime, timedelta
from cluster_detector import ClusterDetector
from storage import InMemoryStorage
from models import Complaint
from constants import BENGALURU_LOCATIONS


class TestClusterIntegration:
    """Test cluster detector integration with storage"""
    
    def setup_method(self):
        """Setup fresh storage for each test"""
        self.storage = InMemoryStorage()
        self.detector = ClusterDetector(radius_meters=500, time_window_hours=24)
    
    def test_clustering_with_storage_complaints(self):
        """Test clustering complaints retrieved from storage"""
        now = datetime.now()
        
        # Add complaints to storage
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test 1",
                timestamp=now - timedelta(hours=2),
                coordinates=BENGALURU_LOCATIONS["Koramangala"]
            ),
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Test 2",
                timestamp=now - timedelta(hours=4),
                coordinates=(12.9360, 77.6250)
            ),
            Complaint(
                location="Indiranagar",
                category="flooding",
                description="Test 3",
                timestamp=now - timedelta(hours=3),
                coordinates=BENGALURU_LOCATIONS["Indiranagar"]
            )
        ]
        
        for complaint in complaints:
            self.storage.add_complaint(complaint)
        
        # Retrieve complaints from storage
        stored_complaints = self.storage.get_all_complaints()
        
        # Detect clusters
        clusters = self.detector.detect_clusters(stored_complaints)
        
        # Should have 2 clusters (Koramangala and Indiranagar)
        assert len(clusters) == 2
        
        # Find Koramangala cluster
        koramangala_cluster = next(
            (c for c in clusters if len(c.complaints) == 2),
            None
        )
        assert koramangala_cluster is not None
        assert koramangala_cluster.is_high_density is False
    
    def test_high_density_detection_with_storage(self):
        """Test high-density cluster detection with storage"""
        now = datetime.now()
        
        # Add 6 complaints to same location
        for i in range(6):
            complaint = Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now - timedelta(hours=i),
                coordinates=BENGALURU_LOCATIONS["Koramangala"]
            )
            self.storage.add_complaint(complaint)
        
        # Retrieve and cluster
        stored_complaints = self.storage.get_all_complaints()
        clusters = self.detector.detect_clusters(stored_complaints)
        
        # Should have 1 high-density cluster
        assert len(clusters) == 1
        assert clusters[0].is_high_density is True
        assert len(clusters[0].complaints) == 6
    
    def test_location_based_clustering(self):
        """Test clustering complaints from specific location"""
        now = datetime.now()
        
        # Add complaints to multiple locations
        locations = ["Koramangala", "Indiranagar", "Whitefield"]
        for location in locations:
            for i in range(3):
                complaint = Complaint(
                    location=location,
                    category="pothole",
                    description=f"Test {i}",
                    timestamp=now - timedelta(hours=i),
                    coordinates=BENGALURU_LOCATIONS[location]
                )
                self.storage.add_complaint(complaint)
        
        # Get complaints for specific location
        koramangala_complaints = self.storage.get_complaints_by_location("Koramangala")
        
        # Cluster only Koramangala complaints
        clusters = self.detector.detect_clusters(koramangala_complaints)
        
        # Should have 1 cluster with 3 complaints
        assert len(clusters) == 1
        assert len(clusters[0].complaints) == 3
        assert all(c.location == "Koramangala" for c in clusters[0].complaints)
    
    def test_category_based_clustering(self):
        """Test clustering complaints of specific category"""
        now = datetime.now()
        
        # Add mixed category complaints to same location
        categories = ["pothole", "flooding", "traffic"]
        for i, category in enumerate(categories):
            for j in range(2):
                complaint = Complaint(
                    location="Koramangala",
                    category=category,
                    description=f"Test {i}-{j}",
                    timestamp=now - timedelta(hours=i+j),
                    coordinates=BENGALURU_LOCATIONS["Koramangala"]
                )
                self.storage.add_complaint(complaint)
        
        # Get complaints of specific category
        pothole_complaints = self.storage.get_complaints_by_category("pothole")
        
        # Cluster only pothole complaints
        clusters = self.detector.detect_clusters(pothole_complaints)
        
        # Should have 1 cluster with 2 pothole complaints
        assert len(clusters) == 1
        assert len(clusters[0].complaints) == 2
        assert all(c.category == "pothole" for c in clusters[0].complaints)
    
    def test_empty_storage_clustering(self):
        """Test clustering with empty storage"""
        stored_complaints = self.storage.get_all_complaints()
        clusters = self.detector.detect_clusters(stored_complaints)
        
        assert len(clusters) == 0
    
    def test_time_filtered_clustering_with_storage(self):
        """Test that old complaints in storage are filtered out"""
        now = datetime.now()
        
        # Add recent and old complaints
        recent = Complaint(
            location="Koramangala",
            category="pothole",
            description="Recent",
            timestamp=now - timedelta(hours=12),
            coordinates=BENGALURU_LOCATIONS["Koramangala"]
        )
        old = Complaint(
            location="Koramangala",
            category="pothole",
            description="Old",
            timestamp=now - timedelta(hours=30),
            coordinates=BENGALURU_LOCATIONS["Koramangala"]
        )
        
        self.storage.add_complaint(recent)
        self.storage.add_complaint(old)
        
        # Retrieve and cluster
        stored_complaints = self.storage.get_all_complaints()
        clusters = self.detector.detect_clusters(stored_complaints)
        
        # Should only cluster the recent complaint
        assert len(clusters) == 1
        assert len(clusters[0].complaints) == 1
        assert clusters[0].complaints[0].description == "Recent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
