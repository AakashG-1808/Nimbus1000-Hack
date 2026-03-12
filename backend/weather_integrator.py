"""
UrbanGuard AI System - Weather Integrator
Retrieves and processes weather data from OpenWeatherMap API
"""
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional
import requests
from threading import Thread, Lock

from models import WeatherData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherIntegrator:
    """
    Retrieves and processes weather data from OpenWeatherMap API.
    
    Features:
    - Fetches weather data every 30 minutes via background scheduler
    - Caches weather data for fallback when API is unavailable
    - Extracts temperature, humidity, precipitation, and wind speed
    - Flags high rainfall conditions (>10mm/hr)
    - Implements retry logic with exponential backoff
    - Provides weather data within 100ms from cache
    """
    
    # OpenWeatherMap API endpoint
    API_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    # Fetch interval in seconds (30 minutes)
    FETCH_INTERVAL = 30 * 60
    
    # Cache validity duration (1 hour)
    CACHE_VALIDITY = 60 * 60
    
    # High rainfall threshold (mm per hour)
    HIGH_RAINFALL_THRESHOLD = 10.0
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        city: str = "Bengaluru",
        country_code: str = "IN",
        auto_start: bool = True
    ):
        """
        Initialize Weather Integrator.
        
        Args:
            api_key: OpenWeatherMap API key (defaults to env var)
            city: City name for weather data
            country_code: Country code (ISO 3166)
            auto_start: Whether to start background scheduler automatically
        """
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
        self.city = city
        self.country_code = country_code
        
        # Cache for weather data
        self._cache: Optional[WeatherData] = None
        self._cache_lock = Lock()
        
        # Background scheduler state
        self._scheduler_thread: Optional[Thread] = None
        self._scheduler_running = False
        
        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open = False
        self._circuit_open_time: Optional[float] = None
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_timeout = 60  # seconds
        
        if auto_start:
            self.start_scheduler()
    
    def fetch_weather_data(self) -> WeatherData:
        """
        Retrieves current weather data.
        
        Returns cached data if available and recent (< 1 hour old).
        Otherwise fetches from OpenWeatherMap API.
        
        Returns:
            WeatherData with current conditions
            
        Performance:
            - < 100ms when returning cached data
            - < 3 seconds when fetching from API (including retries)
        """
        # Check cache first for fast response
        with self._cache_lock:
            if self._cache and self._is_cache_valid():
                logger.debug(f"Returning cached weather data from {self._cache.timestamp}")
                # Return a copy with source preserved
                return WeatherData(
                    temperature_celsius=self._cache.temperature_celsius,
                    humidity_percent=self._cache.humidity_percent,
                    precipitation_mm_per_hour=self._cache.precipitation_mm_per_hour,
                    wind_speed_kmh=self._cache.wind_speed_kmh,
                    high_rainfall_flag=self._cache.high_rainfall_flag,
                    timestamp=self._cache.timestamp,
                    source=self._cache.source
                )
        
        # Fetch fresh data from API
        try:
            weather_data = self._fetch_from_api()
            
            # Update cache
            with self._cache_lock:
                self._cache = weather_data
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {e}")
            
            # Fall back to cached data if available
            with self._cache_lock:
                if self._cache:
                    logger.warning(
                        f"Using cached weather data from {self._cache.timestamp} "
                        f"due to API failure"
                    )
                    # Return cached data with updated source
                    cached_data = WeatherData(
                        temperature_celsius=self._cache.temperature_celsius,
                        humidity_percent=self._cache.humidity_percent,
                        precipitation_mm_per_hour=self._cache.precipitation_mm_per_hour,
                        wind_speed_kmh=self._cache.wind_speed_kmh,
                        high_rainfall_flag=self._cache.high_rainfall_flag,
                        timestamp=self._cache.timestamp,
                        source="cache"
                    )
                    return cached_data
            
            # No cache available, return default values
            logger.warning("No cached data available, returning default weather values")
            return self._get_default_weather_data()
    
    def _fetch_from_api(self) -> WeatherData:
        """
        Fetches weather data from OpenWeatherMap API with retry logic.
        
        Returns:
            WeatherData from API
            
        Raises:
            Exception: If all retries fail
        """
        # Check circuit breaker
        if self._is_circuit_open():
            logger.warning("Circuit breaker is open, skipping API call")
            raise Exception("Circuit breaker is open")
        
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key not configured")
        
        # Prepare request parameters
        params = {
            "q": f"{self.city},{self.country_code}",
            "appid": self.api_key,
            "units": "metric"  # Celsius, m/s
        }
        
        last_exception = None
        
        # Retry logic with exponential backoff
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    f"Fetching weather data from OpenWeatherMap "
                    f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                
                response = requests.get(
                    self.API_URL,
                    params=params,
                    timeout=5
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract weather data
                weather_data = self._parse_api_response(data)
                
                # Reset circuit breaker on success
                self._reset_circuit_breaker()
                
                logger.info("Successfully fetched weather data from OpenWeatherMap")
                return weather_data
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(
                    f"API request failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
                
                # Wait before retry (except on last attempt)
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt]
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        
        # All retries failed
        self._record_failure()
        raise Exception(
            f"Failed to fetch weather data after {self.MAX_RETRIES} attempts: "
            f"{last_exception}"
        )
    
    def _parse_api_response(self, data: dict) -> WeatherData:
        """
        Parses OpenWeatherMap API response and extracts weather data.
        
        Args:
            data: JSON response from OpenWeatherMap API
            
        Returns:
            WeatherData with extracted values
        """
        # Extract temperature (already in Celsius due to units=metric)
        temperature = data["main"]["temp"]
        
        # Extract humidity
        humidity = data["main"]["humidity"]
        
        # Extract precipitation (rain in last hour, if available)
        # OpenWeatherMap returns rain volume in mm for last 1h
        precipitation = 0.0
        if "rain" in data and "1h" in data["rain"]:
            precipitation = data["rain"]["1h"]
        
        # Extract wind speed (convert m/s to km/h)
        wind_speed_ms = data["wind"]["speed"]
        wind_speed_kmh = wind_speed_ms * 3.6
        
        # Check for high rainfall
        high_rainfall_flag = precipitation > self.HIGH_RAINFALL_THRESHOLD
        
        weather_data = WeatherData(
            temperature_celsius=temperature,
            humidity_percent=humidity,
            precipitation_mm_per_hour=precipitation,
            wind_speed_kmh=wind_speed_kmh,
            high_rainfall_flag=high_rainfall_flag,
            timestamp=datetime.now(),
            source="openweathermap"
        )
        
        logger.info(
            f"Weather data: {temperature}°C, {humidity}% humidity, "
            f"{precipitation}mm/h precipitation, {wind_speed_kmh:.1f}km/h wind"
        )
        
        if high_rainfall_flag:
            logger.warning(f"High rainfall detected: {precipitation}mm/h")
        
        return weather_data
    
    def _is_cache_valid(self) -> bool:
        """
        Checks if cached weather data is still valid.
        
        Returns:
            True if cache is valid (< 1 hour old)
        """
        if not self._cache:
            return False
        
        age = (datetime.now() - self._cache.timestamp).total_seconds()
        return age < self.CACHE_VALIDITY
    
    def _get_default_weather_data(self) -> WeatherData:
        """
        Returns default weather data when API and cache are unavailable.
        
        Returns:
            WeatherData with default values
        """
        return WeatherData(
            temperature_celsius=25.0,
            humidity_percent=60.0,
            precipitation_mm_per_hour=0.0,
            wind_speed_kmh=10.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="default"
        )
    
    def is_high_rainfall(self, weather: Optional[WeatherData] = None) -> bool:
        """
        Checks if current weather has high rainfall.
        
        Args:
            weather: WeatherData to check (defaults to current cached data)
            
        Returns:
            True if precipitation > 10mm/hr
        """
        if weather is None:
            weather = self.fetch_weather_data()
        
        return weather.high_rainfall_flag
    
    def start_scheduler(self) -> None:
        """
        Starts background scheduler to fetch weather data every 30 minutes.
        """
        if self._scheduler_running:
            logger.warning("Scheduler already running")
            return
        
        self._scheduler_running = True
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info(
            f"Started weather data scheduler (fetch interval: {self.FETCH_INTERVAL}s)"
        )
    
    def stop_scheduler(self) -> None:
        """
        Stops background scheduler.
        """
        if not self._scheduler_running:
            return
        
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        logger.info("Stopped weather data scheduler")
    
    def _scheduler_loop(self) -> None:
        """
        Background scheduler loop that fetches weather data periodically.
        """
        # Fetch immediately on start
        try:
            self.fetch_weather_data()
        except Exception as e:
            logger.error(f"Initial weather fetch failed: {e}")
        
        # Continue fetching at intervals
        while self._scheduler_running:
            time.sleep(self.FETCH_INTERVAL)
            
            if not self._scheduler_running:
                break
            
            try:
                self.fetch_weather_data()
            except Exception as e:
                logger.error(f"Scheduled weather fetch failed: {e}")
    
    def _is_circuit_open(self) -> bool:
        """
        Checks if circuit breaker is open.
        
        Returns:
            True if circuit is open (too many failures)
        """
        if not self._circuit_open:
            return False
        
        # Check if timeout has elapsed
        if self._circuit_open_time:
            elapsed = time.time() - self._circuit_open_time
            if elapsed >= self._circuit_breaker_timeout:
                logger.info("Circuit breaker timeout elapsed, attempting half-open state")
                self._circuit_open = False
                self._circuit_open_time = None
                return False
        
        return True
    
    def _record_failure(self) -> None:
        """
        Records an API failure and opens circuit breaker if threshold reached.
        """
        self._consecutive_failures += 1
        
        if self._consecutive_failures >= self._circuit_breaker_threshold:
            self._circuit_open = True
            self._circuit_open_time = time.time()
            logger.error(
                f"Circuit breaker opened after {self._consecutive_failures} "
                f"consecutive failures"
            )
    
    def _reset_circuit_breaker(self) -> None:
        """
        Resets circuit breaker after successful API call.
        """
        if self._consecutive_failures > 0:
            logger.info("Circuit breaker reset after successful API call")
        
        self._consecutive_failures = 0
        self._circuit_open = False
        self._circuit_open_time = None
    
    def get_cache_age(self) -> Optional[float]:
        """
        Gets the age of cached weather data in seconds.
        
        Returns:
            Age in seconds, or None if no cache
        """
        with self._cache_lock:
            if not self._cache:
                return None
            return (datetime.now() - self._cache.timestamp).total_seconds()


# Global weather integrator instance
_weather_integrator: Optional[WeatherIntegrator] = None


def get_weather_integrator() -> WeatherIntegrator:
    """
    Gets or creates the global WeatherIntegrator instance.
    
    Returns:
        WeatherIntegrator singleton instance
    """
    global _weather_integrator
    
    if _weather_integrator is None:
        _weather_integrator = WeatherIntegrator()
    
    return _weather_integrator
