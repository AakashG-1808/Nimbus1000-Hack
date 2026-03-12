import React from 'react';
import './WeatherPanel.css';

/**
 * WeatherPanel Component
 * Displays current weather conditions with visual indicators
 * 
 * Props:
 * - weather: {temperature_celsius, humidity_percent, precipitation_mm_per_hour, wind_speed_kmh, high_rainfall}
 * 
 * Validates: Requirements 15.1, 15.2, 15.3, 15.4
 */
const WeatherPanel = ({ weather }) => {
  // Check if weather data is null, undefined, or missing required properties
  if (!weather || 
      weather.temperature_celsius === undefined || 
      weather.humidity_percent === undefined || 
      weather.precipitation_mm_per_hour === undefined || 
      weather.wind_speed_kmh === undefined) {
    return (
      <div className="weather-panel">
        <div className="weather-loading">Loading weather data...</div>
      </div>
    );
  }

  const {
    temperature_celsius,
    humidity_percent,
    precipitation_mm_per_hour,
    wind_speed_kmh,
    high_rainfall
  } = weather;

  // Determine weather icon based on conditions
  const getWeatherIcon = () => {
    if (precipitation_mm_per_hour > 10) return '🌧️';
    if (precipitation_mm_per_hour > 0) return '🌦️';
    if (humidity_percent > 80) return '☁️';
    if (temperature_celsius > 30) return '☀️';
    return '🌤️';
  };

  return (
    <div className={`weather-panel ${high_rainfall ? 'high-rainfall' : ''}`}>
      <div className="weather-icon">
        {getWeatherIcon()}
      </div>
      
      <div className="weather-metrics">
        <div className="weather-metric">
          <span className="metric-icon">🌡️</span>
          <div className="metric-content">
            <span className="metric-label">Temperature</span>
            <span className="metric-value">{temperature_celsius.toFixed(1)}°C</span>
          </div>
        </div>

        <div className="weather-metric">
          <span className="metric-icon">💧</span>
          <div className="metric-content">
            <span className="metric-label">Humidity</span>
            <span className="metric-value">{humidity_percent.toFixed(0)}%</span>
          </div>
        </div>

        <div className="weather-metric">
          <span className="metric-icon">🌧️</span>
          <div className="metric-content">
            <span className="metric-label">Precipitation</span>
            <span className="metric-value">{precipitation_mm_per_hour.toFixed(1)} mm/hr</span>
          </div>
        </div>

        <div className="weather-metric">
          <span className="metric-icon">💨</span>
          <div className="metric-content">
            <span className="metric-label">Wind Speed</span>
            <span className="metric-value">{wind_speed_kmh.toFixed(1)} km/h</span>
          </div>
        </div>
      </div>

      {high_rainfall && (
        <div className="weather-alert">
          ⚠️ High Rainfall Alert
        </div>
      )}
    </div>
  );
};

export default WeatherPanel;
