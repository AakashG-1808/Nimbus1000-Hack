import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MapVisualizer from './MapVisualizer';

/**
 * Unit tests for MapVisualizer component
 * 
 * Tests basic rendering and prop handling
 */

// Mock react-leaflet components
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children, ...props }) => (
    <div data-testid="map-container" {...props}>
      {children}
    </div>
  ),
  TileLayer: () => <div data-testid="tile-layer" />,
  Circle: ({ children, center, pathOptions, ...props }) => (
    <div 
      data-testid="risk-zone-circle" 
      data-center={JSON.stringify(center)}
      data-color={pathOptions?.color}
      {...props}
    >
      {children}
    </div>
  ),
  Marker: ({ children, position, ...props }) => (
    <div 
      data-testid="complaint-marker" 
      data-position={JSON.stringify(position)}
      {...props}
    >
      {children}
    </div>
  ),
  Popup: ({ children }) => (
    <div data-testid="popup">
      {children}
    </div>
  ),
  useMap: () => ({
    setView: jest.fn(),
  }),
}));

// Mock CSS imports
jest.mock('leaflet/dist/leaflet.css', () => ({}));
jest.mock('./MapVisualizer.css', () => ({}));

describe('MapVisualizer Component', () => {
  test('renders without crashing', () => {
    render(<MapVisualizer />);
    // Map should render with default props
    const mapElement = document.querySelector('.map-visualizer');
    expect(mapElement).toBeInTheDocument();
  });

  test('displays correct stats with empty data', () => {
    render(<MapVisualizer riskZones={[]} complaints={[]} />);
    
    // Check stats display
    expect(screen.getByText('Risk Zones:')).toBeInTheDocument();
    expect(screen.getByText('Complaints:')).toBeInTheDocument();
    // Both stats should show 0
    const zeroValues = screen.getAllByText('0');
    expect(zeroValues).toHaveLength(2);
  });

  test('displays correct stats with data', () => {
    const mockRiskZones = [
      { zone_id: '1', risk_score: 45 },
      { zone_id: '2', risk_score: 75 }
    ];
    const mockComplaints = [
      { complaint_id: '1', location: 'Koramangala' },
      { complaint_id: '2', location: 'Indiranagar' },
      { complaint_id: '3', location: 'Whitefield' }
    ];

    render(
      <MapVisualizer 
        riskZones={mockRiskZones} 
        complaints={mockComplaints} 
      />
    );
    
    // Check that stats show correct counts
    expect(screen.getByText('2')).toBeInTheDocument(); // 2 risk zones
    expect(screen.getByText('3')).toBeInTheDocument(); // 3 complaints
  });

  test('renders map legend', () => {
    render(<MapVisualizer />);
    
    // Check legend is present
    expect(screen.getByText('Map Legend')).toBeInTheDocument();
    expect(screen.getByText('Low Risk (0-33)')).toBeInTheDocument();
    expect(screen.getByText('Medium Risk (34-66)')).toBeInTheDocument();
    expect(screen.getByText('High Risk (67-100)')).toBeInTheDocument();
  });

  test('renders map container', () => {
    render(<MapVisualizer />);
    
    // Check that map container is rendered
    const mapContainer = screen.getByTestId('map-container');
    expect(mapContainer).toBeInTheDocument();
  });

  test('accepts updateInterval prop', () => {
    const customInterval = 60000;
    render(<MapVisualizer updateInterval={customInterval} />);
    
    // Component should render without errors
    const mapElement = document.querySelector('.map-visualizer');
    expect(mapElement).toBeInTheDocument();
  });
});


describe('MapVisualizer Risk Zone Visualization', () => {
  test('renders risk zones as circles', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 45,
        complaint_count: 8,
        radius_meters: 500
      },
      {
        zone_id: 'zone-2',
        center_coordinates: [12.9716, 77.6412],
        risk_score: 75,
        complaint_count: 12,
        radius_meters: 500
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    // Check that circles are rendered for each risk zone
    const circles = screen.getAllByTestId('risk-zone-circle');
    expect(circles).toHaveLength(2);
  });

  test('applies correct color coding for low risk zones (0-33)', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-low',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 25,
        complaint_count: 3
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    const circle = screen.getByTestId('risk-zone-circle');
    expect(circle).toHaveAttribute('data-color', '#22c55e'); // Green
  });

  test('applies correct color coding for medium risk zones (34-66)', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-medium',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 50,
        complaint_count: 7
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    const circle = screen.getByTestId('risk-zone-circle');
    expect(circle).toHaveAttribute('data-color', '#eab308'); // Yellow
  });

  test('applies correct color coding for high risk zones (67-100)', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-high',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 85,
        complaint_count: 15
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    const circle = screen.getByTestId('risk-zone-circle');
    expect(circle).toHaveAttribute('data-color', '#ef4444'); // Red
  });

  test('displays risk score in popup', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 67.5,
        complaint_count: 10
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    // Check that risk score is displayed
    expect(screen.getByText(/67\.5/)).toBeInTheDocument();
  });

  test('displays complaint count in popup', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 45,
        complaint_count: 8
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    // Check that complaint count is displayed
    expect(screen.getByText(/8/)).toBeInTheDocument();
  });

  test('displays risk level label in popup', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 75,
        complaint_count: 12
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    // Check that risk level is displayed
    expect(screen.getByText('High Risk')).toBeInTheDocument();
  });

  test('displays dominant category when available', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 55,
        complaint_count: 9,
        dominant_category: 'pothole'
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    // Check that dominant category is displayed
    expect(screen.getByText(/pothole/)).toBeInTheDocument();
  });

  test('handles zones with invalid coordinates gracefully', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-invalid',
        center_coordinates: null,
        risk_score: 45,
        complaint_count: 5
      },
      {
        zone_id: 'zone-valid',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 55,
        complaint_count: 8
      }
    ];

    // Should not crash
    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    // Only valid zone should be rendered
    const circles = screen.getAllByTestId('risk-zone-circle');
    expect(circles).toHaveLength(1);
  });

  test('uses default radius when not specified', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 45,
        complaint_count: 5
        // No radius_meters specified
      }
    ];

    // Should render without errors
    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    const circle = screen.getByTestId('risk-zone-circle');
    expect(circle).toBeInTheDocument();
  });

  test('handles alternative coordinate field names', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        coordinates: [12.9352, 77.6245], // Using 'coordinates' instead of 'center_coordinates'
        risk_score: 45,
        complaint_count: 5
      }
    ];

    render(<MapVisualizer riskZones={mockRiskZones} />);
    
    const circle = screen.getByTestId('risk-zone-circle');
    expect(circle).toBeInTheDocument();
  });
});


describe('MapVisualizer Complaint Marker Display', () => {
  test('renders complaint markers for all complaints', () => {
    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Large pothole on main road',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      },
      {
        complaint_id: 'c2',
        location: 'Indiranagar',
        category: 'flooding',
        description: 'Water logging issue',
        timestamp: '2024-01-15T11:00:00Z',
        coordinates: { latitude: 12.9716, longitude: 77.6412 }
      },
      {
        complaint_id: 'c3',
        location: 'Whitefield',
        category: 'traffic',
        description: 'Heavy traffic congestion',
        timestamp: '2024-01-15T12:00:00Z',
        coordinates: { latitude: 12.9698, longitude: 77.7499 }
      }
    ];

    render(<MapVisualizer complaints={mockComplaints} />);
    
    // Check that markers are rendered for each complaint
    const markers = screen.getAllByTestId('complaint-marker');
    expect(markers).toHaveLength(3);
  });

  test('displays complaint details in marker popup', () => {
    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Large pothole on main road',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      }
    ];

    render(<MapVisualizer complaints={mockComplaints} />);
    
    // Check that complaint details are displayed (text-transform: capitalize is CSS only)
    expect(screen.getByText('pothole')).toBeInTheDocument();
    expect(screen.getByText('Koramangala')).toBeInTheDocument();
    expect(screen.getByText('Large pothole on main road')).toBeInTheDocument();
  });

  test('handles complaints with array coordinate format', () => {
    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Test complaint',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: [12.9352, 77.6245] // Array format
      }
    ];

    render(<MapVisualizer complaints={mockComplaints} />);
    
    const markers = screen.getAllByTestId('complaint-marker');
    expect(markers).toHaveLength(1);
  });

  test('handles complaints with object coordinate format', () => {
    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Test complaint',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 } // Object format
      }
    ];

    render(<MapVisualizer complaints={mockComplaints} />);
    
    const markers = screen.getAllByTestId('complaint-marker');
    expect(markers).toHaveLength(1);
  });

  test('skips complaints with invalid coordinates', () => {
    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Valid complaint',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      },
      {
        complaint_id: 'c2',
        location: 'Indiranagar',
        category: 'flooding',
        description: 'Invalid coordinates',
        timestamp: '2024-01-15T11:00:00Z',
        coordinates: null // Invalid
      },
      {
        complaint_id: 'c3',
        location: 'Whitefield',
        category: 'traffic',
        description: 'Missing coordinates',
        timestamp: '2024-01-15T12:00:00Z',
        coordinates: {} // Invalid
      }
    ];

    // Should not crash
    render(<MapVisualizer complaints={mockComplaints} />);
    
    // Only valid complaint should be rendered
    const markers = screen.getAllByTestId('complaint-marker');
    expect(markers).toHaveLength(1);
  });

  test('displays different complaint categories', () => {
    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Pothole issue',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      },
      {
        complaint_id: 'c2',
        location: 'Indiranagar',
        category: 'water_supply',
        description: 'Water supply issue',
        timestamp: '2024-01-15T11:00:00Z',
        coordinates: { latitude: 12.9716, longitude: 77.6412 }
      }
    ];

    render(<MapVisualizer complaints={mockComplaints} />);
    
    // Check that different categories are displayed (text-transform: capitalize is CSS only)
    expect(screen.getByText('pothole')).toBeInTheDocument();
    expect(screen.getByText('water supply')).toBeInTheDocument();
  });

  test('formats timestamp for display', () => {
    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Test complaint',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      }
    ];

    render(<MapVisualizer complaints={mockComplaints} />);
    
    // Check that timestamp is formatted (should contain date elements)
    expect(screen.getByText(/Jan|15|2024/)).toBeInTheDocument();
  });

  test('displays complaint ID in popup', () => {
    const mockComplaints = [
      {
        complaint_id: 'abc123def456',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Test complaint',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      }
    ];

    render(<MapVisualizer complaints={mockComplaints} />);
    
    // Check that complaint ID is displayed (truncated)
    expect(screen.getByText(/abc123de/)).toBeInTheDocument();
  });

  test('renders both risk zones and complaint markers together', () => {
    const mockRiskZones = [
      {
        zone_id: 'zone-1',
        center_coordinates: [12.9352, 77.6245],
        risk_score: 45,
        complaint_count: 8
      }
    ];

    const mockComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Test complaint',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      },
      {
        complaint_id: 'c2',
        location: 'Indiranagar',
        category: 'flooding',
        description: 'Another complaint',
        timestamp: '2024-01-15T11:00:00Z',
        coordinates: { latitude: 12.9716, longitude: 77.6412 }
      }
    ];

    render(
      <MapVisualizer 
        riskZones={mockRiskZones} 
        complaints={mockComplaints} 
      />
    );
    
    // Check that both risk zones and markers are rendered
    const circles = screen.getAllByTestId('risk-zone-circle');
    expect(circles).toHaveLength(1);
    
    const markers = screen.getAllByTestId('complaint-marker');
    expect(markers).toHaveLength(2);
  });

  test('updates markers when complaints data changes', () => {
    const initialComplaints = [
      {
        complaint_id: 'c1',
        location: 'Koramangala',
        category: 'pothole',
        description: 'Test complaint',
        timestamp: '2024-01-15T10:30:00Z',
        coordinates: { latitude: 12.9352, longitude: 77.6245 }
      }
    ];

    const { rerender } = render(<MapVisualizer complaints={initialComplaints} />);
    
    // Initially 1 marker
    let markers = screen.getAllByTestId('complaint-marker');
    expect(markers).toHaveLength(1);

    // Update with more complaints
    const updatedComplaints = [
      ...initialComplaints,
      {
        complaint_id: 'c2',
        location: 'Indiranagar',
        category: 'flooding',
        description: 'New complaint',
        timestamp: '2024-01-15T11:00:00Z',
        coordinates: { latitude: 12.9716, longitude: 77.6412 }
      }
    ];

    rerender(<MapVisualizer complaints={updatedComplaints} />);
    
    // Now 2 markers
    markers = screen.getAllByTestId('complaint-marker');
    expect(markers).toHaveLength(2);
  });
});
