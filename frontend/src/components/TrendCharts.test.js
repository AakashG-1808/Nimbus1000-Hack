import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TrendCharts from './TrendCharts';

/**
 * Unit Tests for TrendCharts Component
 * 
 * Feature: urbanguard-ai-system
 * Task: 17.1 - Implement Chart.js visualizations
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

describe('TrendCharts Component', () => {
  const mockComplaints = [
    {
      complaint_id: '1',
      location: 'Koramangala',
      category: 'pothole',
      description: 'Large pothole',
      timestamp: new Date().toISOString(),
      coordinates: [12.9352, 77.6245],
    },
    {
      complaint_id: '2',
      location: 'Indiranagar',
      category: 'flooding',
      description: 'Water logging',
      timestamp: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
      coordinates: [12.9716, 77.6412],
    },
    {
      complaint_id: '3',
      location: 'Whitefield',
      category: 'traffic',
      description: 'Heavy traffic',
      timestamp: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
      coordinates: [12.9698, 77.7499],
    },
  ];

  const mockRiskZones = [
    {
      zone_id: 'zone-1',
      center_coordinates: [12.9352, 77.6245],
      risk_score: 85.5,
      complaint_count: 10,
    },
    {
      zone_id: 'zone-2',
      center_coordinates: [12.9716, 77.6412],
      risk_score: 72.3,
      complaint_count: 8,
    },
    {
      zone_id: 'zone-3',
      center_coordinates: [12.9698, 77.7499],
      risk_score: 68.1,
      complaint_count: 6,
    },
    {
      zone_id: 'zone-4',
      center_coordinates: [12.8456, 77.6603],
      risk_score: 55.0,
      complaint_count: 4,
    },
    {
      zone_id: 'zone-5',
      center_coordinates: [12.9250, 77.5838],
      risk_score: 45.2,
      complaint_count: 3,
    },
  ];

  test('renders TrendCharts component', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />);
    
    const charts = screen.getAllByTestId('line-chart');
    expect(charts).toHaveLength(2); // Two charts: complaint volume and risk score trends
  });

  test('renders complaint volume chart with correct title', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />);
    
    const charts = screen.getAllByTestId('line-chart');
    const complaintVolumeChart = charts[0];
    
    expect(complaintVolumeChart).toHaveAttribute(
      'data-chart-title',
      '7-Day Complaint Volume Trend'
    );
  });

  test('renders risk score trend chart with correct title', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />);
    
    const charts = screen.getAllByTestId('line-chart');
    const riskScoreChart = charts[1];
    
    expect(riskScoreChart).toHaveAttribute(
      'data-chart-title',
      'Top 5 High-Risk Zones - Risk Score Trends'
    );
  });

  test('displays placeholder when no complaint data available', () => {
    render(<TrendCharts complaints={[]} riskZones={mockRiskZones} />);
    
    expect(screen.getByText('No complaint data available')).toBeInTheDocument();
  });

  test('displays placeholder when no risk zone data available', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={[]} />);
    
    expect(screen.getByText('No risk zone data available')).toBeInTheDocument();
  });

  test('handles null complaints prop gracefully', () => {
    render(<TrendCharts complaints={null} riskZones={mockRiskZones} />);
    
    expect(screen.getByText('No complaint data available')).toBeInTheDocument();
  });

  test('handles null riskZones prop gracefully', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={null} />);
    
    expect(screen.getByText('No risk zone data available')).toBeInTheDocument();
  });

  test('complaint volume chart includes 7 days of data', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />);
    
    const charts = screen.getAllByTestId('line-chart');
    const complaintVolumeChart = charts[0];
    const labelsElement = complaintVolumeChart.querySelector('[data-testid="chart-labels"]');
    const labels = JSON.parse(labelsElement.textContent);
    
    expect(labels).toHaveLength(7); // 7 days
  });

  test('risk score chart shows top 5 zones', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />);
    
    const charts = screen.getAllByTestId('line-chart');
    const riskScoreChart = charts[1];
    const datasetsElement = riskScoreChart.querySelector('[data-testid="chart-datasets"]');
    const datasets = JSON.parse(datasetsElement.textContent);
    
    expect(datasets).toHaveLength(5); // Top 5 zones
  });

  test('risk score chart shows fewer zones when less than 5 available', () => {
    const fewZones = mockRiskZones.slice(0, 3);
    render(<TrendCharts complaints={mockComplaints} riskZones={fewZones} />);
    
    const charts = screen.getAllByTestId('line-chart');
    const riskScoreChart = charts[1];
    const datasetsElement = riskScoreChart.querySelector('[data-testid="chart-datasets"]');
    const datasets = JSON.parse(datasetsElement.textContent);
    
    expect(datasets).toHaveLength(3); // Only 3 zones available
  });

  test('component updates when complaints prop changes', () => {
    const { rerender } = render(
      <TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />
    );
    
    const newComplaints = [
      ...mockComplaints,
      {
        complaint_id: '4',
        location: 'BTM Layout',
        category: 'garbage',
        description: 'Garbage pile',
        timestamp: new Date().toISOString(),
        coordinates: [12.9166, 77.6101],
      },
    ];
    
    rerender(<TrendCharts complaints={newComplaints} riskZones={mockRiskZones} />);
    
    // Component should re-render without errors
    const charts = screen.getAllByTestId('line-chart');
    expect(charts).toHaveLength(2);
  });

  test('component updates when riskZones prop changes', () => {
    const { rerender } = render(
      <TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />
    );
    
    const newRiskZones = [
      ...mockRiskZones,
      {
        zone_id: 'zone-6',
        center_coordinates: [13.0039, 77.5727],
        risk_score: 90.0,
        complaint_count: 12,
      },
    ];
    
    rerender(<TrendCharts complaints={mockComplaints} riskZones={newRiskZones} />);
    
    // Component should re-render without errors
    const charts = screen.getAllByTestId('line-chart');
    expect(charts).toHaveLength(2);
  });

  test('renders both charts when both props are provided', () => {
    render(<TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />);
    
    const charts = screen.getAllByTestId('line-chart');
    expect(charts).toHaveLength(2);
  });

  test('chart containers have correct CSS classes', () => {
    const { container } = render(
      <TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />
    );
    
    const chartContainers = container.querySelectorAll('.chart-container');
    expect(chartContainers).toHaveLength(2);
  });

  test('trend charts container has correct CSS class', () => {
    const { container } = render(
      <TrendCharts complaints={mockComplaints} riskZones={mockRiskZones} />
    );
    
    const trendChartsContainer = container.querySelector('.trend-charts');
    expect(trendChartsContainer).toBeInTheDocument();
  });
});
