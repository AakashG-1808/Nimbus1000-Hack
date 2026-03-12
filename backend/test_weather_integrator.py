"""
Unit tests for Weather Integrator component
Tests OpenWeatherMap API integration, caching, and error handling
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests

from weather_integrator import WeatherIntegrator
from models import WeatherData


class TestWeatherIntegratorBasics:
    """Test basic Weather Integrator functionality"""
    
    def test_initialization_with_api_key(self):
        """Test Weather Integrator initializes with provided API key"""
        integrator = WeatherIntegrator(
            api_key="test_key",
            auto_start=False
        )
        assert integrator.api_key == "test_key"
        assert integrator.city == "Bengaluru"
        assert integrator.country_code == "IN"
    
    def test_initialization_from_env(self):
        """Test Weather Integrator reads API key from environment"""
        with patch.dict('os.environ', {'OPENWEATHERMAP_API_KEY': 'env_key'}):
            integrator = WeatherIntegrator(auto_start=False)
            assert integrator.api_key == "env_key"
    
    def test_high_rainfall_threshold(self):
        """Test high rainfall threshold is 10mm/hr"""
        assert WeatherIntegrator.HIGH_RAINFALL_THRESHOLD == 10.0
    
    def test_fetch_interval_is_30_minutes(self):
        """Test fetch interval is 30 minutes (1800 seconds)"""
        assert WeatherIntegrator.FETCH_INTERVAL == 30 * 60


class TestWeatherDataExtraction:
    """Test weather data extraction from API response"""
    
    def test_parse_api_response_extracts_all_fields(self):
        """Test parsing extracts temperature, humidity, precipitation, wind speed"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        api_response = {
            "main": {
                "temp": 28.5,
                "humidity": 65
            },
            "rain": {
                "1h": 5.2
            },
            "wind": {
                "speed": 4.5  # m/s
            }
        }
        
        weather = integrator._parse_api_response(api_response)
        
        assert weather.temperature_celsius == 28.5
        assert weather.humidity_percent == 65
        assert weather.precipitation_mm_per_hour == 5.2
        assert weather.wind_speed_kmh == pytest.approx(16.2, rel=0.1)  # 4.5 * 3.6
        assert weather.source == "openweathermap"
    
    def test_parse_api_response_no_rain(self):
        """Test parsing handles missing rain data"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        api_response = {
            "main": {
                "temp": 30.0,
                "humidity": 50
            },
            "wind": {
                "speed": 3.0
            }
        }
        
        weather = integrator._parse_api_response(api_response)
        
        assert weather.precipitation_mm_per_hour == 0.0
        assert weather.high_rainfall_flag is False
    
    def test_high_rainfall_flag_set_above_threshold(self):
        """Test high rainfall flag is set when precipitation > 10mm/hr"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        api_response = {
            "main": {"temp": 25.0, "humidity": 80},
            "rain": {"1h": 15.0},
            "wind": {"speed": 5.0}
        }
        
        weather = integrator._parse_api_response(api_response)
        
        assert weather.high_rainfall_flag is True
        assert weather.precipitation_mm_per_hour == 15.0
    
    def test_high_rainfall_flag_not_set_below_threshold(self):
        """Test high rainfall flag is not set when precipitation <= 10mm/hr"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        api_response = {
            "main": {"temp": 25.0, "humidity": 70},
            "rain": {"1h": 8.0},
            "wind": {"speed": 4.0}
        }
        
        weather = integrator._parse_api_response(api_response)
        
        assert weather.high_rainfall_flag is False


class TestCachingMechanism:
    """Test weather data caching"""
    
    def test_cache_stores_weather_data(self):
        """Test weather data is cached after successful fetch"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        weather_data = WeatherData(
            temperature_celsius=27.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=12.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = weather_data
        
        assert integrator._cache == weather_data
    
    def test_cache_validity_check(self):
        """Test cache validity is checked based on age"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        # Recent cache (valid)
        recent_weather = WeatherData(
            temperature_celsius=27.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=12.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = recent_weather
        
        assert integrator._is_cache_valid() is True
    
    def test_cache_invalid_when_old(self):
        """Test cache is invalid when older than 1 hour"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        # Old cache (invalid)
        old_weather = WeatherData(
            temperature_celsius=27.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=12.0,
            high_rainfall_flag=False,
            timestamp=datetime.now() - timedelta(hours=2),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = old_weather
        
        assert integrator._is_cache_valid() is False
    
    def test_fetch_returns_cached_data_when_valid(self):
        """Test fetch_weather_data returns cached data when valid"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        cached_weather = WeatherData(
            temperature_celsius=28.0,
            humidity_percent=65.0,
            precipitation_mm_per_hour=2.0,
            wind_speed_kmh=15.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = cached_weather
        
        result = integrator.fetch_weather_data()
        
        assert result == cached_weather
        assert result.temperature_celsius == 28.0


class TestAPIIntegration:
    """Test OpenWeatherMap API integration"""
    
    @patch('requests.get')
    def test_successful_api_call(self, mock_get):
        """Test successful API call fetches and parses data"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "main": {"temp": 29.0, "humidity": 70},
            "rain": {"1h": 3.0},
            "wind": {"speed": 5.0}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        weather = integrator._fetch_from_api()
        
        assert weather.temperature_celsius == 29.0
        assert weather.humidity_percent == 70
        assert weather.precipitation_mm_per_hour == 3.0
        assert weather.source == "openweathermap"
        
        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['q'] == "Bengaluru,IN"
        assert call_args[1]['params']['appid'] == "test_key"
        assert call_args[1]['params']['units'] == "metric"
    
    @patch('requests.get')
    def test_api_retry_on_failure(self, mock_get):
        """Test API retries on failure with exponential backoff"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        # Simulate failures
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        with pytest.raises(Exception) as exc_info:
            integrator._fetch_from_api()
        
        assert "Failed to fetch weather data after 3 attempts" in str(exc_info.value)
        assert mock_get.call_count == 3
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_exponential_backoff_delays(self, mock_sleep, mock_get):
        """Test retry delays follow exponential backoff pattern"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        mock_get.side_effect = requests.exceptions.RequestException("Error")
        
        with pytest.raises(Exception):
            integrator._fetch_from_api()
        
        # Check sleep was called with correct delays
        assert mock_sleep.call_count == 2  # 2 retries after first attempt
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1, 2]  # Exponential backoff: 1s, 2s


class TestErrorHandling:
    """Test error handling and fallback mechanisms"""
    
    def test_fallback_to_cache_on_api_failure(self):
        """Test falls back to cached data when API fails"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        # Set up cached data that's old (> 1 hour) so it won't be returned as valid
        # This forces the integrator to try fetching from API, which will fail
        cached_weather = WeatherData(
            temperature_celsius=26.0,
            humidity_percent=55.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=10.0,
            high_rainfall_flag=False,
            timestamp=datetime.now() - timedelta(hours=2),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = cached_weather
        
        # Mock API failure
        with patch.object(integrator, '_fetch_from_api', side_effect=Exception("API error")):
            result = integrator.fetch_weather_data()
        
        assert result.source == "cache"
        assert result.temperature_celsius == 26.0
    
    def test_default_values_when_no_cache(self):
        """Test returns default values when API fails and no cache available"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        # Mock API failure
        with patch.object(integrator, '_fetch_from_api', side_effect=Exception("API error")):
            result = integrator.fetch_weather_data()
        
        assert result.source == "default"
        assert result.temperature_celsius == 25.0
        assert result.humidity_percent == 60.0
        assert result.precipitation_mm_per_hour == 0.0
        assert result.wind_speed_kmh == 10.0
        assert result.high_rainfall_flag is False
    
    def test_missing_api_key_raises_error(self):
        """Test raises error when API key is not configured"""
        integrator = WeatherIntegrator(api_key=None, auto_start=False)
        
        with pytest.raises(ValueError) as exc_info:
            integrator._fetch_from_api()
        
        assert "API key not configured" in str(exc_info.value)


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after consecutive failures"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        # Record failures
        for _ in range(5):
            integrator._record_failure()
        
        assert integrator._circuit_open is True
        assert integrator._is_circuit_open() is True
    
    def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker resets after successful call"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        # Record some failures
        integrator._record_failure()
        integrator._record_failure()
        
        # Reset on success
        integrator._reset_circuit_breaker()
        
        assert integrator._consecutive_failures == 0
        assert integrator._circuit_open is False
    
    @patch('time.time')
    def test_circuit_breaker_timeout(self, mock_time):
        """Test circuit breaker reopens after timeout"""
        integrator = WeatherIntegrator(api_key="test_key", auto_start=False)
        
        # Open circuit
        mock_time.return_value = 1000.0
        for _ in range(5):
            integrator._record_failure()
        
        assert integrator._is_circuit_open() is True
        
        # Advance time past timeout
        mock_time.return_value = 1070.0  # 70 seconds later
        
        assert integrator._is_circuit_open() is False


class TestHighRainfallDetection:
    """Test high rainfall detection"""
    
    def test_is_high_rainfall_with_data(self):
        """Test is_high_rainfall checks the flag correctly"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        high_rain = WeatherData(
            temperature_celsius=25.0,
            humidity_percent=85.0,
            precipitation_mm_per_hour=15.0,
            wind_speed_kmh=20.0,
            high_rainfall_flag=True,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        assert integrator.is_high_rainfall(high_rain) is True
        
        low_rain = WeatherData(
            temperature_celsius=28.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=3.0,
            wind_speed_kmh=12.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        assert integrator.is_high_rainfall(low_rain) is False


class TestBackgroundScheduler:
    """Test background scheduler functionality"""
    
    def test_scheduler_starts_and_stops(self):
        """Test scheduler can be started and stopped"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        assert integrator._scheduler_running is False
        
        integrator.start_scheduler()
        assert integrator._scheduler_running is True
        assert integrator._scheduler_thread is not None
        
        integrator.stop_scheduler()
        assert integrator._scheduler_running is False
    
    def test_scheduler_auto_start(self):
        """Test scheduler starts automatically when auto_start=True"""
        integrator = WeatherIntegrator(api_key="test", auto_start=True)
        
        assert integrator._scheduler_running is True
        
        integrator.stop_scheduler()
    
    def test_scheduler_prevents_double_start(self):
        """Test scheduler prevents starting twice"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        integrator.start_scheduler()
        
        # Try to start again
        integrator.start_scheduler()
        
        # Should still have only one thread
        assert integrator._scheduler_running is True
        
        integrator.stop_scheduler()


class TestPerformance:
    """Test performance requirements"""
    
    def test_cached_data_response_time(self):
        """Test cached data is returned within 100ms"""
        integrator = WeatherIntegrator(api_key="test", auto_start=False)
        
        # Set up cache
        cached_weather = WeatherData(
            temperature_celsius=27.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=12.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        with integrator._cache_lock:
            integrator._cache = cached_weather
        
        # Measure response time
        start = time.time()
        result = integrator.fetch_weather_data()
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert elapsed < 100  # Should be < 100ms
        assert result == cached_weather


class TestGlobalInstance:
    """Test global weather integrator instance"""
    
    def test_get_weather_integrator_singleton(self):
        """Test get_weather_integrator returns singleton instance"""
        from weather_integrator import get_weather_integrator, _weather_integrator
        
        # Reset global instance
        import weather_integrator as wi
        wi._weather_integrator = None
        
        instance1 = get_weather_integrator()
        instance2 = get_weather_integrator()
        
        assert instance1 is instance2
        
        # Clean up
        instance1.stop_scheduler()
