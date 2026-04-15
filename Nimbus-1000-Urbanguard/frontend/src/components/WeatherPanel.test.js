import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import WeatherPanel from './WeatherPanel';

describe('WeatherPanel', () => {
  const mockWeatherData = {
    temperature_celsius: 25.3,
    humidity_percent: 65,
    precipitation_mm_per_hour: 5.2,
    wind_speed_kmh: 15.8,
    high_rainfall: false
  };

  const mockHighRainfallData = {
    temperature_celsius: 22.1,
    humidity_percent: 85,
    precipitation_mm_per_hour: 12.5,
    wind_speed_kmh: 20.3,
    high_rainfall: true
  };

  test('renders loading state when weather data is null', () => {
    render(<WeatherPanel weather={null} />);
    expect(screen.getByText('Loading weather data...')).toBeInTheDocument();
  });

  test('displays all four weather metrics', () => {
    render(<WeatherPanel weather={mockWeatherData} />);
    
    // Check for temperature
    expect(screen.getByText('Temperature')).toBeInTheDocument();
    expect(screen.getByText('25.3°C')).toBeInTheDocument();
    
    // Check for humidity
    expect(screen.getByText('Humidity')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();
    
    // Check for precipitation
    expect(screen.getByText('Precipitation')).toBeInTheDocument();
    expect(screen.getByText('5.2 mm/hr')).toBeInTheDocument();
    
    // Check for wind speed
    expect(screen.getByText('Wind Speed')).toBeInTheDocument();
    expect(screen.getByText('15.8 km/h')).toBeInTheDocument();
  });

  test('formats numbers appropriately', () => {
    const weatherData = {
      temperature_celsius: 25.345,
      humidity_percent: 64.789,
      precipitation_mm_per_hour: 5.234,
      wind_speed_kmh: 15.876,
      high_rainfall: false
    };
    
    render(<WeatherPanel weather={weatherData} />);
    
    // Temperature should have 1 decimal place
    expect(screen.getByText('25.3°C')).toBeInTheDocument();
    
    // Humidity should be rounded to integer
    expect(screen.getByText('65%')).toBeInTheDocument();
    
    // Precipitation should have 1 decimal place
    expect(screen.getByText('5.2 mm/hr')).toBeInTheDocument();
    
    // Wind speed should have 1 decimal place
    expect(screen.getByText('15.9 km/h')).toBeInTheDocument();
  });

  test('does not show high rainfall alert when high_rainfall is false', () => {
    render(<WeatherPanel weather={mockWeatherData} />);
    expect(screen.queryByText(/High Rainfall Alert/i)).not.toBeInTheDocument();
  });

  test('highlights panel in red when high rainfall detected', () => {
    const { container } = render(<WeatherPanel weather={mockHighRainfallData} />);
    const panel = container.querySelector('.weather-panel');
    expect(panel).toHaveClass('high-rainfall');
  });

  test('shows high rainfall alert when high_rainfall is true', () => {
    render(<WeatherPanel weather={mockHighRainfallData} />);
    expect(screen.getByText(/High Rainfall Alert/i)).toBeInTheDocument();
  });

  test('displays weather icon', () => {
    const { container } = render(<WeatherPanel weather={mockWeatherData} />);
    const icon = container.querySelector('.weather-icon');
    expect(icon).toBeInTheDocument();
    expect(icon.textContent).toBeTruthy();
  });

  test('shows rain icon when precipitation is high', () => {
    const { container } = render(<WeatherPanel weather={mockHighRainfallData} />);
    const icon = container.querySelector('.weather-icon');
    expect(icon.textContent).toBe('🌧️');
  });

  test('shows appropriate icon for light rain', () => {
    const lightRainData = {
      ...mockWeatherData,
      precipitation_mm_per_hour: 2.5
    };
    const { container } = render(<WeatherPanel weather={lightRainData} />);
    const icon = container.querySelector('.weather-icon');
    expect(icon.textContent).toBe('🌦️');
  });

  test('shows sunny icon for hot weather', () => {
    const hotWeatherData = {
      ...mockWeatherData,
      temperature_celsius: 35,
      precipitation_mm_per_hour: 0
    };
    const { container } = render(<WeatherPanel weather={hotWeatherData} />);
    const icon = container.querySelector('.weather-icon');
    expect(icon.textContent).toBe('☀️');
  });
});
