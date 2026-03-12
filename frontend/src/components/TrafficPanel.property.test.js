import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import * as fc from 'fast-check';
import TrafficPanel from './TrafficPanel';

/**
 * Property-Based Tests for TrafficPanel Component
 * 
 * These tests validate universal correctness properties across all valid traffic data inputs.
 * Uses fast-check library with minimum 100 iterations per property.
 * 
 * Validates: Requirements 16.1, 16.2
 */

// Arbitrary generator for congestion levels
const congestionLevelArbitrary = () => fc.constantFrom('LOW', 'MEDIUM', 'HIGH', 'low', 'medium', 'high');

// Arbitrary generator for Bengaluru locations
const bengaluruLocationArbitrary = () => fc.constantFrom(
  'Koramangala',
  'Indiranagar',
  'Whitefield',
  'Electronic City',
  'Jayanagar',
  'Malleshwaram',
  'HSR Layout',
  'BTM Layout',
  'Marathahalli',
  'Silk Board',
  'Hebbal',
  'Yeshwanthpur',
  'MG Road',
  'Brigade Road',
  'Bannerghatta Road'
);

// Arbitrary generator for a single traffic data item
const trafficItemArbitrary = () => fc.record({
  location: bengaluruLocationArbitrary(),
  congestion_level: congestionLevelArbitrary(),
  congestion_score: fc.integer({ min: 1, max: 10 })
});

// Arbitrary generator for traffic data array (10+ locations as per requirement 16.4)
const trafficDataArrayArbitrary = () => fc.array(trafficItemArbitrary(), { minLength: 10, maxLength: 20 });

// Clean up after each test
afterEach(() => {
  cleanup();
});

describe('TrafficPanel Property-Based Tests', () => {
  /**
   * Property 43: Traffic Location Display
   * 
   * For any set of traffic data, the Map_Visualizer should display traffic 
   * congestion levels for major Bengaluru_Location areas.
   * 
   * **Validates: Requirements 16.1**
   */
  test('Property 43: All major locations in traffic data are displayed', () => {
    fc.assert(
      fc.property(trafficDataArrayArbitrary(), (trafficData) => {
        const { container, unmount } = render(<TrafficPanel trafficData={trafficData} />);
        
        try {
          // Verify the correct number of traffic items are rendered
          const trafficItems = container.querySelectorAll('.traffic-item');
          expect(trafficItems.length).toBe(trafficData.length);
          
          // Verify all locations from the traffic data array are displayed
          trafficData.forEach((traffic, index) => {
            const trafficItem = trafficItems[index];
            
            // Verify location is displayed in the correct traffic item
            const locationElement = trafficItem.querySelector('.location-name');
            expect(locationElement).toBeInTheDocument();
            expect(locationElement.textContent).toBe(traffic.location);
            
            // Verify the congestion level is displayed
            const statusElement = trafficItem.querySelector('.status-text');
            expect(statusElement).toBeInTheDocument();
            expect(statusElement.textContent).toBe(traffic.congestion_level);
          });
        } finally {
          // Clean up after each iteration
          unmount();
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 44: Traffic Congestion Color Coding
   * 
   * For any traffic congestion level displayed, the Map_Visualizer should use 
   * color coding: green for low, yellow for medium, red for high.
   * 
   * **Validates: Requirements 16.2**
   */
  test('Property 44: Correct color coding for all congestion levels', () => {
    fc.assert(
      fc.property(trafficDataArrayArbitrary(), (trafficData) => {
        const { container, unmount } = render(<TrafficPanel trafficData={trafficData} />);
        
        try {
          // Verify each traffic item has the correct color class
          trafficData.forEach((traffic, index) => {
            const trafficItems = container.querySelectorAll('.traffic-item');
            const trafficItem = trafficItems[index];
            
            const statusElement = trafficItem.querySelector('.traffic-status');
            expect(statusElement).toBeInTheDocument();
            
            const levelUpper = traffic.congestion_level.toUpperCase();
            
            // Verify correct CSS class is applied based on congestion level
            if (levelUpper === 'LOW') {
              expect(statusElement).toHaveClass('congestion-low');
              // Verify green icon
              const iconElement = statusElement.querySelector('.status-icon');
              expect(iconElement.textContent).toBe('🟢');
            } else if (levelUpper === 'MEDIUM') {
              expect(statusElement).toHaveClass('congestion-medium');
              // Verify yellow icon
              const iconElement = statusElement.querySelector('.status-icon');
              expect(iconElement.textContent).toBe('🟡');
            } else if (levelUpper === 'HIGH') {
              expect(statusElement).toHaveClass('congestion-high');
              // Verify red icon
              const iconElement = statusElement.querySelector('.status-icon');
              expect(iconElement.textContent).toBe('🔴');
            }
          });
        } finally {
          // Clean up after each iteration
          unmount();
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Additional test: Verify component handles empty traffic data gracefully
   */
  test('Component displays loading state when traffic data is empty', () => {
    const { container } = render(<TrafficPanel trafficData={[]} />);
    
    const loadingElement = screen.getByText(/Loading traffic data/i);
    expect(loadingElement).toBeInTheDocument();
  });

  test('Component displays loading state when traffic data is null', () => {
    const { container } = render(<TrafficPanel trafficData={null} />);
    
    const loadingElement = screen.getByText(/Loading traffic data/i);
    expect(loadingElement).toBeInTheDocument();
  });

  test('Component displays loading state when traffic data is undefined', () => {
    const { container } = render(<TrafficPanel trafficData={undefined} />);
    
    const loadingElement = screen.getByText(/Loading traffic data/i);
    expect(loadingElement).toBeInTheDocument();
  });
});
