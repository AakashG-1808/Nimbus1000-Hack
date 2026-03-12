import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TrafficPanel from './TrafficPanel';

describe('TrafficPanel', () => {
  const mockTrafficData = [
    { location: 'Koramangala', congestion_level: 'LOW', congestion_score: 1 },
    { location: 'Indiranagar', congestion_level: 'MEDIUM', congestion_score: 5 },
    { location: 'Whitefield', congestion_level: 'HIGH', congestion_score: 10 },
    { location: 'Electronic City', congestion_level: 'LOW', congestion_score: 1 },
    { location: 'Jayanagar', congestion_level: 'MEDIUM', congestion_score: 5 },
    { location: 'Malleshwaram', congestion_level: 'HIGH', congestion_score: 10 },
    { location: 'HSR Layout', congestion_level: 'LOW', congestion_score: 1 },
    { location: 'BTM Layout', congestion_level: 'MEDIUM', congestion_score: 5 },
    { location: 'MG Road', congestion_level: 'HIGH', congestion_score: 10 },
    { location: 'Silk Board', congestion_level: 'HIGH', congestion_score: 10 }
  ];

  test('renders loading state when traffic data is null', () => {
    render(<TrafficPanel trafficData={null} />);
    expect(screen.getByText('Loading traffic data...')).toBeInTheDocument();
  });

  test('renders loading state when traffic data is empty array', () => {
    render(<TrafficPanel trafficData={[]} />);
    expect(screen.getByText('Loading traffic data...')).toBeInTheDocument();
  });

  test('displays all traffic locations', () => {
    render(<TrafficPanel trafficData={mockTrafficData} />);
    
    mockTrafficData.forEach(traffic => {
      expect(screen.getByText(traffic.location)).toBeInTheDocument();
    });
  });

  test('displays at least 10 key locations', () => {
    render(<TrafficPanel trafficData={mockTrafficData} />);
    
    const trafficItems = screen.getAllByText(/Koramangala|Indiranagar|Whitefield|Electronic City|Jayanagar|Malleshwaram|HSR Layout|BTM Layout|MG Road|Silk Board/);
    expect(trafficItems.length).toBeGreaterThanOrEqual(10);
  });

  test('displays congestion levels for all locations', () => {
    render(<TrafficPanel trafficData={mockTrafficData} />);
    
    // Check that congestion levels are displayed
    const lowLevels = screen.getAllByText('LOW');
    const mediumLevels = screen.getAllByText('MEDIUM');
    const highLevels = screen.getAllByText('HIGH');
    
    expect(lowLevels.length).toBeGreaterThan(0);
    expect(mediumLevels.length).toBeGreaterThan(0);
    expect(highLevels.length).toBeGreaterThan(0);
  });

  test('applies green color coding for LOW congestion', () => {
    const lowTrafficData = [
      { location: 'Test Location', congestion_level: 'LOW', congestion_score: 1 }
    ];
    
    const { container } = render(<TrafficPanel trafficData={lowTrafficData} />);
    const statusElement = container.querySelector('.congestion-low');
    expect(statusElement).toBeInTheDocument();
  });

  test('applies yellow color coding for MEDIUM congestion', () => {
    const mediumTrafficData = [
      { location: 'Test Location', congestion_level: 'MEDIUM', congestion_score: 5 }
    ];
    
    const { container } = render(<TrafficPanel trafficData={mediumTrafficData} />);
    const statusElement = container.querySelector('.congestion-medium');
    expect(statusElement).toBeInTheDocument();
  });

  test('applies red color coding for HIGH congestion', () => {
    const highTrafficData = [
      { location: 'Test Location', congestion_level: 'HIGH', congestion_score: 10 }
    ];
    
    const { container } = render(<TrafficPanel trafficData={highTrafficData} />);
    const statusElement = container.querySelector('.congestion-high');
    expect(statusElement).toBeInTheDocument();
  });

  test('handles case-insensitive congestion levels', () => {
    const mixedCaseData = [
      { location: 'Location 1', congestion_level: 'low', congestion_score: 1 },
      { location: 'Location 2', congestion_level: 'Medium', congestion_score: 5 },
      { location: 'Location 3', congestion_level: 'HiGh', congestion_score: 10 }
    ];
    
    const { container } = render(<TrafficPanel trafficData={mixedCaseData} />);
    
    expect(container.querySelector('.congestion-low')).toBeInTheDocument();
    expect(container.querySelector('.congestion-medium')).toBeInTheDocument();
    expect(container.querySelector('.congestion-high')).toBeInTheDocument();
  });

  test('displays correct icons for each congestion level', () => {
    const { container } = render(<TrafficPanel trafficData={mockTrafficData} />);
    
    const icons = container.querySelectorAll('.status-icon');
    expect(icons.length).toBe(mockTrafficData.length);
    
    // Check that icons are present (emojis)
    icons.forEach(icon => {
      expect(icon.textContent).toMatch(/🟢|🟡|🔴/);
    });
  });

  test('renders scrollable list for many locations', () => {
    const { container } = render(<TrafficPanel trafficData={mockTrafficData} />);
    const trafficList = container.querySelector('.traffic-list');
    
    expect(trafficList).toBeInTheDocument();
    expect(trafficList).toHaveClass('traffic-list');
  });

  test('displays location icons', () => {
    const { container } = render(<TrafficPanel trafficData={mockTrafficData} />);
    const locationIcons = container.querySelectorAll('.location-icon');
    
    expect(locationIcons.length).toBe(mockTrafficData.length);
    locationIcons.forEach(icon => {
      expect(icon.textContent).toBe('📍');
    });
  });

  test('component updates when props change', () => {
    const { rerender } = render(<TrafficPanel trafficData={mockTrafficData} />);
    expect(screen.getByText('Koramangala')).toBeInTheDocument();
    
    const newTrafficData = [
      { location: 'New Location', congestion_level: 'LOW', congestion_score: 1 }
    ];
    
    rerender(<TrafficPanel trafficData={newTrafficData} />);
    expect(screen.getByText('New Location')).toBeInTheDocument();
    expect(screen.queryByText('Koramangala')).not.toBeInTheDocument();
  });
});
