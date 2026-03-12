import React, { useState, useEffect, useCallback } from 'react';
import { complaintsAPI, riskAPI, weatherAPI, trafficAPI } from '../services/api';
import MapVisualizer from './MapVisualizer';
import ComplaintFeed from './ComplaintFeed';
import TrendCharts from './TrendCharts';
import WeatherPanel from './WeatherPanel';
import TrafficPanel from './TrafficPanel';
import './Dashboard.css';

/**
 * Main Dashboard component with grid layout
 * Implements 30-second polling for real-time updates
 * 
 * Validates: Requirements 12.1, 12.2
 */
const Dashboard = () => {
  // State for all dashboard data
  const [complaints, setComplaints] = useState([]);
  const [riskZones, setRiskZones] = useState([]);
  const [weather, setWeather] = useState(null);
  const [traffic, setTraffic] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setError(null);
      
      // Fetch all data in parallel
      const [complaintsRes, riskRes, weatherRes, trafficRes] = await Promise.all([
        complaintsAPI.getAllComplaints(),
        riskAPI.getRiskHotspots(),
        weatherAPI.getWeather(),
        trafficAPI.getTraffic(),
      ]);

      setComplaints(complaintsRes.data);
      setRiskZones(riskRes.data);
      setWeather(weatherRes.data);
      setTraffic(trafficRes.data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Retrying...');
      setLoading(false);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Set up 30-second polling for real-time updates
  useEffect(() => {
    const pollInterval = setInterval(() => {
      fetchDashboardData();
    }, 30000); // 30 seconds

    // Cleanup interval on unmount
    return () => clearInterval(pollInterval);
  }, [fetchDashboardData]);

  if (loading && !lastUpdate) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>UrbanGuard AI Dashboard</h1>
        {lastUpdate && (
          <div className="last-update">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
        )}
        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}
      </div>

      <div className="dashboard-grid">
        {/* Map Section - Main visualization area */}
        <section className="dashboard-section map-section">
          <div className="section-header">
            <h2>Risk Map</h2>
            <span className="section-badge">{riskZones.length} zones</span>
          </div>
          <div className="section-content">
            {/* MapVisualizer component - Task 15.1 */}
            <MapVisualizer 
              riskZones={riskZones} 
              complaints={complaints}
              updateInterval={30000}
            />
          </div>
        </section>

        {/* Complaint Feed Section */}
        <section className="dashboard-section feed-section">
          <div className="section-header">
            <h2>Recent Complaints</h2>
            <span className="section-badge">{Math.min(20, complaints.length)}</span>
          </div>
          <div className="section-content">
            <ComplaintFeed complaints={complaints} />
          </div>
        </section>

        {/* Weather Panel Section */}
        <section className="dashboard-section weather-section">
          <div className="section-header">
            <h2>Weather Conditions</h2>
          </div>
          <div className="section-content">
            {/* WeatherPanel component - Task 18.1 */}
            <WeatherPanel weather={weather} />
          </div>
        </section>

        {/* Traffic Panel Section */}
        <section className="dashboard-section traffic-section">
          <div className="section-header">
            <h2>Traffic Status</h2>
            <span className="section-badge">{traffic.length} locations</span>
          </div>
          <div className="section-content">
            {/* TrafficPanel component - Task 19.1 */}
            <TrafficPanel trafficData={traffic} />
          </div>
        </section>

        {/* Trend Charts Section */}
        <section className="dashboard-section charts-section">
          <div className="section-header">
            <h2>Trend Analysis</h2>
          </div>
          <div className="section-content">
            {/* TrendCharts component - Task 17.1 */}
            <TrendCharts complaints={complaints} riskZones={riskZones} />
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
