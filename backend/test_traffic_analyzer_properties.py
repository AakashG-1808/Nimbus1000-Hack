"""
Property-based tests for Traffic Analyzer
Tests universal properties using Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime

from traffic_analyzer import TrafficAnalyzer
from models import CongestionLevel
from constants import BENGALURU_LOCATIONS


# Strategy for valid Bengaluru locations
bengaluru_location_strategy = st.sampled_from(list(BENGALURU_LOCATIONS.keys()))


class TestTrafficAnalyzerProperties:
    """Property-based tests for TrafficAnalyzer"""
    
    @given(bengaluru_location_strategy)
    @settings(max_examples=100)
    def test_property_17_congestion_processing(self, location):
        """
        **Validates: Requirements 6.1**
        
        Property 17: Traffic Congestion Processing
        For any Bengaluru_Location, the Traffic_Analyzer should process 
        and provide traffic congestion level (low, medium, or high).
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Should successfully get traffic data for any valid location
        traffic = analyzer.get_traffic_data(location)
        
        # Should have a valid congestion level
        assert traffic.congestion_level in [
            CongestionLevel.LOW,
            CongestionLevel.MEDIUM,
            CongestionLevel.HIGH
        ]
        
        # Should match the requested location
        assert traffic.location == location
        
        # Should have a timestamp
        assert isinstance(traffic.timestamp, datetime)
    
    @given(bengaluru_location_strategy)
    @settings(max_examples=100)
    def test_property_18_congestion_score_mapping(self, location):
        """
        **Validates: Requirements 6.3**
        
        Property 18: Congestion Score Mapping
        For any traffic data, the Traffic_Analyzer should assign congestion 
        scores according to the mapping: low=1, medium=5, high=10.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        traffic = analyzer.get_traffic_data(location)
        
        # Verify score matches level
        if traffic.congestion_level == CongestionLevel.LOW:
            assert traffic.congestion_score == 1
        elif traffic.congestion_level == CongestionLevel.MEDIUM:
            assert traffic.congestion_score == 5
        elif traffic.congestion_level == CongestionLevel.HIGH:
            assert traffic.congestion_score == 10
        else:
            pytest.fail(f"Unexpected congestion level: {traffic.congestion_level}")
    
    @given(st.text())
    @settings(max_examples=100)
    def test_invalid_location_rejection(self, location):
        """
        Property: Invalid locations should be rejected
        For any location not in BENGALURU_LOCATIONS, the Traffic_Analyzer 
        should raise ValueError.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Skip if location happens to be valid
        if location in BENGALURU_LOCATIONS:
            return
        
        # Should raise ValueError for invalid location
        with pytest.raises(ValueError) as exc_info:
            analyzer.get_traffic_data(location)
        
        assert "Invalid location" in str(exc_info.value)
    
    @given(bengaluru_location_strategy)
    @settings(max_examples=50)
    def test_traffic_data_consistency(self, location):
        """
        Property: Traffic data should be consistent across multiple calls
        For any location, calling get_traffic_data multiple times without 
        update should return the same data.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Get traffic data twice
        traffic1 = analyzer.get_traffic_data(location)
        traffic2 = analyzer.get_traffic_data(location)
        
        # Should return same values (before update)
        assert traffic1.location == traffic2.location
        assert traffic1.congestion_level == traffic2.congestion_level
        assert traffic1.congestion_score == traffic2.congestion_score
        assert traffic1.timestamp == traffic2.timestamp
    
    @given(bengaluru_location_strategy)
    @settings(max_examples=50)
    def test_traffic_data_update_changes_timestamp(self, location):
        """
        Property: Update should change timestamp
        For any location, after calling update_traffic_data, the timestamp 
        should be more recent.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Get initial traffic data
        traffic_before = analyzer.get_traffic_data(location)
        initial_timestamp = traffic_before.timestamp
        
        # Update traffic data
        analyzer.update_traffic_data()
        
        # Get updated traffic data
        traffic_after = analyzer.get_traffic_data(location)
        
        # Timestamp should be updated
        assert traffic_after.timestamp >= initial_timestamp
    
    def test_all_locations_have_traffic_data(self):
        """
        Property: All locations should have traffic data
        After initialization, every Bengaluru location should have 
        valid traffic data.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        all_traffic = analyzer.get_all_traffic_data()
        
        # Should have data for all locations
        assert len(all_traffic) == len(BENGALURU_LOCATIONS)
        
        # Every location should be present
        for location in BENGALURU_LOCATIONS.keys():
            assert location in all_traffic
            
            traffic = all_traffic[location]
            assert traffic.location == location
            assert traffic.congestion_level in [
                CongestionLevel.LOW,
                CongestionLevel.MEDIUM,
                CongestionLevel.HIGH
            ]
            assert traffic.congestion_score in [1, 5, 10]
    
    @given(bengaluru_location_strategy)
    @settings(max_examples=100)
    def test_congestion_score_in_valid_range(self, location):
        """
        Property: Congestion score should always be 1, 5, or 10
        For any location, the congestion score should be one of the 
        three valid values.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        traffic = analyzer.get_traffic_data(location)
        
        # Score must be one of the three valid values
        assert traffic.congestion_score in [1, 5, 10]
    
    @given(bengaluru_location_strategy)
    @settings(max_examples=100)
    def test_traffic_data_has_required_fields(self, location):
        """
        Property: Traffic data should have all required fields
        For any location, the returned TrafficData should have location, 
        congestion_level, congestion_score, and timestamp.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        traffic = analyzer.get_traffic_data(location)
        
        # All required fields should be present and valid
        assert traffic.location is not None
        assert isinstance(traffic.location, str)
        
        assert traffic.congestion_level is not None
        assert isinstance(traffic.congestion_level, CongestionLevel)
        
        assert traffic.congestion_score is not None
        assert isinstance(traffic.congestion_score, int)
        
        assert traffic.timestamp is not None
        assert isinstance(traffic.timestamp, datetime)
    
    def test_update_affects_all_locations(self):
        """
        Property: Update should affect all locations
        After calling update_traffic_data, all locations should have 
        updated timestamps.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Get initial timestamps
        initial_traffic = analyzer.get_all_traffic_data()
        initial_timestamps = {
            loc: data.timestamp for loc, data in initial_traffic.items()
        }
        
        # Update traffic data
        analyzer.update_traffic_data()
        
        # Get updated traffic
        updated_traffic = analyzer.get_all_traffic_data()
        
        # All locations should have updated timestamps
        for location in BENGALURU_LOCATIONS.keys():
            assert updated_traffic[location].timestamp >= initial_timestamps[location]
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=50)
    def test_multiple_updates_maintain_validity(self, num_updates):
        """
        Property: Multiple updates should maintain data validity
        After any number of updates, traffic data should remain valid.
        """
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Perform multiple updates
        for _ in range(num_updates):
            analyzer.update_traffic_data()
        
        # Check that all data is still valid
        all_traffic = analyzer.get_all_traffic_data()
        
        for location, traffic in all_traffic.items():
            assert traffic.location == location
            assert traffic.congestion_level in [
                CongestionLevel.LOW,
                CongestionLevel.MEDIUM,
                CongestionLevel.HIGH
            ]
            assert traffic.congestion_score in [1, 5, 10]
            assert isinstance(traffic.timestamp, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
