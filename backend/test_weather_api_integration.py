"""
Integration test for Weather API endpoint
Tests the /weather endpoint in the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime

from main import app
from models import WeatherData


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_weather_data():
    """Mock weather data for testing"""
    return WeatherData(
        temperature_celsius=28.5,
        humidity_percent=65.0,
        precipitation_mm_per_hour=3.2,
        wind_speed_kmh=15.5,
        high_rainfall_flag=False,
        timestamp=datetime.now(),
        source="openweathermap"
    )


class TestWeatherEndpoint:
    """Test /weather endpoint"""
    
    def test_weather_endpoint_exists(self, client):
        """Test /weather endpoint is accessible"""
        response = client.get("/weather")
        assert response.status_code == 200
    
    def test_weather_endpoint_returns_json(self, client):
        """Test /weather endpoint returns JSON"""
        response = client.get("/weather")
        assert response.headers["content-type"] == "application/json"
    
    def test_weather_endpoint_response_structure(self, client, mock_weather_data):
        """Test /weather endpoint returns all required fields"""
        with patch('main.get_weather_integrator') as mock_integrator:
            mock_instance = mock_integrator.return_value
            mock_instance.fetch_weather_data.return_value = mock_weather_data
            
            response = client.get("/weather")
            data = response.json()
            
            # Check all required fields are present
            assert "temperature_celsius" in data
            assert "humidity_percent" in data
            assert "precipitation_mm_per_hour" in data
            assert "wind_speed_kmh" in data
            assert "high_rainfall_flag" in data
            assert "timestamp" in data
            assert "source" in data
    
    def test_weather_endpoint_returns_correct_values(self, client, mock_weather_data):
        """Test /weather endpoint returns correct weather data"""
        with patch('main.get_weather_integrator') as mock_integrator:
            mock_instance = mock_integrator.return_value
            mock_instance.fetch_weather_data.return_value = mock_weather_data
            
            response = client.get("/weather")
            data = response.json()
            
            assert data["temperature_celsius"] == 28.5
            assert data["humidity_percent"] == 65.0
            assert data["precipitation_mm_per_hour"] == 3.2
            assert data["wind_speed_kmh"] == 15.5
            assert data["high_rainfall_flag"] is False
            assert data["source"] == "openweathermap"
    
    def test_weather_endpoint_high_rainfall(self, client):
        """Test /weather endpoint correctly reports high rainfall"""
        high_rain_data = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=85.0,
            precipitation_mm_per_hour=15.0,
            wind_speed_kmh=20.0,
            high_rainfall_flag=True,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        with patch('main.get_weather_integrator') as mock_integrator:
            mock_instance = mock_integrator.return_value
            mock_instance.fetch_weather_data.return_value = high_rain_data
            
            response = client.get("/weather")
            data = response.json()
            
            assert data["high_rainfall_flag"] is True
            assert data["precipitation_mm_per_hour"] == 15.0
    
    def test_weather_endpoint_performance(self, client, mock_weather_data):
        """Test /weather endpoint responds within 100ms"""
        import time
        
        with patch('main.get_weather_integrator') as mock_integrator:
            mock_instance = mock_integrator.return_value
            mock_instance.fetch_weather_data.return_value = mock_weather_data
            
            start = time.time()
            response = client.get("/weather")
            elapsed_ms = (time.time() - start) * 1000
            
            assert response.status_code == 200
            assert elapsed_ms < 100  # Should be < 100ms
    
    def test_weather_endpoint_handles_cache_source(self, client):
        """Test /weather endpoint correctly reports cache source"""
        cached_data = WeatherData(
            temperature_celsius=27.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=12.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="cache"
        )
        
        with patch('main.get_weather_integrator') as mock_integrator:
            mock_instance = mock_integrator.return_value
            mock_instance.fetch_weather_data.return_value = cached_data
            
            response = client.get("/weather")
            data = response.json()
            
            assert data["source"] == "cache"
    
    def test_weather_endpoint_handles_default_source(self, client):
        """Test /weather endpoint correctly reports default source"""
        default_data = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=10.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="default"
        )
        
        with patch('main.get_weather_integrator') as mock_integrator:
            mock_instance = mock_integrator.return_value
            mock_instance.fetch_weather_data.return_value = default_data
            
            response = client.get("/weather")
            data = response.json()
            
            assert data["source"] == "default"
            assert data["temperature_celsius"] == 25.0


class TestWeatherIntegratorLifecycle:
    """Test weather integrator lifecycle in FastAPI app"""
    
    def test_weather_integrator_starts_on_app_startup(self):
        """Test weather integrator is started when app starts"""
        # This is tested implicitly by the app starting successfully
        # The lifespan context manager should start the integrator
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_weather_endpoint_uses_singleton(self, client):
        """Test weather endpoint uses the global singleton integrator"""
        from weather_integrator import get_weather_integrator
        
        integrator1 = get_weather_integrator()
        
        # Make a request
        response = client.get("/weather")
        assert response.status_code == 200
        
        integrator2 = get_weather_integrator()
        
        # Should be the same instance
        assert integrator1 is integrator2
