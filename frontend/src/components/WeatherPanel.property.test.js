import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import * as fc from 'fast-check';
import WeatherPanel from './WeatherPanel';

/**
 * Property-Based Tests for WeatherPanel Component
 * 
 * These tests validate universal correctness properties across all valid weather data inputs.
 * Uses fast-check library with minimum 100 iterations per property.
 * 
 * Validates: Requirements 15.1, 15.3, 15.4
 */

// Arbitrary generator for realistic weather data
const weatherDataArbitrary = () => fc.record({
  temperature_celsius: fc.double({ min: -10, max: 50, noNaN: true }),
  humidity_percent: fc.double({ min: 0, max: 100, noNaN: true }),
  precipitation_mm_per_hour: fc.double({ min: 0, max: 50, noNaN: true }),
  wind_speed_kmh: fc.double({ min: 0, max: 100, noNaN: true }),
  high_rainfall: fc.boolean()
});

// Clean up after each test
afterEach(() => {
  cleanup();
});

describe('WeatherPanel Property-Based Tests', () => {
  /**
   * Property 40: Weather Display Completeness
   * 
   * For any weather data, the Map_Visualizer should display temperature, 
   * humidity, precipitation, and wind speed.
   * 
   * **Validates: Requirements 15.1**
   */
  test('Property 40: All weather fields are displayed for any valid weather data', () => {
    fc.assert(
      fc.property(weatherDataArbitrary(), (weather) => {
        const { container, unmount } = render(<WeatherPanel weather={weather} />);
        
        try {
          // Verify all four weather fields are displayed
          const temperatureElement = screen.getByText(/Temperature/i);
          const humidityElement = screen.getByText(/Humidity/i);
          const precipitationElement = screen.getByText(/Precipitation/i);
          const windElement = screen.getByText(/Wind Speed/i);
          
          expect(temperatureElement).toBeInTheDocument();
          expect(humidityElement).toBeInTheDocument();
          expect(precipitationElement).toBeInTheDocument();
          expect(windElement).toBeInTheDocument();
          
          // Verify the values are displayed
          expect(container.textContent).toContain(weather.temperature_celsius.toFixed(1));
          expect(container.textContent).toContain(weather.humidity_percent.toFixed(0));
          expect(container.textContent).toContain(weather.precipitation_mm_per_hour.toFixed(1));
          expect(container.textContent).toContain(weather.wind_speed_kmh.toFixed(1));
        } finally {
          // Clean up after each iteration
          unmount();
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 41: High Rainfall Weather Panel Highlighting
   * 
   * For any weather data, if high rainfall conditions are detected, 
   * the Map_Visualizer should highlight the weather panel in red.
   * 
   * **Validates: Requirements 15.3**
   */
  test('Property 41: Weather panel is highlighted in red when high_rainfall is true', () => {
    fc.assert(
      fc.property(weatherDataArbitrary(), (weather) => {
        const { container, unmount } = render(<WeatherPanel weather={weather} />);
        
        try {
          const weatherPanel = container.querySelector('.weather-panel');
          expect(weatherPanel).toBeInTheDocument();
          
          if (weather.high_rainfall) {
            // When high_rainfall is true, panel should have high-rainfall class
            expect(weatherPanel).toHaveClass('high-rainfall');
            
            // Verify red highlighting via CSS class (the CSS applies red border and background)
            // The high-rainfall class is applied which triggers the red styling
            
            // Verify alert message is displayed
            const alertElement = container.querySelector('.weather-alert');
            expect(alertElement).toBeInTheDocument();
            expect(alertElement.textContent).toContain('High Rainfall Alert');
          } else {
            // When high_rainfall is false, panel should not have high-rainfall class
            expect(weatherPanel).not.toHaveClass('high-rainfall');
            
            // Verify alert message is not displayed
            const alertElement = container.querySelector('.weather-alert');
            expect(alertElement).not.toBeInTheDocument();
          }
        } finally {
          // Clean up after each iteration
          unmount();
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 42: Weather Icon Selection
   * 
   * For any weather condition, the Map_Visualizer should display a weather icon 
   * corresponding to the current conditions.
   * 
   * **Validates: Requirements 15.4**
   */
  test('Property 42: Weather icon matches current conditions', () => {
    fc.assert(
      fc.property(weatherDataArbitrary(), (weather) => {
        const { container, unmount } = render(<WeatherPanel weather={weather} />);
        
        try {
          const weatherIcon = container.querySelector('.weather-icon');
          expect(weatherIcon).toBeInTheDocument();
          
          const iconText = weatherIcon.textContent;
          
          // Verify icon selection logic matches conditions
          // Icon logic from WeatherPanel.js:
          // - precipitation > 10mm/hr → 🌧️ (heavy rain)
          // - precipitation > 0mm/hr → 🌦️ (light rain)
          // - humidity > 80% → ☁️ (cloudy)
          // - temperature > 30°C → ☀️ (sunny)
          // - default → 🌤️ (partly cloudy)
          
          if (weather.precipitation_mm_per_hour > 10) {
            expect(iconText).toBe('🌧️');
          } else if (weather.precipitation_mm_per_hour > 0) {
            expect(iconText).toBe('🌦️');
          } else if (weather.humidity_percent > 80) {
            expect(iconText).toBe('☁️');
          } else if (weather.temperature_celsius > 30) {
            expect(iconText).toBe('☀️');
          } else {
            expect(iconText).toBe('🌤️');
          }
        } finally {
          // Clean up after each iteration
          unmount();
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Additional test: Verify component handles missing weather data gracefully
   */
  test('Component displays loading state when weather data is missing', () => {
    const { container } = render(<WeatherPanel weather={null} />);
    
    const loadingElement = screen.getByText(/Loading weather data/i);
    expect(loadingElement).toBeInTheDocument();
  });

  test('Component displays loading state when weather data is incomplete', () => {
    const incompleteWeather = {
      temperature_celsius: 25,
      humidity_percent: 60
      // Missing precipitation and wind_speed
    };
    
    const { container } = render(<WeatherPanel weather={incompleteWeather} />);
    
    const loadingElement = screen.getByText(/Loading weather data/i);
    expect(loadingElement).toBeInTheDocument();
  });
});
