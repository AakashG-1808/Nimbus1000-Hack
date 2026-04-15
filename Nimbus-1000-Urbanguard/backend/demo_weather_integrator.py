"""
Demo script for Weather Integrator
Shows how to use the Weather_Integrator component
"""
import os
import time
from dotenv import load_dotenv
from weather_integrator import WeatherIntegrator, get_weather_integrator

# Load environment variables
load_dotenv()


def demo_basic_usage():
    """Demonstrate basic weather data fetching"""
    print("=" * 60)
    print("Demo 1: Basic Weather Data Fetching")
    print("=" * 60)
    
    # Create integrator (without auto-start for demo)
    integrator = WeatherIntegrator(auto_start=False)
    
    print(f"\nFetching weather data for {integrator.city}, {integrator.country_code}...")
    
    try:
        weather = integrator.fetch_weather_data()
        
        print(f"\n✓ Weather data retrieved successfully!")
        print(f"  Source: {weather.source}")
        print(f"  Temperature: {weather.temperature_celsius}°C")
        print(f"  Humidity: {weather.humidity_percent}%")
        print(f"  Precipitation: {weather.precipitation_mm_per_hour}mm/h")
        print(f"  Wind Speed: {weather.wind_speed_kmh:.1f}km/h")
        print(f"  High Rainfall: {'Yes' if weather.high_rainfall_flag else 'No'}")
        print(f"  Timestamp: {weather.timestamp}")
        
    except Exception as e:
        print(f"\n✗ Error fetching weather data: {e}")


def demo_high_rainfall_detection():
    """Demonstrate high rainfall detection"""
    print("\n" + "=" * 60)
    print("Demo 2: High Rainfall Detection")
    print("=" * 60)
    
    integrator = WeatherIntegrator(auto_start=False)
    
    try:
        weather = integrator.fetch_weather_data()
        
        if integrator.is_high_rainfall(weather):
            print(f"\n⚠️  HIGH RAINFALL ALERT!")
            print(f"   Precipitation: {weather.precipitation_mm_per_hour}mm/h")
            print(f"   (Threshold: {WeatherIntegrator.HIGH_RAINFALL_THRESHOLD}mm/h)")
        else:
            print(f"\n✓ Normal rainfall conditions")
            print(f"  Precipitation: {weather.precipitation_mm_per_hour}mm/h")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


def demo_caching():
    """Demonstrate caching mechanism"""
    print("\n" + "=" * 60)
    print("Demo 3: Caching Mechanism")
    print("=" * 60)
    
    integrator = WeatherIntegrator(auto_start=False)
    
    print("\nFirst fetch (from API)...")
    start = time.time()
    weather1 = integrator.fetch_weather_data()
    time1 = (time.time() - start) * 1000
    print(f"  Time: {time1:.2f}ms")
    print(f"  Source: {weather1.source}")
    
    print("\nSecond fetch (from cache)...")
    start = time.time()
    weather2 = integrator.fetch_weather_data()
    time2 = (time.time() - start) * 1000
    print(f"  Time: {time2:.2f}ms")
    print(f"  Source: {weather2.source}")
    
    print(f"\n✓ Cache speedup: {time1/time2:.1f}x faster")
    
    cache_age = integrator.get_cache_age()
    if cache_age:
        print(f"  Cache age: {cache_age:.1f} seconds")


def demo_background_scheduler():
    """Demonstrate background scheduler"""
    print("\n" + "=" * 60)
    print("Demo 4: Background Scheduler")
    print("=" * 60)
    
    print("\nStarting background scheduler...")
    print(f"Fetch interval: {WeatherIntegrator.FETCH_INTERVAL} seconds (30 minutes)")
    
    # Use global singleton with auto-start
    integrator = get_weather_integrator()
    
    print("\n✓ Scheduler started!")
    print("  Weather data will be fetched automatically every 30 minutes")
    print("  You can call fetch_weather_data() anytime to get cached data")
    
    # Get current weather
    weather = integrator.fetch_weather_data()
    print(f"\nCurrent weather: {weather.temperature_celsius}°C, {weather.humidity_percent}% humidity")
    
    # Stop scheduler for demo
    integrator.stop_scheduler()
    print("\n✓ Scheduler stopped")


def demo_error_handling():
    """Demonstrate error handling and fallback"""
    print("\n" + "=" * 60)
    print("Demo 5: Error Handling and Fallback")
    print("=" * 60)
    
    # Create integrator with invalid API key
    integrator = WeatherIntegrator(api_key="invalid_key", auto_start=False)
    
    print("\nAttempting to fetch with invalid API key...")
    print("(This will demonstrate fallback to default values)")
    
    try:
        weather = integrator.fetch_weather_data()
        
        print(f"\n✓ Graceful fallback to default values:")
        print(f"  Source: {weather.source}")
        print(f"  Temperature: {weather.temperature_celsius}°C")
        print(f"  Humidity: {weather.humidity_percent}%")
        print(f"  Precipitation: {weather.precipitation_mm_per_hour}mm/h")
        print(f"  Wind Speed: {weather.wind_speed_kmh}km/h")
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("Weather Integrator Demo")
    print("=" * 60)
    
    # Check if API key is configured
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\n⚠️  WARNING: OpenWeatherMap API key not configured!")
        print("   Set OPENWEATHERMAP_API_KEY in .env file")
        print("   Demos will use fallback/default values\n")
    else:
        print(f"\n✓ API key configured")
    
    # Run demos
    demo_basic_usage()
    demo_high_rainfall_detection()
    demo_caching()
    demo_background_scheduler()
    demo_error_handling()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
