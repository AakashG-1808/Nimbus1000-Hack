import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import TrafficPanel from './TrafficPanel';

/**
 * Visual verification test for TrafficPanel
 * Tests the component renders correctly with sample data
 */
describe('TrafficPanel Visual Verification', () => {
  const sampleTrafficData = [
    { location: 'Koramangala', congestion_level: 'LOW', congestion_score: 1 },
    { location: 'Indiranagar', congestion_level: 'MEDIUM', congestion_score: 5 },
    { location: 'Whitefield', congestion_level: 'HIGH', congestion_score: 10 },
    { location: 'Electronic City', congestion_level: 'LOW', congestion_score: 1 },
    { location: 'Jayanagar', congestion_level: 'MEDIUM', congestion_score: 5 },
    { location: 'Malleshwaram', congestion_level: 'HIGH', congestion_score: 10 },
    { location: 'HSR Layout', congestion_level: 'LOW', congestion_score: 1 },
    { location: 'BTM Layout', congestion_level: 'MEDIUM', congestion_score: 5 },
    { location: 'MG Road', congestion_level: 'HIGH', congestion_score: 10 },
    { location: 'Silk Board', congestion_level: 'HIGH', congestion_score: 10 },
    { location: 'Marathahalli', congestion_level: 'MEDIUM', congestion_score: 5 }
  ];

  test('renders with 10+ locations showing color-coded congestion levels', () => {
    const { container } = render(<TrafficPanel trafficData={sampleTrafficData} />);
    
    // Verify component renders
    expect(container.querySelector('.traffic-panel')).toBeInTheDocument();
    
    // Verify all locations are displayed
    expect(container.querySelectorAll('.traffic-item').length).toBe(11);
    
    // Verify color coding is applied
    expect(container.querySelectorAll('.congestion-low').length).toBeGreaterThan(0);
    expect(container.querySelectorAll('.congestion-medium').length).toBeGreaterThan(0);
    expect(container.querySelectorAll('.congestion-high').length).toBeGreaterThan(0);
    
    // Verify scrollable list
    expect(container.querySelector('.traffic-list')).toBeInTheDocument();
  });

  test('integrates with Dashboard data structure', () => {
    // Simulate data from Dashboard API
    const dashboardTrafficData = [
      { location: 'Koramangala', congestion_level: 'LOW', congestion_score: 1 },
      { location: 'Indiranagar', congestion_level: 'MEDIUM', congestion_score: 5 },
      { location: 'Whitefield', congestion_level: 'HIGH', congestion_score: 10 }
    ];
    
    const { container } = render(<TrafficPanel trafficData={dashboardTrafficData} />);
    
    // Verify it accepts the Dashboard data format
    expect(container.querySelector('.traffic-panel')).toBeInTheDocument();
    expect(container.querySelectorAll('.traffic-item').length).toBe(3);
  });
});
