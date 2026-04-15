import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from './Dashboard';
import { complaintsAPI, riskAPI, weatherAPI, trafficAPI } from '../services/api';

// Mock the API services
jest.mock('../services/api', () => ({
  complaintsAPI: {
    getAllComplaints: jest.fn(),
  },
  riskAPI: {
    getRiskHotspots: jest.fn(),
  },
  weatherAPI: {
    getWeather: jest.fn(),
  },
  trafficAPI: {
    getTraffic: jest.fn(),
  },
}));

describe('Dashboard Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  test('renders dashboard with loading state initially', () => {
    // Mock API responses with pending promises
    complaintsAPI.getAllComplaints.mockReturnValue(new Promise(() => {}));
    riskAPI.getRiskHotspots.mockReturnValue(new Promise(() => {}));
    weatherAPI.getWeather.mockReturnValue(new Promise(() => {}));
    trafficAPI.getTraffic.mockReturnValue(new Promise(() => {}));

    render(<Dashboard />);
    
    expect(screen.getByText(/Loading dashboard/i)).toBeInTheDocument();
  });

  test('renders dashboard sections after data loads', async () => {
    // Mock successful API responses
    complaintsAPI.getAllComplaints.mockResolvedValue({
      data: [
        {
          complaint_id: '1',
          location: 'Koramangala',
          category: 'pothole',
          description: 'Test complaint',
          timestamp: '2024-01-01T10:00:00',
          coordinates: [12.9352, 77.6245],
        },
      ],
    });

    riskAPI.getRiskHotspots.mockResolvedValue({
      data: [
        {
          zone_id: 'zone1',
          center_coordinates: [12.9352, 77.6245],
          risk_score: 75,
          risk_level: 'high',
          complaint_count: 5,
        },
      ],
    });

    weatherAPI.getWeather.mockResolvedValue({
      data: {
        temperature_celsius: 28,
        humidity_percent: 65,
        precipitation_mm_per_hour: 0,
        wind_speed_kmh: 10,
        high_rainfall_flag: false,
      },
    });

    trafficAPI.getTraffic.mockResolvedValue({
      data: [
        {
          location: 'Koramangala',
          congestion_level: 'medium',
          congestion_score: 5,
        },
      ],
    });

    render(<Dashboard />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/UrbanGuard AI Dashboard/i)).toBeInTheDocument();
    });

    // Check that all sections are rendered
    expect(screen.getByText(/Risk Map/i)).toBeInTheDocument();
    expect(screen.getByText(/Recent Complaints/i)).toBeInTheDocument();
    expect(screen.getByText(/Weather Conditions/i)).toBeInTheDocument();
    expect(screen.getByText(/Traffic Status/i)).toBeInTheDocument();
    expect(screen.getByText(/Trend Analysis/i)).toBeInTheDocument();
  });

  test('displays error message when API calls fail', async () => {
    // Mock API failures
    complaintsAPI.getAllComplaints.mockRejectedValue(new Error('API Error'));
    riskAPI.getRiskHotspots.mockRejectedValue(new Error('API Error'));
    weatherAPI.getWeather.mockRejectedValue(new Error('API Error'));
    trafficAPI.getTraffic.mockRejectedValue(new Error('API Error'));

    render(<Dashboard />);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard data/i)).toBeInTheDocument();
    });
  });

  test('fetches dashboard data on mount', async () => {
    // Mock successful API responses
    complaintsAPI.getAllComplaints.mockResolvedValue({ data: [] });
    riskAPI.getRiskHotspots.mockResolvedValue({ data: [] });
    weatherAPI.getWeather.mockResolvedValue({ data: {} });
    trafficAPI.getTraffic.mockResolvedValue({ data: [] });

    render(<Dashboard />);

    await waitFor(() => {
      expect(complaintsAPI.getAllComplaints).toHaveBeenCalledTimes(1);
      expect(riskAPI.getRiskHotspots).toHaveBeenCalledTimes(1);
      expect(weatherAPI.getWeather).toHaveBeenCalledTimes(1);
      expect(trafficAPI.getTraffic).toHaveBeenCalledTimes(1);
    });
  });

  test('displays last update timestamp', async () => {
    // Mock successful API responses
    complaintsAPI.getAllComplaints.mockResolvedValue({ data: [] });
    riskAPI.getRiskHotspots.mockResolvedValue({ data: [] });
    weatherAPI.getWeather.mockResolvedValue({ data: {} });
    trafficAPI.getTraffic.mockResolvedValue({ data: [] });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/i)).toBeInTheDocument();
    });
  });
});
