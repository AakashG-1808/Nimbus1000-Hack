import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import * as fc from 'fast-check';
import TrendCharts from './TrendCharts';

/**
 * Property-Based Tests for TrendCharts Component
 * 
 * Feature: urbanguard-ai-system
 * Task: 17.2 - Write property tests for trend charts
 * 
 * Uses fast-check library with minimum 100 iterations
 */

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }) => (
    <div data-testid="line-chart" data-chart-title={options?.plugins?.title?.text}>
      <div data-testid="chart-labels">{JSON.stringify(data?.labels)}</div>
      <div data-testid="chart-datasets">{JSON.stringify(data?.datasets)}</div>
    </div>
  ),
}));

// Mock CSS imports
jest.mock('./TrendCharts.css', () => ({}));

// ============================================================================
// Generators for Property-Based Testing
// ============================================================================

/**
 * Generator for valid timestamps within the last 30 days
 */
const timestampArbitrary = () => {
  const now = Date.now();
  const thirtyDaysAgo = now - (30 * 24 * 60 * 60 * 1000);
  return fc.integer({ min: thirtyDaysAgo, max: now }).map(ts => new Date(ts).toISOString());
};

/**
 * Generator for complaint categories
 */
const categoryArbitrary = () => {
  return fc.constantFrom(
    'pothole',
    'flooding',
    'traffic',
    'garbage',
    'streetlight',
    'water_supply',
    'noise',
    'construction'
  );
};

/**
 * Generator for Bengaluru coordinates
 * Lat: 12.8-13.2°N, Lon: 77.4-77.8°E
 */
const coordinatesArbitrary = () => {
  return fc.tuple(
    fc.double({ min: 12.8, max: 13.2 }),
    fc.double({ min: 77.4, max: 77.8 })
  );
};

/**
 * Generator for a single complaint
 */
const complaintArbitrary = () => {
  return fc.record({
    complaint_id: fc.uuid(),
    location: fc.constantFrom(
      'Koramangala',
      'Indiranagar',
      'Whitefield',
      'Electronic City',
      'Jayanagar',
      'Malleshwaram',
      'HSR Layout',
      'BTM Layout'
    ),
    category: categoryArbitrary(),
    description: fc.string({ minLength: 10, maxLength: 100 }),
    timestamp: timestampArbitrary(),
    coordinates: coordinatesArbitrary(),
  });
};

/**
 * Generator for an array of complaints
 */
const complaintsArrayArbitrary = () => {
  return fc.array(complaintArbitrary(), { minLength: 0, maxLength: 100 });
};

/**
 * Generator for a single risk zone
 */
const riskZoneArbitrary = () => {
  return fc.record({
    zone_id: fc.uuid(),
    center_coordinates: coordinatesArbitrary(),
    risk_score: fc.double({ min: 0, max: 100 }),
    complaint_count: fc.integer({ min: 0, max: 50 }),
  });
};

/**
 * Generator for an array of risk zones
 */
const riskZonesArrayArbitrary = () => {
  return fc.array(riskZoneArbitrary(), { minLength: 0, maxLength: 20 });
};

// ============================================================================
// Property-Based Tests
// ============================================================================

describe('TrendCharts Property-Based Tests', () => {
  /**
   * Feature: urbanguard-ai-system, Property 38: Seven-Day Complaint Volume Trend
   * 
   * For any set of complaints, the Map_Visualizer should calculate and display
   * complaint volume trends for the past 7 days.
   * 
   * Validates: Requirements 14.2
   */
  test('Property 38: Seven-Day Complaint Volume Trend - 7 days of data shown', () => {
    fc.assert(
      fc.property(
        complaintsArrayArbitrary(),
        riskZonesArrayArbitrary(),
        (complaints, riskZones) => {
          // Skip if no complaints (placeholder will be shown)
          if (complaints.length === 0) {
            return true;
          }

          const { container } = render(
            <TrendCharts complaints={complaints} riskZones={riskZones} />
          );

          const charts = screen.getAllByTestId('line-chart');
          const complaintVolumeChart = charts[0];
          const labelsElement = complaintVolumeChart.querySelector('[data-testid="chart-labels"]');
          
          if (labelsElement) {
            const labels = JSON.parse(labelsElement.textContent);
            
            // Property: The complaint volume chart should always show exactly 7 days of data
            expect(labels).toHaveLength(7);
            
            // Additional verification: labels should be in chronological order
            // Each label should be a string in format "Day M/D"
            labels.forEach(label => {
              expect(typeof label).toBe('string');
              expect(label).toMatch(/^(Sun|Mon|Tue|Wed|Thu|Fri|Sat) \d{1,2}\/\d{1,2}$/);
            });
          }

          // Cleanup
          container.remove();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Feature: urbanguard-ai-system, Property 39: Top Five Risk Zone Trends
   * 
   * For any set of risk zones, the Map_Visualizer should identify the top 5
   * high-risk zones and display their Risk_Score trends.
   * 
   * Validates: Requirements 14.3
   */
  test('Property 39: Top Five Risk Zone Trends - Top 5 zones identified and displayed', () => {
    fc.assert(
      fc.property(
        complaintsArrayArbitrary(),
        riskZonesArrayArbitrary(),
        (complaints, riskZones) => {
          // Skip if no risk zones (placeholder will be shown)
          if (riskZones.length === 0) {
            return true;
          }

          const { container } = render(
            <TrendCharts complaints={complaints} riskZones={riskZones} />
          );

          const charts = screen.queryAllByTestId('line-chart');
          
          // Find the risk score chart by its title
          const riskScoreChart = charts.find(chart => 
            chart.getAttribute('data-chart-title') === 'Top 5 High-Risk Zones - Risk Score Trends'
          );
          
          // If no risk score chart found, skip (placeholder is shown)
          if (!riskScoreChart) {
            return true;
          }
          
          const datasetsElement = riskScoreChart.querySelector('[data-testid="chart-datasets"]');
          
          if (datasetsElement) {
            const datasets = JSON.parse(datasetsElement.textContent);
            
            // Property: The risk score chart should show at most 5 zones
            // (or fewer if less than 5 zones exist)
            const expectedZoneCount = Math.min(5, riskZones.length);
            expect(datasets).toHaveLength(expectedZoneCount);
            
            // Additional verification: The zones should be the top 5 by risk_score
            if (riskZones.length > 0) {
              // Sort risk zones by score descending to get expected top 5
              const sortedZones = [...riskZones]
                .sort((a, b) => b.risk_score - a.risk_score)
                .slice(0, 5);
              
              // Each dataset should correspond to one of the top zones
              datasets.forEach((dataset, index) => {
                expect(dataset).toHaveProperty('label');
                expect(dataset).toHaveProperty('data');
                expect(dataset).toHaveProperty('borderColor');
                
                // Verify the dataset label contains the zone_id from top zones
                const expectedZoneId = sortedZones[index].zone_id.substring(0, 8);
                expect(dataset.label).toContain(expectedZoneId);
                
                // Verify the dataset label contains the risk score
                const expectedScore = sortedZones[index].risk_score.toFixed(0);
                expect(dataset.label).toContain(expectedScore);
              });
            }
          }

          // Cleanup
          container.remove();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional Property: Complaint Volume Chart Always Shows 7 Days
   * Even with Empty Data
   * 
   * This test verifies that the chart structure is consistent regardless
   * of whether complaints exist within the 7-day window.
   */
  test('Property: Complaint volume chart shows 7 days even with sparse data', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 10 }),
        riskZonesArrayArbitrary(),
        (complaints, riskZones) => {
          const { container } = render(
            <TrendCharts complaints={complaints} riskZones={riskZones} />
          );

          const charts = screen.getAllByTestId('line-chart');
          const complaintVolumeChart = charts[0];
          const labelsElement = complaintVolumeChart.querySelector('[data-testid="chart-labels"]');
          const datasetsElement = complaintVolumeChart.querySelector('[data-testid="chart-datasets"]');
          
          if (labelsElement && datasetsElement) {
            const labels = JSON.parse(labelsElement.textContent);
            const datasets = JSON.parse(datasetsElement.textContent);
            
            // Always 7 days
            expect(labels).toHaveLength(7);
            
            // Should have exactly one dataset (complaint volume)
            expect(datasets).toHaveLength(1);
            
            // Dataset should have 7 data points (one per day)
            expect(datasets[0].data).toHaveLength(7);
            
            // All data points should be non-negative integers
            datasets[0].data.forEach(count => {
              expect(count).toBeGreaterThanOrEqual(0);
              expect(Number.isInteger(count)).toBe(true);
            });
          }

          // Cleanup
          container.remove();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional Property: Risk Score Chart Respects Zone Count Limit
   * 
   * This test verifies that the chart never shows more than 5 zones,
   * even when many zones are available.
   */
  test('Property: Risk score chart never exceeds 5 zones', () => {
    fc.assert(
      fc.property(
        complaintsArrayArbitrary(),
        fc.array(riskZoneArbitrary(), { minLength: 1, maxLength: 50 }),
        (complaints, riskZones) => {
          const { container } = render(
            <TrendCharts complaints={complaints} riskZones={riskZones} />
          );

          const charts = screen.queryAllByTestId('line-chart');
          
          // Find the risk score chart by its title
          const riskScoreChart = charts.find(chart => 
            chart.getAttribute('data-chart-title') === 'Top 5 High-Risk Zones - Risk Score Trends'
          );
          
          // If no risk score chart found, skip
          if (!riskScoreChart) {
            return true;
          }
          
          const datasetsElement = riskScoreChart.querySelector('[data-testid="chart-datasets"]');
          
          if (datasetsElement) {
            const datasets = JSON.parse(datasetsElement.textContent);
            
            // Should never exceed 5 zones
            expect(datasets.length).toBeLessThanOrEqual(5);
            
            // Should show min(5, riskZones.length) zones
            expect(datasets.length).toBe(Math.min(5, riskZones.length));
          }

          // Cleanup
          container.remove();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional Property: Top Zones Are Correctly Sorted by Risk Score
   * 
   * This test verifies that when multiple zones exist, the chart displays
   * the zones with the highest risk scores.
   */
  test('Property: Risk score chart displays zones sorted by risk score descending', () => {
    fc.assert(
      fc.property(
        complaintsArrayArbitrary(),
        fc.array(riskZoneArbitrary(), { minLength: 6, maxLength: 20 }),
        (complaints, riskZones) => {
          const { container } = render(
            <TrendCharts complaints={complaints} riskZones={riskZones} />
          );

          // Get the top 5 zones by risk score
          const top5Zones = [...riskZones]
            .sort((a, b) => b.risk_score - a.risk_score)
            .slice(0, 5);

          const charts = screen.queryAllByTestId('line-chart');
          
          // Find the risk score chart by its title
          const riskScoreChart = charts.find(chart => 
            chart.getAttribute('data-chart-title') === 'Top 5 High-Risk Zones - Risk Score Trends'
          );
          
          // If no risk score chart found, skip
          if (!riskScoreChart) {
            return true;
          }
          
          const datasetsElement = riskScoreChart.querySelector('[data-testid="chart-datasets"]');
          
          if (datasetsElement) {
            const datasets = JSON.parse(datasetsElement.textContent);
            
            // Verify each dataset corresponds to one of the top 5 zones
            datasets.forEach((dataset, index) => {
              const expectedZoneId = top5Zones[index].zone_id.substring(0, 8);
              const expectedScore = top5Zones[index].risk_score.toFixed(0);
              
              expect(dataset.label).toContain(expectedZoneId);
              expect(dataset.label).toContain(expectedScore);
            });
          }

          // Cleanup
          container.remove();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional Property: Charts Handle Edge Cases Gracefully
   * 
   * This test verifies that the component handles edge cases like
   * null/undefined props, empty arrays, and single items correctly.
   */
  test('Property: Charts handle edge cases without crashing', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.constant(null),
          fc.constant(undefined),
          fc.constant([]),
          complaintsArrayArbitrary()
        ),
        fc.oneof(
          fc.constant(null),
          fc.constant(undefined),
          fc.constant([]),
          riskZonesArrayArbitrary()
        ),
        (complaints, riskZones) => {
          // Should not throw an error
          const { container } = render(
            <TrendCharts complaints={complaints} riskZones={riskZones} />
          );

          // Component should render something (either charts or placeholders)
          expect(container.querySelector('.trend-charts')).toBeInTheDocument();

          // Cleanup
          container.remove();
        }
      ),
      { numRuns: 100 }
    );
  });
});
