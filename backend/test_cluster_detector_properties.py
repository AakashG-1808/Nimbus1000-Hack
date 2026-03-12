"""
UrbanGuard AI System - Cluster Detector Property-Based Tests
Property-based tests using Hypothesis to validate cluster detection logic.

These tests run with minimum 100 iterations to ensure correctness across a wide range of inputs.
"""
import pytest
import math
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st, assume
from cluster_detector import ClusterDetector
from models import Complaint, Cluster
from constants import BENGALURU_LOCATIONS


# Custom strategies for generating test data
def valid_locations():
    """Strategy for generating valid Bengaluru locations."""
    return st.sampled_from(list(BENGALURU_LOCATIONS.keys()))


def valid_coordinates():
    """Strategy for generating valid coordinates within Bengaluru bounds."""
    # Bengaluru bounds: 12.8-13.2°N, 77.4-77.8°E
    return st.tuples(
        st.floats(min_value=12.8, max_value=13.2),  # latitude
        st.floats(min_value=77.4, max_value=77.8)   # longitude
    )


def valid_categories():
    """Strategy for generating valid complaint categories."""
    return st.sampled_from([
        "pothole", "flooding", "traffic", "garbage",
        "streetlight", "water_supply", "noise", "construction"
    ])


def valid_descriptions():
    """Strategy for generating valid descriptions."""
    return st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != "")


def recent_timestamps(hours_back=24):
    """Strategy for generating recent timestamps within specified hours."""
    now = datetime.now()
    return st.datetimes(
        min_value=now - timedelta(hours=hours_back),
        max_value=now
    )


def complaint_strategy(coord_strategy=None, timestamp_strategy=None):
    """Strategy for generating valid Complaint objects."""
    if coord_strategy is None:
        coord_strategy = valid_coordinates()
    if timestamp_strategy is None:
        timestamp_strategy = recent_timestamps()
    
    return st.builds(
        Complaint,
        location=valid_locations(),
        category=valid_categories(),
        description=valid_descriptions(),
        timestamp=timestamp_strategy,
        coordinates=coord_strategy
    )


# Property 11: Geographic Clustering - Complaints within 500m grouped together
# **Validates: Requirements 4.1**
class TestGeographicClusteringProperty:
    """Property-based tests for geographic clustering."""
    
    @settings(max_examples=100)
    @given(
        base_coord=valid_coordinates(),
        num_complaints=st.integers(min_value=2, max_value=10)
    )
    def test_nearby_complaints_grouped_together(self, base_coord, num_complaints):
        """
        Property 11: Geographic Clustering
        
        For any set of complaints, those within 500 meters of each other should 
        be grouped into the same cluster by the Cluster_Detector.
        
        **Validates: Requirements 4.1**
        """
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        # Generate complaints within 400m of base coordinate (well within 500m radius)
        # Using small offsets: ~0.004 degrees ≈ 400m
        complaints = []
        for i in range(num_complaints):
            # Small random offset within ~400m
            lat_offset = (i * 0.001) % 0.004  # Keep within 400m
            lon_offset = (i * 0.001) % 0.004
            coord = (base_coord[0] + lat_offset, base_coord[1] + lon_offset)
            
            complaint = Complaint(
                location=list(BENGALURU_LOCATIONS.keys())[0],
                category="pothole",
                description=f"Test complaint {i}",
                timestamp=now,
                coordinates=coord
            )
            complaints.append(complaint)
        
        # Verify all complaints are within 500m of base
        for complaint in complaints:
            distance = detector.haversine_distance(base_coord, complaint.coordinates)
            assume(distance <= 500)  # Ensure test precondition
        
        # Detect clusters
        clusters = detector.detect_clusters(complaints)
        
        # All nearby complaints should be in the same cluster
        assert len(clusters) == 1, f"Expected 1 cluster, got {len(clusters)}"
        assert len(clusters[0].complaints) == num_complaints, \
            f"Expected {num_complaints} complaints in cluster, got {len(clusters[0].complaints)}"
    
    @settings(max_examples=100)
    @given(
        coord1=valid_coordinates(),
        coord2=valid_coordinates()
    )
    def test_distant_complaints_separate_clusters(self, coord1, coord2):
        """
        Property 11 (inverse): Complaints beyond 500m should be in separate clusters.
        
        For any two complaints more than 500 meters apart, they should be in 
        different clusters.
        """
        detector = ClusterDetector(radius_meters=500)
        now = datetime.now()
        
        # Calculate distance between coordinates
        distance = detector.haversine_distance(coord1, coord2)
        
        # Only test when coordinates are sufficiently far apart
        assume(distance > 500)
        
        complaints = [
            Complaint(
                location=list(BENGALURU_LOCATIONS.keys())[0],
                category="pothole",
                description="Test 1",
                timestamp=now,
                coordinates=coord1
            ),
            Complaint(
                location=list(BENGALURU_LOCATIONS.keys())[1],
                category="flooding",
                description="Test 2",
                timestamp=now,
                coordinates=coord2
            )
        ]
        
        clusters = detector.detect_clusters(complaints)
        
        # Should have 2 separate clusters
        assert len(clusters) == 2, \
            f"Expected 2 clusters for complaints {distance:.0f}m apart, got {len(clusters)}"
        assert all(len(c.complaints) == 1 for c in clusters), \
            "Each cluster should have exactly 1 complaint"
    
    @settings(max_examples=100)
    @given(
        complaints=st.lists(
            complaint_strategy(),
            min_size=1,
            max_size=20
        )
    )
    def test_all_complaints_assigned_to_clusters(self, complaints):
        """
        Property 11 (completeness): All complaints should be assigned to exactly one cluster.
        
        For any set of complaints, every complaint should appear in exactly one cluster.
        """
        detector = ClusterDetector(radius_meters=500)
        
        clusters = detector.detect_clusters(complaints)
        
        # Count total complaints in all clusters
        total_in_clusters = sum(len(c.complaints) for c in clusters)
        
        # Filter complaints by time window (same as detector does)
        recent_complaints = detector.filter_by_time_window(complaints)
        
        # All recent complaints should be in clusters
        assert total_in_clusters == len(recent_complaints), \
            f"Expected {len(recent_complaints)} complaints in clusters, got {total_in_clusters}"
        
        # Check no complaint appears in multiple clusters
        seen_ids = set()
        for cluster in clusters:
            for complaint in cluster.complaints:
                assert complaint.complaint_id not in seen_ids, \
                    f"Complaint {complaint.complaint_id} appears in multiple clusters"
                seen_ids.add(complaint.complaint_id)


# Property 12: Density Calculation Correctness - Density accurately calculated
# **Validates: Requirements 4.2**
class TestDensityCalculationProperty:
    """Property-based tests for density calculation."""
    
    @settings(max_examples=100)
    @given(
        num_complaints=st.integers(min_value=1, max_value=50),
        radius_meters=st.floats(min_value=100, max_value=2000)
    )
    def test_density_calculation_accuracy(self, num_complaints, radius_meters):
        """
        Property 12: Density Calculation Correctness
        
        For any cluster, the calculated density (complaints per square kilometer) 
        should accurately reflect the number of complaints divided by the cluster area.
        
        **Validates: Requirements 4.2**
        """
        detector = ClusterDetector(radius_meters=radius_meters)
        now = datetime.now()
        
        # Create complaints at same location
        base_coord = (12.9352, 77.6245)
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now,
                coordinates=base_coord
            )
            for i in range(num_complaints)
        ]
        
        # Create cluster
        cluster = Cluster(
            complaints=complaints,
            center_coordinates=base_coord,
            radius_meters=radius_meters,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        # Calculate density
        density = detector.calculate_density(cluster)
        
        # Calculate expected density
        radius_km = radius_meters / 1000.0
        area_km2 = math.pi * (radius_km ** 2)
        expected_density = num_complaints / area_km2
        
        # Verify density is accurate
        assert abs(density - expected_density) < 0.01, \
            f"Expected density {expected_density:.2f}, got {density:.2f}"
    
    @settings(max_examples=100)
    @given(
        num_complaints=st.integers(min_value=1, max_value=20),
        radius_meters=st.floats(min_value=100, max_value=1000)
    )
    def test_density_scales_linearly_with_complaints(self, num_complaints, radius_meters):
        """
        Property 12 (linearity): Density should scale linearly with complaint count.
        
        For any cluster, doubling the number of complaints should double the density.
        """
        detector = ClusterDetector(radius_meters=radius_meters)
        now = datetime.now()
        base_coord = (12.9352, 77.6245)
        
        # Create cluster with N complaints
        complaints1 = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now,
                coordinates=base_coord
            )
            for i in range(num_complaints)
        ]
        
        cluster1 = Cluster(
            complaints=complaints1,
            center_coordinates=base_coord,
            radius_meters=radius_meters,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        # Create cluster with 2N complaints
        complaints2 = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now,
                coordinates=base_coord
            )
            for i in range(num_complaints * 2)
        ]
        
        cluster2 = Cluster(
            complaints=complaints2,
            center_coordinates=base_coord,
            radius_meters=radius_meters,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        density1 = detector.calculate_density(cluster1)
        density2 = detector.calculate_density(cluster2)
        
        # Density should double
        assert abs(density2 - 2 * density1) < 0.01, \
            f"Expected density to double: {density1:.2f} -> {density2:.2f}"
    
    @settings(max_examples=100)
    @given(
        num_complaints=st.integers(min_value=1, max_value=20)
    )
    def test_density_inversely_proportional_to_area(self, num_complaints):
        """
        Property 12 (inverse proportionality): Density should be inversely proportional to area.
        
        For the same number of complaints, doubling the radius should reduce density by ~4x.
        """
        now = datetime.now()
        base_coord = (12.9352, 77.6245)
        
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now,
                coordinates=base_coord
            )
            for i in range(num_complaints)
        ]
        
        # Cluster with radius R
        detector1 = ClusterDetector(radius_meters=500)
        cluster1 = Cluster(
            complaints=complaints,
            center_coordinates=base_coord,
            radius_meters=500,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        # Cluster with radius 2R
        detector2 = ClusterDetector(radius_meters=1000)
        cluster2 = Cluster(
            complaints=complaints,
            center_coordinates=base_coord,
            radius_meters=1000,
            density_per_km2=0.0,
            is_high_density=False,
            time_window_hours=24
        )
        
        density1 = detector1.calculate_density(cluster1)
        density2 = detector2.calculate_density(cluster2)
        
        # Density should be ~4x smaller (area increases by 4x when radius doubles)
        ratio = density1 / density2 if density2 > 0 else 0
        assert abs(ratio - 4.0) < 0.1, \
            f"Expected density ratio ~4.0, got {ratio:.2f}"


# Property 13: High-Density Cluster Flagging - 5+ complaints flagged as high-density
# **Validates: Requirements 4.3**
class TestHighDensityClusterFlaggingProperty:
    """Property-based tests for high-density cluster flagging."""
    
    @settings(max_examples=100)
    @given(
        num_complaints=st.integers(min_value=5, max_value=50),
        base_coord=valid_coordinates()
    )
    def test_five_or_more_complaints_flagged_high_density(self, num_complaints, base_coord):
        """
        Property 13: High-Density Cluster Flagging
        
        For any zone, if it contains 5 or more complaints within a 24-hour time window, 
        the Cluster_Detector should flag it as a high-density cluster.
        
        **Validates: Requirements 4.3**
        """
        detector = ClusterDetector(radius_meters=500, time_window_hours=24)
        now = datetime.now()
        
        # Create N complaints at same location (N >= 5)
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now - timedelta(hours=i % 12),  # Within 24h window
                coordinates=base_coord
            )
            for i in range(num_complaints)
        ]
        
        clusters = detector.detect_clusters(complaints)
        
        # Should have exactly one cluster
        assert len(clusters) == 1, f"Expected 1 cluster, got {len(clusters)}"
        
        # Cluster should be flagged as high-density
        assert clusters[0].is_high_density is True, \
            f"Cluster with {num_complaints} complaints should be flagged as high-density"
        assert len(clusters[0].complaints) >= 5, \
            f"High-density cluster should have >= 5 complaints"
    
    @settings(max_examples=100)
    @given(
        num_complaints=st.integers(min_value=1, max_value=4),
        base_coord=valid_coordinates()
    )
    def test_fewer_than_five_complaints_not_flagged(self, num_complaints, base_coord):
        """
        Property 13 (inverse): Clusters with fewer than 5 complaints should not be flagged.
        
        For any zone with fewer than 5 complaints, it should not be flagged as 
        high-density.
        """
        detector = ClusterDetector(radius_meters=500, time_window_hours=24)
        now = datetime.now()
        
        # Create N complaints at same location (N < 5)
        complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Test {i}",
                timestamp=now - timedelta(hours=i),
                coordinates=base_coord
            )
            for i in range(num_complaints)
        ]
        
        clusters = detector.detect_clusters(complaints)
        
        # Should have exactly one cluster
        assert len(clusters) == 1, f"Expected 1 cluster, got {len(clusters)}"
        
        # Cluster should NOT be flagged as high-density
        assert clusters[0].is_high_density is False, \
            f"Cluster with {num_complaints} complaints should NOT be flagged as high-density"
        assert len(clusters[0].complaints) < 5, \
            f"Low-density cluster should have < 5 complaints"
    
    @settings(max_examples=100)
    @given(
        num_recent=st.integers(min_value=5, max_value=10),
        num_old=st.integers(min_value=1, max_value=10),
        base_coord=valid_coordinates()
    )
    def test_high_density_only_counts_recent_complaints(self, num_recent, num_old, base_coord):
        """
        Property 13 (time window): High-density flagging should only count complaints 
        within the 24-hour time window.
        
        For any zone, only complaints within the time window should count toward 
        the 5+ threshold.
        """
        detector = ClusterDetector(radius_meters=500, time_window_hours=24)
        now = datetime.now()
        
        # Create recent complaints (within 24h)
        recent_complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Recent {i}",
                timestamp=now - timedelta(hours=i % 12),
                coordinates=base_coord
            )
            for i in range(num_recent)
        ]
        
        # Create old complaints (outside 24h window)
        old_complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description=f"Old {i}",
                timestamp=now - timedelta(hours=30 + i),
                coordinates=base_coord
            )
            for i in range(num_old)
        ]
        
        all_complaints = recent_complaints + old_complaints
        
        clusters = detector.detect_clusters(all_complaints)
        
        # Should have exactly one cluster (only recent complaints)
        assert len(clusters) == 1, f"Expected 1 cluster, got {len(clusters)}"
        
        # Cluster should only contain recent complaints
        assert len(clusters[0].complaints) == num_recent, \
            f"Expected {num_recent} recent complaints, got {len(clusters[0].complaints)}"
        
        # High-density flag should be based on recent complaints only
        expected_high_density = num_recent >= 5
        assert clusters[0].is_high_density == expected_high_density, \
            f"Expected is_high_density={expected_high_density} for {num_recent} recent complaints"
    
    @settings(max_examples=100)
    @given(
        complaints=st.lists(
            complaint_strategy(),
            min_size=1,
            max_size=30
        )
    )
    def test_high_density_flag_consistency(self, complaints):
        """
        Property 13 (consistency): High-density flag should be consistent with 
        complaint count.
        
        For any cluster, is_high_density should be True if and only if the cluster 
        has 5 or more complaints.
        """
        detector = ClusterDetector(radius_meters=500, time_window_hours=24)
        
        clusters = detector.detect_clusters(complaints)
        
        for cluster in clusters:
            complaint_count = len(cluster.complaints)
            
            if complaint_count >= 5:
                assert cluster.is_high_density is True, \
                    f"Cluster with {complaint_count} complaints should be high-density"
            else:
                assert cluster.is_high_density is False, \
                    f"Cluster with {complaint_count} complaints should NOT be high-density"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
