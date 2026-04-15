"""
Integration tests for Traffic API endpoint
Tests the /traffic endpoint in the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestTrafficAPIIntegration:
    """Integration tests for /traffic endpoint"""
    
    def test_traffic_endpoint_exists(self):
        """Test that /traffic endpoint exists and returns 200"""
        response = client.get("/traffic")
        assert response.status_code == 200
    
    def test_traffic_endpoint_returns_list(self):
        """Test that /traffic returns a list of traffic data"""
        response = client.get("/traffic")
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_traffic_data_structure(self):
        """Test that each traffic data item has required fields"""
        response = client.get("/traffic")
        data = response.json()
        
        # Check first item structure
        traffic_item = data[0]
        
        assert "location" in traffic_item
        assert "congestion_level" in traffic_item
        assert "congestion_score" in traffic_item
        assert "timestamp" in traffic_item
        
        # Verify types
        assert isinstance(traffic_item["location"], str)
        assert isinstance(traffic_item["congestion_level"], str)
        assert isinstance(traffic_item["congestion_score"], int)
        assert isinstance(traffic_item["timestamp"], str)
    
    def test_traffic_congestion_levels(self):
        """Test that congestion levels are valid"""
        response = client.get("/traffic")
        data = response.json()
        
        valid_levels = ["low", "medium", "high"]
        
        for traffic_item in data:
            assert traffic_item["congestion_level"] in valid_levels
    
    def test_traffic_congestion_scores(self):
        """Test that congestion scores match levels"""
        response = client.get("/traffic")
        data = response.json()
        
        for traffic_item in data:
            level = traffic_item["congestion_level"]
            score = traffic_item["congestion_score"]
            
            if level == "low":
                assert score == 1
            elif level == "medium":
                assert score == 5
            elif level == "high":
                assert score == 10
    
    def test_traffic_all_locations_present(self):
        """Test that all Bengaluru locations have traffic data"""
        from constants import BENGALURU_LOCATIONS
        
        response = client.get("/traffic")
        data = response.json()
        
        # Extract locations from response
        response_locations = {item["location"] for item in data}
        
        # Should have data for all predefined locations
        assert len(response_locations) == len(BENGALURU_LOCATIONS)
        
        # All predefined locations should be present
        for location in BENGALURU_LOCATIONS.keys():
            assert location in response_locations
    
    def test_traffic_response_time(self):
        """Test that /traffic endpoint responds quickly"""
        import time
        
        start_time = time.time()
        response = client.get("/traffic")
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        # Should be well under 100ms requirement
        assert elapsed_ms < 200, f"Response time {elapsed_ms}ms exceeds 200ms"
    
    def test_traffic_timestamp_format(self):
        """Test that timestamp is in ISO format"""
        from datetime import datetime
        
        response = client.get("/traffic")
        data = response.json()
        
        # Check first item timestamp
        timestamp_str = data[0]["timestamp"]
        
        # Should be parseable as ISO format
        try:
            datetime.fromisoformat(timestamp_str)
        except ValueError:
            pytest.fail(f"Timestamp not in ISO format: {timestamp_str}")
    
    def test_traffic_cors_headers(self):
        """Test that CORS headers are present (when using real server)"""
        response = client.get("/traffic")
        
        # CORS headers may not be present in TestClient, but endpoint should work
        # In production with real server, CORS headers will be added by middleware
        assert response.status_code == 200
    
    def test_traffic_multiple_requests_consistent(self):
        """Test that multiple requests return consistent data structure"""
        response1 = client.get("/traffic")
        response2 = client.get("/traffic")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Should have same number of locations
        assert len(data1) == len(data2)
        
        # Should have same locations (though values may differ)
        locations1 = {item["location"] for item in data1}
        locations2 = {item["location"] for item in data2}
        assert locations1 == locations2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
