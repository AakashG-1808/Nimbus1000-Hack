"""
Property-based tests for Weather Integrator component
Tests universal properties that should hold for all inputs
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings
import requests

from weather_integrator import WeatherIntegrator
from models import WeatherData


# Custom strategies for weather data
@st.composite
def api_response_strategy(draw):
    """Generate valid OpenWeatherMap API responses"""
    return {
        "main": {
            "temp": draw(st.floats(min_value=-10, max_value=50)),
            "humidity": draw(st.integers(min_value=0, max_value=100))
        },
        "rain": {
            "1h": draw(st.floats(min_value=0, max_value=100))
        } if draw(st.booleans()) else {},
        "wind": {
            "speed": draw(st.floats(min_value=0, max_value=30))
        }
    }


@st.composite
def weather_data_strategy(draw):
    """Generate valid WeatherData instances"""
    precipitation = draw(st.floats(min_value=0, max_value=100))
    return WeatherData(
        temperature_celsius=draw(st.floats(min_value=-10, max_value=50)),
        humidity_percent=draw(st.floats(min_value=0, max_value=100)),
        precipitation_mm_per_hour=precipitation,
        wind_speed_kmh=draw(st.floats(min_value=0, max_value=100)),
        high_rainfall_flag=precipitation > 10.0,
        timestamp=datetime.now(),
        source=draw(st.sampled_from(["openweathermap", "cache", "default"]))
    )


class TestWeatherDataExtractionProperties:
    """Property-based tests for weather data extraction"""
    
    # Feature: urbanguard-ai-system, Property 14: Weather Data Extraction Completeness
    @given(api_response_strategy())
    @settings(max_examples=100)
    def test_extraction_completeness(self, api_response):
        """
        **Validates: Requirements 5.2**
        
        For any weather data retrieved from the OpenWeatherMap API,
        the Weather_Integrator should extract and provide temperature,
        humidity, precipitation, and wind speed.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        weather = integrator._parse_api_response(api_response)
        
        # All fields must be present
        assert hasattr(weather, 'temperature_celsius')
        assert hasattr(weather, 'humidity_percent')
        assert hasattr(weather, 'precipitation_mm_per_hour')
        assert hasattr(weather, 'wind_speed_kmh')
        
        # All fields must have valid values
        assert weather.temperature_celsius is not None
        assert weather.humidity_percent is not None
        assert weather.precipitation_mm_per_hour is not None
        assert weather.wind_speed_kmh is not None
        
        # Source should be set
        assert weather.source == "openweathermap"
    
    # Feature: urbanguard-ai-system, Property 16: High Rainfall Flagging
    @given(st.floats(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_high_rainfall_flagging(self, precipitation):
        """
        **Validates: Requirements 5.5**
        
        For any weather data, if precipitation exceeds 10mm per hour,
        the Weather_Integrator should set the high_rainfall_flag to true.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        api_response = {
            "main": {"temp": 25.0, "humidity": 70},
            "rain": {"1h": precipitation},
            "wind": {"speed": 5.0}
        }
        
        weather = integrator._parse_api_response(api_response)
        
        # High rainfall flag should match threshold
        if precipitation > 10.0:
            assert weather.high_rainfall_flag is True
        else:
            assert weather.high_rainfall_flag is False
    
    @given(st.floats(min_value=0, max_value=30))
    @settings(max_examples=100)
    def test_wind_speed_conversion(self, wind_speed_ms):
        """
        For any wind speed in m/s from API, it should be correctly
        converted to km/h (multiply by 3.6).
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        api_response = {
            "main": {"temp": 25.0, "humidity": 60},
            "wind": {"speed": wind_speed_ms}
        }
        
        weather = integrator._parse_api_response(api_response)
        
        expected_kmh = wind_speed_ms * 3.6
        assert weather.wind_speed_kmh == pytest.approx(expected_kmh, rel=0.01)


class TestCachingProperties:
    """Property-based tests for caching mechanism"""
    
    @given(weather_data_strategy())
    @settings(max_examples=100)
    def test_cache_stores_any_weather_data(self, weather_data):
        """
        For any valid WeatherData, the cache should be able to store
        and retrieve it correctly.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        with integrator._cache_lock:
            integrator._cache = weather_data
        
        with integrator._cache_lock:
            cached = integrator._cache
        
        assert cached == weather_data
        assert cached.temperature_celsius == weather_data.temperature_celsius
        assert cached.humidity_percent == weather_data.humidity_percent
        assert cached.precipitation_mm_per_hour == weather_data.precipitation_mm_per_hour
    
    @given(st.integers(min_value=0, max_value=7200))
    @settings(max_examples=100)
    def test_cache_validity_based_on_age(self, age_seconds):
        """
        For any cached weather data, it should be valid if age < 3600 seconds
        (1 hour) and invalid otherwise.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        weather_data = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=10.0,
            high_rainfall_flag=False,
            timestamp=datetime.now() - timedelta(seconds=age_seconds),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = weather_data
        
        is_valid = integrator._is_cache_valid()
        
        if age_seconds < 3600:
            assert is_valid is True
        else:
            assert is_valid is False


class TestErrorHandlingProperties:
    """Property-based tests for error handling"""
    
    # Feature: urbanguard-ai-system, Property 15: Weather Data Fallback on API Failure
    @given(weather_data_strategy())
    @settings(max_examples=100)
    def test_fallback_to_cache_on_api_failure(self, cached_weather):
        """
        **Validates: Requirements 5.3**
        
        For any request for weather data, if the OpenWeatherMap API is
        unavailable, the Weather_Integrator should return cached data
        and log a warning (rather than failing).
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        # Set up old cache (> 1 hour) to force API call attempt
        old_weather = WeatherData(
            temperature_celsius=cached_weather.temperature_celsius,
            humidity_percent=cached_weather.humidity_percent,
            precipitation_mm_per_hour=cached_weather.precipitation_mm_per_hour,
            wind_speed_kmh=cached_weather.wind_speed_kmh,
            high_rainfall_flag=cached_weather.high_rainfall_flag,
            timestamp=datetime.now() - timedelta(hours=2),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = old_weather
        
        # Mock API failure
        with patch.object(integrator, '_fetch_from_api', side_effect=Exception("API error")):
            result = integrator.fetch_weather_data()
        
        # Should return cached data (not crash)
        assert result is not None
        assert result.source == "cache"
        assert result.temperature_celsius == cached_weather.temperature_celsius
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=50)
    def test_retry_attempts_on_failure(self, num_failures):
        """
        For any number of API failures, the integrator should retry
        up to MAX_RETRIES times before giving up.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        call_count = 0
        
        def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < num_failures:
                raise requests.exceptions.RequestException("Error")
            # Success on the num_failures-th attempt
            mock_response = Mock()
            mock_response.json.return_value = {
                "main": {"temp": 25.0, "humidity": 60},
                "wind": {"speed": 5.0}
            }
            mock_response.raise_for_status = Mock()
            return mock_response
        
        with patch('requests.get', side_effect=mock_request):
            with patch('time.sleep'):  # Skip actual sleep
                if num_failures <= integrator.MAX_RETRIES:
                    # Should succeed on the num_failures-th attempt
                    result = integrator._fetch_from_api()
                    assert result is not None
                    assert call_count == num_failures
                else:
                    # Should fail after MAX_RETRIES attempts
                    with pytest.raises(Exception):
                        integrator._fetch_from_api()
                    assert call_count == integrator.MAX_RETRIES


class TestHighRainfallDetectionProperties:
    """Property-based tests for high rainfall detection"""
    
    @given(weather_data_strategy())
    @settings(max_examples=100)
    def test_is_high_rainfall_consistency(self, weather_data):
        """
        For any WeatherData, is_high_rainfall should return the same
        value as the high_rainfall_flag in the data.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        result = integrator.is_high_rainfall(weather_data)
        
        assert result == weather_data.high_rainfall_flag
    
    @given(st.floats(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_high_rainfall_threshold_consistency(self, precipitation):
        """
        For any precipitation value, high_rainfall_flag should be
        consistent with the threshold (> 10mm/hr).
        """
        weather_data = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=70.0,
            precipitation_mm_per_hour=precipitation,
            wind_speed_kmh=15.0,
            high_rainfall_flag=precipitation > 10.0,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        result = integrator.is_high_rainfall(weather_data)
        
        if precipitation > 10.0:
            assert result is True
        else:
            assert result is False


class TestCircuitBreakerProperties:
    """Property-based tests for circuit breaker pattern"""
    
    @given(st.integers(min_value=0, max_value=10))
    @settings(max_examples=50)
    def test_circuit_breaker_threshold(self, num_failures):
        """
        For any number of consecutive failures, the circuit breaker
        should open when failures reach the threshold (5).
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        for _ in range(num_failures):
            integrator._record_failure()
        
        if num_failures >= integrator._circuit_breaker_threshold:
            assert integrator._circuit_open is True
            assert integrator._is_circuit_open() is True
        else:
            assert integrator._circuit_open is False
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=50)
    def test_circuit_breaker_reset_on_success(self, num_failures):
        """
        For any number of failures, a successful API call should
        reset the circuit breaker.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        # Record failures
        for _ in range(num_failures):
            integrator._record_failure()
        
        # Reset on success
        integrator._reset_circuit_breaker()
        
        assert integrator._consecutive_failures == 0
        assert integrator._circuit_open is False


class TestPerformanceProperties:
    """Property-based tests for performance requirements"""
    
    @given(weather_data_strategy())
    @settings(max_examples=50)
    def test_cached_data_response_time(self, weather_data):
        """
        **Validates: Requirements 5.4**
        
        For any cached weather data, the Weather_Integrator should
        provide it within 100ms of request.
        """
        import time
        
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        with integrator._cache_lock:
            integrator._cache = weather_data
        
        start = time.time()
        result = integrator.fetch_weather_data()
        elapsed_ms = (time.time() - start) * 1000
        
        assert elapsed_ms < 100
        assert result is not None


class TestDefaultValuesProperties:
    """Property-based tests for default values"""
    
    @given(st.integers(min_value=0, max_value=5))
    @settings(max_examples=20)
    def test_default_values_on_total_failure(self, _):
        """
        For any scenario where API fails and no cache is available,
        the integrator should return default values (not crash).
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        # No cache
        with integrator._cache_lock:
            integrator._cache = None
        
        # Mock API failure
        with patch.object(integrator, '_fetch_from_api', side_effect=Exception("API error")):
            result = integrator.fetch_weather_data()
        
        # Should return default values
        assert result is not None
        assert result.source == "default"
        assert result.temperature_celsius == 25.0
        assert result.humidity_percent == 60.0
        assert result.precipitation_mm_per_hour == 0.0
        assert result.wind_speed_kmh == 10.0
        assert result.high_rainfall_flag is False


class TestDataIntegrityProperties:
    """Property-based tests for data integrity"""
    
    @given(api_response_strategy())
    @settings(max_examples=100)
    def test_timestamp_is_recent(self, api_response):
        """
        For any weather data parsed from API, the timestamp should
        be recent (within last minute).
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        before = datetime.now()
        weather = integrator._parse_api_response(api_response)
        after = datetime.now()
        
        assert before <= weather.timestamp <= after
    
    @given(api_response_strategy())
    @settings(max_examples=100)
    def test_humidity_bounds(self, api_response):
        """
        For any weather data, humidity should be within valid range (0-100%).
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        weather = integrator._parse_api_response(api_response)
        
        assert 0 <= weather.humidity_percent <= 100
    
    @given(api_response_strategy())
    @settings(max_examples=100)
    def test_precipitation_non_negative(self, api_response):
        """
        For any weather data, precipitation should be non-negative.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        weather = integrator._parse_api_response(api_response)
        
        assert weather.precipitation_mm_per_hour >= 0
    
    @given(api_response_strategy())
    @settings(max_examples=100)
    def test_wind_speed_non_negative(self, api_response):
        """
        For any weather data, wind speed should be non-negative.
        """
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        weather = integrator._parse_api_response(api_response)
        
        assert weather.wind_speed_kmh >= 0
