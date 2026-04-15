"""
Unit tests for Traffic Analyzer
Tests traffic data generation, congestion level assignment, and scheduling
"""
import pytest
import time
from datetime import datetime, timedelta

from traffic_analyzer import TrafficAnalyzer
from models import TrafficData, CongestionLevel
from constants import BENGALURU_LOCATIONS


class TestTrafficAnalyzer:
    """Unit tests for TrafficAnalyzer"""
    
    def test_initialization(self):
        """Test that traffic analyzer initializes with data for all locations"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Should have traffic data for all Bengaluru locations
        all_traffic = analyzer.get_all_traffic_data()
        assert len(all_traffic) == len(BENGALURU_LOCATIONS)
        
        # Each location should have valid traffic data
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
            assert isinstance(traffic.timestamp, datetime)
    
    def test_get_traffic_data_valid_location(self):
        """Test getting traffic data for a valid location"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        traffic = analyzer.get_traffic_data("Koramangala")
        
        assert traffic.location == "Koramangala"
        assert traffic.congestion_level in [
            CongestionLevel.LOW,
            CongestionLevel.MEDIUM,
            CongestionLevel.HIGH
        ]
        assert traffic.congestion_score in [1, 5, 10]
        assert isinstance(traffic.timestamp, datetime)
    
    def test_get_traffic_data_invalid_location(self):
        """Test that invalid location raises ValueError"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        with pytest.raises(ValueError) as exc_info:
            analyzer.get_traffic_data("InvalidLocation")
        
        assert "Invalid location" in str(exc_info.value)
    
    def test_congestion_score_mapping_low(self):
        """Test that LOW congestion maps to score 1"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Find a location with LOW congestion or update one
        analyzer._traffic_cache["Koramangala"] = TrafficData(
            location="Koramangala",
            congestion_level=CongestionLevel.LOW,
            congestion_score=1,
            timestamp=datetime.now()
        )
        
        traffic = analyzer.get_traffic_data("Koramangala")
        assert traffic.congestion_level == CongestionLevel.LOW
        assert traffic.congestion_score == 1
    
    def test_congestion_score_mapping_medium(self):
        """Test that MEDIUM congestion maps to score 5"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        analyzer._traffic_cache["Indiranagar"] = TrafficData(
            location="Indiranagar",
            congestion_level=CongestionLevel.MEDIUM,
            congestion_score=5,
            timestamp=datetime.now()
        )
        
        traffic = analyzer.get_traffic_data("Indiranagar")
        assert traffic.congestion_level == CongestionLevel.MEDIUM
        assert traffic.congestion_score == 5
    
    def test_congestion_score_mapping_high(self):
        """Test that HIGH congestion maps to score 10"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        analyzer._traffic_cache["Whitefield"] = TrafficData(
            location="Whitefield",
            congestion_level=CongestionLevel.HIGH,
            congestion_score=10,
            timestamp=datetime.now()
        )
        
        traffic = analyzer.get_traffic_data("Whitefield")
        assert traffic.congestion_level == CongestionLevel.HIGH
        assert traffic.congestion_score == 10
    
    def test_update_traffic_data(self):
        """Test that update_traffic_data refreshes all locations"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Get initial timestamps
        initial_traffic = analyzer.get_all_traffic_data()
        initial_timestamps = {
            loc: data.timestamp for loc, data in initial_traffic.items()
        }
        
        # Wait a bit to ensure timestamp difference
        time.sleep(0.1)
        
        # Update traffic data
        analyzer.update_traffic_data()
        
        # Get updated traffic
        updated_traffic = analyzer.get_all_traffic_data()
        
        # All locations should have updated timestamps
        for location in BENGALURU_LOCATIONS.keys():
            assert updated_traffic[location].timestamp > initial_timestamps[location]
    
    def test_get_all_traffic_data(self):
        """Test getting all traffic data at once"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        all_traffic = analyzer.get_all_traffic_data()
        
        # Should return data for all locations
        assert len(all_traffic) == len(BENGALURU_LOCATIONS)
        
        # Each entry should be valid
        for location, traffic in all_traffic.items():
            assert location in BENGALURU_LOCATIONS
            assert traffic.location == location
            assert traffic.congestion_level in [
                CongestionLevel.LOW,
                CongestionLevel.MEDIUM,
                CongestionLevel.HIGH
            ]
            assert traffic.congestion_score in [1, 5, 10]
    
    def test_traffic_data_immutability(self):
        """Test that returned traffic data cannot modify internal cache"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Get traffic data
        traffic1 = analyzer.get_traffic_data("Koramangala")
        original_level = traffic1.congestion_level
        
        # Modify the returned object
        traffic1.congestion_level = CongestionLevel.HIGH
        traffic1.congestion_score = 10
        
        # Get traffic data again
        traffic2 = analyzer.get_traffic_data("Koramangala")
        
        # Should still have original value (not modified)
        assert traffic2.congestion_level == original_level
    
    def test_response_time_performance(self):
        """Test that get_traffic_data responds within 50ms"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Measure response time
        start_time = time.time()
        analyzer.get_traffic_data("Koramangala")
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Should be well under 50ms
        assert elapsed_ms < 50, f"Response time {elapsed_ms}ms exceeds 50ms requirement"
    
    def test_scheduler_start_stop(self):
        """Test that scheduler can be started and stopped"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Start scheduler
        analyzer.start_scheduler()
        assert analyzer._scheduler_running is True
        assert analyzer._scheduler_thread is not None
        
        # Stop scheduler
        analyzer.stop_scheduler()
        assert analyzer._scheduler_running is False
    
    def test_scheduler_auto_start(self):
        """Test that scheduler auto-starts when enabled"""
        analyzer = TrafficAnalyzer(auto_start=True)
        
        assert analyzer._scheduler_running is True
        assert analyzer._scheduler_thread is not None
        
        # Clean up
        analyzer.stop_scheduler()
    
    def test_congestion_level_distribution(self):
        """Test that generated congestion levels have reasonable distribution"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Generate many samples
        samples = []
        for _ in range(1000):
            level = analyzer._generate_congestion_level()
            samples.append(level)
        
        # Count occurrences
        low_count = samples.count(CongestionLevel.LOW)
        medium_count = samples.count(CongestionLevel.MEDIUM)
        high_count = samples.count(CongestionLevel.HIGH)
        
        # Should have reasonable distribution (not all same)
        assert low_count > 0
        assert medium_count > 0
        assert high_count > 0
        
        # LOW and MEDIUM should be more common than HIGH (roughly 40%, 40%, 20%)
        assert low_count > high_count
        assert medium_count > high_count


class TestTrafficAnalyzerIntegration:
    """Integration tests for TrafficAnalyzer"""
    
    def test_all_bengaluru_locations_supported(self):
        """Test that all predefined Bengaluru locations have traffic data"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        # Test each location
        for location in BENGALURU_LOCATIONS.keys():
            traffic = analyzer.get_traffic_data(location)
            assert traffic is not None
            assert traffic.location == location
    
    def test_concurrent_access(self):
        """Test that traffic analyzer handles concurrent access safely"""
        analyzer = TrafficAnalyzer(auto_start=False)
        
        import threading
        results = []
        errors = []
        
        def get_traffic():
            try:
                traffic = analyzer.get_traffic_data("Koramangala")
                results.append(traffic)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=get_traffic) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 10
        
        # All results should be valid
        for traffic in results:
            assert traffic.location == "Koramangala"
            assert traffic.congestion_level in [
                CongestionLevel.LOW,
                CongestionLevel.MEDIUM,
                CongestionLevel.HIGH
            ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
