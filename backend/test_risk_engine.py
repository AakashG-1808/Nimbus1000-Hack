"""
Unit tests for Risk Engine - Base Risk Score Calculation
Tests for Task 7.1: Base score calculation, density threshold logic, and score bounds
"""
import pytest
from datetime import datetime
from risk_engine import RiskEngine
from models import Cluster, Complaint, RiskLevel


class TestBaseRiskScoreCalculation:
    """Tests for base risk score calculation from complaint density."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def test_zero_density_returns_zero_score(self):
        """Test that zero complaint density results in zero risk score."""
        score = self.engine.calculate_base_score(0.0)
        assert score == 0.0
    
    def test_low_density_scales_linearly(self):
        """Test that density below threshold scales linearly (density * 4)."""
        # 1 complaint per km² should give score of 4
        score = self.engine.calculate_base_score(1.0)
        assert score == 4.0
        
        # 2 complaints per km² should give score of 8
        score = self.engine.calculate_base_score(2.0)
        assert score == 8.0
        
        # 3 complaints per km² should give score of 12
        score = self.engine.calculate_base_score(3.0)
        assert score == 12.0
    
    def test_threshold_density_adds_bonus(self):
        """Test that density at threshold (5 per km²) adds 20 point bonus."""
        score = self.engine.calculate_base_score(5.0)
        # At threshold: should get 20 points
        assert score == 20.0
    
    def test_high_density_exceeds_threshold_bonus(self):
        """Test that density above threshold gets bonus plus additional points."""
        # 6 complaints per km²: 20 (bonus) + (6-5)*4 = 24
        score = self.engine.calculate_base_score(6.0)
        assert score == 24.0
        
        # 10 complaints per km²: 20 (bonus) + (10-5)*4 = 40
        score = self.engine.calculate_base_score(10.0)
        assert score == 40.0
    
    def test_very_high_density_capped_at_100(self):
        """Test that extremely high density is capped at 100."""
        # 50 complaints per km² would be 20 + (50-5)*4 = 200, but should cap at 100
        score = self.engine.calculate_base_score(50.0)
        assert score == 100.0
        
        # 100 complaints per km² should also cap at 100
        score = self.engine.calculate_base_score(100.0)
        assert score == 100.0
    
    def test_score_never_negative(self):
        """Test that score is never negative even with invalid input."""
        # Negative density should return 0 (bounded)
        score = self.engine.calculate_base_score(-5.0)
        assert score == 0.0
    
    def test_score_always_bounded_0_to_100(self):
        """Test that all scores are within valid range [0, 100]."""
        test_densities = [0, 0.5, 1, 2, 3, 4, 5, 6, 10, 20, 50, 100]
        
        for density in test_densities:
            score = self.engine.calculate_base_score(density)
            assert 0.0 <= score <= 100.0, f"Score {score} out of bounds for density {density}"


class TestRiskLevelClassification:
    """Tests for risk level classification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def test_low_risk_classification(self):
        """Test that scores 0-33 are classified as LOW risk."""
        assert self.engine.classify_risk_level(0) == RiskLevel.LOW
        assert self.engine.classify_risk_level(15) == RiskLevel.LOW
        assert self.engine.classify_risk_level(33) == RiskLevel.LOW
    
    def test_medium_risk_classification(self):
        """Test that scores 34-66 are classified as MEDIUM risk."""
        assert self.engine.classify_risk_level(34) == RiskLevel.MEDIUM
        assert self.engine.classify_risk_level(50) == RiskLevel.MEDIUM
        assert self.engine.classify_risk_level(66) == RiskLevel.MEDIUM
    
    def test_high_risk_classification(self):
        """Test that scores 67-100 are classified as HIGH risk."""
        assert self.engine.classify_risk_level(67) == RiskLevel.HIGH
        assert self.engine.classify_risk_level(85) == RiskLevel.HIGH
        assert self.engine.classify_risk_level(100) == RiskLevel.HIGH
    
    def test_boundary_values(self):
        """Test classification at exact boundary values."""
        # Boundary between LOW and MEDIUM
        assert self.engine.classify_risk_level(33) == RiskLevel.LOW
        assert self.engine.classify_risk_level(34) == RiskLevel.MEDIUM
        
        # Boundary between MEDIUM and HIGH
        assert self.engine.classify_risk_level(66) == RiskLevel.MEDIUM
        assert self.engine.classify_risk_level(67) == RiskLevel.HIGH


class TestRiskScoreWithClusters:
    """Tests for risk score calculation with actual cluster objects."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def create_cluster(self, complaint_count: int, density: float, category: str = "pothole") -> Cluster:
        """Helper to create a test cluster."""
        complaints = []
        for i in range(complaint_count):
            complaint = Complaint(
                location="Koramangala",
                category=category,
                description=f"Test complaint {i}",
                timestamp=datetime.now(),
                coordinates=(12.9352, 77.6245)
            )
            complaints.append(complaint)
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=density,
            is_high_density=density >= 5.0,
            time_window_hours=24
        )
        
        return cluster
    
    def test_cluster_with_low_density(self):
        """Test risk score for cluster with low complaint density."""
        cluster = self.create_cluster(complaint_count=2, density=2.5)
        
        # Without weather or traffic modifiers
        score = self.engine.calculate_risk_score(cluster)
        
        # Expected: 2.5 * 4 = 10
        assert score == 10.0
    
    def test_cluster_with_high_density(self):
        """Test risk score for cluster with high complaint density (>= 5 per km²)."""
        cluster = self.create_cluster(complaint_count=6, density=6.0)
        
        # Without weather or traffic modifiers
        score = self.engine.calculate_risk_score(cluster)
        
        # Expected: 20 + (6-5)*4 = 24
        assert score == 24.0
    
    def test_cluster_at_threshold(self):
        """Test risk score for cluster exactly at density threshold."""
        cluster = self.create_cluster(complaint_count=5, density=5.0)
        
        score = self.engine.calculate_risk_score(cluster)
        
        # Expected: exactly 20 points at threshold
        assert score == 20.0
    
    def test_create_risk_zone_from_cluster(self):
        """Test creating a RiskZone from a Cluster."""
        cluster = self.create_cluster(complaint_count=8, density=8.0)
        
        risk_zone = self.engine.create_risk_zone_from_cluster(cluster)
        
        # Verify RiskZone properties
        assert risk_zone.center_coordinates == cluster.center_coordinates
        assert risk_zone.radius_meters == cluster.radius_meters
        assert risk_zone.complaint_count == 8
        assert risk_zone.dominant_category == "pothole"
        
        # Verify risk score calculation
        # Expected: 20 + (8-5)*4 = 32
        assert risk_zone.risk_score == 32.0
        assert risk_zone.risk_level == RiskLevel.LOW  # 32 is in LOW range (0-33)
    
    def test_dominant_category_detection(self):
        """Test that dominant category is correctly identified."""
        # Create cluster with mixed categories
        complaints = [
            Complaint("Koramangala", "pothole", "Test 1", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "pothole", "Test 2", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "flooding", "Test 3", datetime.now(), (12.9352, 77.6245)),
            Complaint("Koramangala", "pothole", "Test 4", datetime.now(), (12.9352, 77.6245)),
        ]
        
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=(12.9352, 77.6245),
            radius_meters=500.0,
            density_per_km2=5.0,
            is_high_density=True,
            time_window_hours=24
        )
        
        risk_zone = self.engine.create_risk_zone_from_cluster(cluster)
        
        # Pothole is dominant (3 out of 4)
        assert risk_zone.dominant_category == "pothole"


class TestScoreBounds:
    """Tests to ensure risk scores are always bounded 0-100."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def test_minimum_bound(self):
        """Test that minimum score is 0."""
        score = self.engine.calculate_base_score(0.0)
        assert score >= 0.0
    
    def test_maximum_bound(self):
        """Test that maximum score is 100."""
        # Test with extremely high density
        score = self.engine.calculate_base_score(1000.0)
        assert score <= 100.0
    
    def test_all_scores_within_bounds(self):
        """Test that various density values produce bounded scores."""
        test_cases = [
            0.0, 0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 4.9,
            5.0, 5.1, 6.0, 10.0, 20.0, 50.0, 100.0, 1000.0
        ]
        
        for density in test_cases:
            score = self.engine.calculate_base_score(density)
            assert 0.0 <= score <= 100.0, \
                f"Score {score} out of bounds for density {density}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
