import React from 'react';
import './TrafficPanel.css';

/**
 * TrafficPanel Component
 * Displays traffic congestion levels for key Bengaluru locations
 * 
 * Props:
 * - trafficData: Array of {location, congestion_level, congestion_score}
 * 
 * Validates: Requirements 16.1, 16.2, 16.3, 16.4
 */
const TrafficPanel = ({ trafficData }) => {
  // Check if traffic data is null, undefined, or empty
  if (!trafficData || trafficData.length === 0) {
    return (
      <div className="traffic-panel">
        <div className="traffic-loading">Loading traffic data...</div>
      </div>
    );
  }

  /**
   * Get color class based on congestion level
   * GREEN for LOW, YELLOW for MEDIUM, RED for HIGH
   */
  const getCongestionColor = (level) => {
    const levelUpper = level?.toUpperCase();
    switch (levelUpper) {
      case 'LOW':
        return 'congestion-low';
      case 'MEDIUM':
        return 'congestion-medium';
      case 'HIGH':
        return 'congestion-high';
      default:
        return 'congestion-unknown';
    }
  };

  /**
   * Get icon based on congestion level
   */
  const getCongestionIcon = (level) => {
    const levelUpper = level?.toUpperCase();
    switch (levelUpper) {
      case 'LOW':
        return '🟢';
      case 'MEDIUM':
        return '🟡';
      case 'HIGH':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div className="traffic-panel">
      <div className="traffic-list">
        {trafficData.map((traffic, index) => (
          <div key={index} className="traffic-item">
            <div className="traffic-location">
              <span className="location-icon">📍</span>
              <span className="location-name">{traffic.location}</span>
            </div>
            <div className={`traffic-status ${getCongestionColor(traffic.congestion_level)}`}>
              <span className="status-icon">{getCongestionIcon(traffic.congestion_level)}</span>
              <span className="status-text">{traffic.congestion_level}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrafficPanel;
