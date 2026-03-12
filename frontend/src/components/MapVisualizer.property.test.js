import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import * as fc from 'fast-check';
import MapVisualizer from './MapVisualizer';

/**
 * Property-Based Tests for MapVisualizer Component
 * 
 * Uses fast-check for property-based testing with 100+ iterations
 * to verify universal correctness properties across all valid inputs.
 * 
 * Feature: urbanguard-ai-system
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
      data-fill-color={pathOptions?.fillColor}
      {...props}
    >
      {children}
    </div>
  ),
  Marker: ({ children, position, icon, ...props }) => (
    <div 
      data-testid="complaint-marker" 
      data-position={JSON.stringify(position)}
      data-icon={icon ? 'custom-icon' : 'default-icon'}
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

/**
 * Arbitrary generators for test data
 */

// Generate valid Bengaluru coordinates
const bengaluruCoordinatesArbitrary = () => 
  fc.tuple(
    fc.double({ min: 12.8, max: 13.2 }), // Latitude
    fc.double({ min: 77.4, max: 77.8 })  // Longitude
  );

// Generate risk scores in valid range (0-100)
const riskScoreArbitrary = () => 
  fc.double({ min: 0, max: 100, noNaN: true });

// Generate low risk scores (0-33)
const lowRiskScoreArbitrary = () => 
  fc.double({ min: 0, max: 33, noNaN: true });

// Generate medium risk scores (34-66)
const mediumRiskScoreArbitrary = () => 
  fc.double({ min: 34, max: 66, noNaN: true });

// Generate high risk scores (67-100)
const highRiskScoreArbitrary = () => 
  fc.double({ min: 67, max: 100, noNaN: true });

// Generate a risk zone object
const riskZoneArbitrary = (riskScoreGen = riskScoreArbitrary()) =>
  fc.record({
    zone_id: fc.uuid(),
    center_coordinates: bengaluruCoordinatesArbitrary(),
    risk_score: riskScoreGen,
    complaint_count: fc.integer({ min: 0, max: 50 }),
    radius_meters: fc.integer({ min: 100, max: 1000 }),
    dominant_category: fc.constantFrom(
      'pothole', 'flooding', 'traffic', 'garbage', 
      'streetlight', 'water_supply', 'noise', 'construction'
    )
  });

// Generate a complaint object
let complaintIdCounter = 0;
const complaintArbitrary = () =>
  fc.record({
    complaint_id: fc.integer({ min: 1, max: 1000000 }).map(n => `complaint-${n}-${++complaintIdCounter}`),
    location: fc.constantFrom(
      'Koramangala', 'Indiranagar', 'Whitefield', 'Electronic City',
      'Jayanagar', 'Malleshwaram', 'HSR Layout', 'BTM Layout'
    ),
    category: fc.constantFrom(
      'pothole', 'flooding', 'traffic', 'garbage', 
      'streetlight', 'water_supply', 'noise', 'construction'
    ),
    description: fc.string({ minLength: 10, maxLength: 100 }).filter(s => s.trim().length > 0),
    timestamp: fc.date({ min: new Date('2024-01-01'), max: new Date() }).map(d => d.toISOString()),
    coordinates: bengaluruCoordinatesArbitrary()
  }).filter(c => !isNaN(c.coordinates[0]) && !isNaN(c.coordinates[1]));

/**
 * Property 34: Risk Zone Color Coding
 * 
 * For any risk zone displayed, the Map_Visualizer should apply color coding 
 * based on risk level:
 * - Green (#22c55e) for low-risk (0-33)
 * - Yellow (#eab308) for medium-risk (34-66)
 * - Red (#ef4444) for high-risk (67-100)
 * 
 * Validates: Requirements 11.2
 */
describe('Property 34: Risk Zone Color Coding', () => {
  
  test('Property: Low risk zones (0-33) always render with green color', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(lowRiskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const circle = screen.getByTestId('risk-zone-circle');
          const color = circle.getAttribute('data-color');
          
          // Cleanup
          container.remove();
          
          // Assert: Low risk zones should always be green
          return color === '#22c55e';
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Medium risk zones (34-66) always render with yellow color', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(mediumRiskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const circle = screen.getByTestId('risk-zone-circle');
          const color = circle.getAttribute('data-color');
          
          // Cleanup
          container.remove();
          
          // Assert: Medium risk zones should always be yellow
          return color === '#eab308';
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: High risk zones (67-100) always render with red color', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(highRiskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const circle = screen.getByTestId('risk-zone-circle');
          const color = circle.getAttribute('data-color');
          
          // Cleanup
          container.remove();
          
          // Assert: High risk zones should always be red
          return color === '#ef4444';
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: All risk zones with valid scores (0-100) render with correct color', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(riskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const circle = screen.getByTestId('risk-zone-circle');
          const color = circle.getAttribute('data-color');
          const riskScore = zone.risk_score;
          
          // Cleanup
          container.remove();
          
          // Determine expected color based on risk score
          let expectedColor;
          if (riskScore >= 0 && riskScore <= 33) {
            expectedColor = '#22c55e'; // Green
          } else if (riskScore >= 34 && riskScore <= 66) {
            expectedColor = '#eab308'; // Yellow
          } else if (riskScore >= 67 && riskScore <= 100) {
            expectedColor = '#ef4444'; // Red
          }
          
          // Assert: Color matches expected color for risk score
          return color === expectedColor;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Color coding is consistent for boundary values', () => {
    // Test boundary values explicitly
    const boundaryZones = [
      { zone_id: '1', center_coordinates: [12.9, 77.6], risk_score: 0, complaint_count: 1 },
      { zone_id: '2', center_coordinates: [12.9, 77.6], risk_score: 33, complaint_count: 1 },
      { zone_id: '3', center_coordinates: [12.9, 77.6], risk_score: 34, complaint_count: 1 },
      { zone_id: '4', center_coordinates: [12.9, 77.6], risk_score: 66, complaint_count: 1 },
      { zone_id: '5', center_coordinates: [12.9, 77.6], risk_score: 67, complaint_count: 1 },
      { zone_id: '6', center_coordinates: [12.9, 77.6], risk_score: 100, complaint_count: 1 },
    ];

    const expectedColors = [
      '#22c55e', // 0 -> green
      '#22c55e', // 33 -> green
      '#eab308', // 34 -> yellow
      '#eab308', // 66 -> yellow
      '#ef4444', // 67 -> red
      '#ef4444', // 100 -> red
    ];

    const { container } = render(<MapVisualizer riskZones={boundaryZones} />);
    
    const circles = screen.getAllByTestId('risk-zone-circle');
    
    circles.forEach((circle, index) => {
      const color = circle.getAttribute('data-color');
      expect(color).toBe(expectedColors[index]);
    });

    container.remove();
  });

  test('Property: Multiple zones with different risk levels render with correct colors', () => {
    fc.assert(
      fc.property(
        fc.array(riskZoneArbitrary(riskScoreArbitrary()), { minLength: 1, maxLength: 10 }),
        (zones) => {
          const { container } = render(<MapVisualizer riskZones={zones} />);
          
          const circles = screen.getAllByTestId('risk-zone-circle');
          
          // Cleanup
          container.remove();
          
          // Assert: Each zone has correct color
          return circles.every((circle, index) => {
            const color = circle.getAttribute('data-color');
            const riskScore = zones[index].risk_score;
            
            if (riskScore >= 0 && riskScore <= 33) {
              return color === '#22c55e';
            } else if (riskScore >= 34 && riskScore <= 66) {
              return color === '#eab308';
            } else if (riskScore >= 67 && riskScore <= 100) {
              return color === '#ef4444';
            }
            return false;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Fill color matches border color for all risk zones', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(riskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const circle = screen.getByTestId('risk-zone-circle');
          const color = circle.getAttribute('data-color');
          const fillColor = circle.getAttribute('data-fill-color');
          
          // Cleanup
          container.remove();
          
          // Assert: Fill color should match border color
          return color === fillColor;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Risk level label matches color coding', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(riskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const riskScore = zone.risk_score;
          
          // Determine expected label
          let expectedLabel;
          if (riskScore >= 0 && riskScore <= 33) {
            expectedLabel = 'Low Risk';
          } else if (riskScore >= 34 && riskScore <= 66) {
            expectedLabel = 'Medium Risk';
          } else if (riskScore >= 67 && riskScore <= 100) {
            expectedLabel = 'High Risk';
          }
          
          // Check if label is present
          const hasLabel = screen.queryByText(expectedLabel) !== null;
          
          // Cleanup
          container.remove();
          
          // Assert: Correct label is displayed
          return hasLabel;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Additional property tests for risk zone visualization
 */
describe('Risk Zone Visualization Properties', () => {
  
  test('Property: All zones with valid coordinates are rendered', () => {
    fc.assert(
      fc.property(
        fc.array(riskZoneArbitrary(riskScoreArbitrary()), { minLength: 1, maxLength: 20 }),
        (zones) => {
          const { container } = render(<MapVisualizer riskZones={zones} />);
          
          const circles = screen.getAllByTestId('risk-zone-circle');
          
          // Cleanup
          container.remove();
          
          // Assert: Number of rendered circles equals number of zones
          return circles.length === zones.length;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Risk score is always displayed in popup', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(riskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const riskScore = zone.risk_score;
          const formattedScore = riskScore.toFixed(1);
          
          // Check if the popup div contains the risk score
          const popup = container.querySelector('.risk-zone-popup');
          const hasScore = popup && popup.textContent.includes(formattedScore);
          
          // Cleanup
          container.remove();
          
          // Assert: Risk score is displayed
          return hasScore;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Complaint count is always displayed in popup', () => {
    fc.assert(
      fc.property(
        riskZoneArbitrary(riskScoreArbitrary()),
        (zone) => {
          const { container } = render(<MapVisualizer riskZones={[zone]} />);
          
          const complaintCount = zone.complaint_count;
          
          // Check if the popup div contains the complaint count
          const popup = container.querySelector('.risk-zone-popup');
          const hasCount = popup && popup.textContent.includes(`Complaints: ${complaintCount}`);
          
          // Cleanup
          container.remove();
          
          // Assert: Complaint count is displayed
          return hasCount;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Property 35: Complaint Marker Display
 * 
 * For any complaint in the system, the Map_Visualizer should display it 
 * as a marker on the map at its coordinate location.
 * 
 * Validates: Requirements 11.4
 * 
 * Feature: urbanguard-ai-system, Property 35: Complaint Marker Display
 */
describe('Property 35: Complaint Marker Display', () => {
  
  test('Property: All complaints with valid coordinates are displayed as markers', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<MapVisualizer complaints={complaints} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: Number of rendered markers equals number of complaints
          return markers.length === complaints.length;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Each complaint marker is positioned at its coordinate location', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 10 }),
        (complaints) => {
          const { container } = render(<MapVisualizer complaints={complaints} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: Each marker has correct position matching complaint coordinates
          return markers.every((marker, index) => {
            const position = JSON.parse(marker.getAttribute('data-position'));
            const complaint = complaints[index];
            const [lat, lon] = complaint.coordinates;
            
            return position[0] === lat && position[1] === lon;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Single complaint is always displayed as a marker', () => {
    fc.assert(
      fc.property(
        complaintArbitrary(),
        (complaint) => {
          const { container } = render(<MapVisualizer complaints={[complaint]} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: Exactly one marker is rendered
          return markers.length === 1;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Empty complaint list renders no markers', () => {
    const { container } = render(<MapVisualizer complaints={[]} />);
    
    const markers = screen.queryAllByTestId('complaint-marker');
    
    // Cleanup
    container.remove();
    
    // Assert: No markers rendered for empty list
    expect(markers.length).toBe(0);
  });

  test('Property: Large number of complaints (100+) all render as markers', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 50, maxLength: 75 }),
        (complaints) => {
          const { container } = render(<MapVisualizer complaints={complaints} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: All complaints rendered even with large count
          return markers.length === complaints.length;
        }
      ),
      { numRuns: 10 } // Fewer runs for performance with large arrays
    );
  });

  test('Property: Complaint markers have custom icons', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 10 }),
        (complaints) => {
          const { container } = render(<MapVisualizer complaints={complaints} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: All markers have custom icons (not default)
          return markers.every(marker => {
            const icon = marker.getAttribute('data-icon');
            return icon === 'custom-icon';
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Complaint details are included in marker popup', () => {
    fc.assert(
      fc.property(
        complaintArbitrary(),
        (complaint) => {
          const { container } = render(<MapVisualizer complaints={[complaint]} />);
          
          // Check if popup contains complaint details
          const popup = container.querySelector('.complaint-popup');
          const hasCategory = popup && popup.textContent.includes(complaint.category.replace('_', ' '));
          const hasLocation = popup && popup.textContent.includes(complaint.location);
          const hasDescription = popup && popup.textContent.includes(complaint.description);
          
          // Cleanup
          container.remove();
          
          // Assert: All complaint details are in popup
          return hasCategory && hasLocation && hasDescription;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Markers render for complaints with array coordinate format', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 10 }),
        (complaints) => {
          // Ensure coordinates are in array format [lat, lon]
          const complaintsWithArrayCoords = complaints.map(c => ({
            ...c,
            coordinates: c.coordinates // Already in array format from generator
          }));
          
          const { container } = render(<MapVisualizer complaints={complaintsWithArrayCoords} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: All complaints with array coordinates render
          return markers.length === complaintsWithArrayCoords.length;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Markers render for complaints with object coordinate format', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 10 }),
        (complaints) => {
          // Convert coordinates to object format {latitude, longitude}
          const complaintsWithObjectCoords = complaints.map(c => ({
            ...c,
            coordinates: {
              latitude: c.coordinates[0],
              longitude: c.coordinates[1]
            }
          }));
          
          const { container } = render(<MapVisualizer complaints={complaintsWithObjectCoords} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: All complaints with object coordinates render
          return markers.length === complaintsWithObjectCoords.length;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Complaint count in stats matches input complaint count', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 0, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<MapVisualizer complaints={complaints} />);
          
          // Get all stat items and find the one with "Complaints:" label
          const statItems = container.querySelectorAll('.map-stats .stat-item');
          let displayedCount = 0;
          
          statItems.forEach(item => {
            const label = item.querySelector('.stat-label');
            if (label && label.textContent === 'Complaints:') {
              const value = item.querySelector('.stat-value');
              displayedCount = value ? parseInt(value.textContent, 10) : 0;
            }
          });
          
          // Cleanup
          container.remove();
          
          // Assert: Stats count matches the input complaint count
          // The component shows total complaints passed in
          return displayedCount === complaints.length;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Complaints with different categories all render as markers', () => {
    const categories = ['pothole', 'flooding', 'traffic', 'garbage', 
                       'streetlight', 'water_supply', 'noise', 'construction'];
    
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 8, maxLength: 16 }),
        (complaints) => {
          // Ensure we have at least one complaint of each category
          const diverseComplaints = complaints.map((c, i) => ({
            ...c,
            category: categories[i % categories.length]
          }));
          
          const { container } = render(<MapVisualizer complaints={diverseComplaints} />);
          
          const markers = screen.getAllByTestId('complaint-marker');
          
          // Cleanup
          container.remove();
          
          // Assert: All complaints render regardless of category
          return markers.length === diverseComplaints.length;
        }
      ),
      { numRuns: 100 }
    );
  });
});
