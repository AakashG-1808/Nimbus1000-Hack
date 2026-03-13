import React, { useEffect, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapVisualizer.css';

/**
 * MapVisualizer Component
 * 
 * Renders an interactive Leaflet.js map centered on Bengaluru
 * with risk zones and complaint markers.
 * 
 * Validates: Requirements 11.1
 * 
 * Features:
 * - Leaflet.js map centered on Bengaluru (12.9716, 77.5946)
 * - OpenStreetMap tiles
 * - Configurable zoom levels (10-18)
 * - Responsive container sizing
 */

// Bengaluru center coordinates
const BENGALURU_CENTER = [12.9716, 77.5946];
const DEFAULT_ZOOM = 12;
const MIN_ZOOM = 10;
const MAX_ZOOM = 18;
const CLUSTER_GRID_SIZE = 0.003;

/**
 * MapController component to handle map updates
 * This component uses the useMap hook to access the map instance
 */
const MapController = ({ center, zoom }) => {
  const map = useMap();
  
  useEffect(() => {
    if (center && zoom) {
      map.setView(center, zoom);
    }
  }, [map, center, zoom]);
  
  return null;
};

/**
 * Get color for risk zone based on risk score
 * Green: 0-33 (low risk)
 * Yellow: 34-66 (medium risk)
 * Red: 67-100 (high risk)
 * 
 * Validates: Requirements 11.2
 */
const getRiskZoneColor = (riskScore) => {
  if (riskScore >= 0 && riskScore <= 33) {
    return '#22c55e'; // Green - low risk
  } else if (riskScore >= 34 && riskScore <= 66) {
    return '#eab308'; // Yellow - medium risk
  } else if (riskScore >= 67 && riskScore <= 100) {
    return '#ef4444'; // Red - high risk
  }
  return '#9ca3af'; // Gray - default/unknown
};

/**
 * Get risk level label based on risk score
 */
const getRiskLevelLabel = (riskScore) => {
  if (riskScore >= 0 && riskScore <= 33) {
    return 'Low Risk';
  } else if (riskScore >= 34 && riskScore <= 66) {
    return 'Medium Risk';
  } else if (riskScore >= 67 && riskScore <= 100) {
    return 'High Risk';
  }
  return 'Unknown';
};

/**
 * Create custom marker icon for complaint categories
 * Different colors for different complaint types
 * 
 * Validates: Requirements 11.4
 */
const createComplaintIcon = (category) => {
  // Color mapping for different complaint categories
  const categoryColors = {
    pothole: '#8b5cf6',      // Purple
    flooding: '#3b82f6',     // Blue
    traffic: '#f59e0b',      // Amber
    garbage: '#84cc16',      // Lime
    streetlight: '#fbbf24',  // Yellow
    water_supply: '#06b6d4', // Cyan
    noise: '#ec4899',        // Pink
    construction: '#f97316', // Orange
  };

  const color = categoryColors[category] || '#6b7280'; // Gray default

  // Create SVG marker icon
  const svgIcon = `
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="12" fill="${color}" stroke="white" stroke-width="2" opacity="0.9"/>
      <circle cx="16" cy="16" r="4" fill="white"/>
    </svg>
  `;

  return L.divIcon({
    html: svgIcon,
    className: 'complaint-marker-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

const createClusterIcon = (count) => {
  const size = count >= 50 ? 48 : count >= 20 ? 42 : 36;
  const fontSize = count >= 50 ? 14 : 12;
  const html = `
    <div class="cluster-marker" style="width:${size}px;height:${size}px;">
      <div class="cluster-inner">
        <span style="font-size:${fontSize}px;">${count}</span>
      </div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'cluster-marker-icon',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2]
  });
};

/**
 * Format timestamp for display
 */
const formatTimestamp = (timestamp) => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return timestamp;
  }
};

/**
 * MapVisualizer Component
 * 
 * @param {Object} props - Component props
 * @param {Array} props.riskZones - Array of risk zone objects
 * @param {Array} props.complaints - Array of complaint objects
 * @param {number} props.updateInterval - Update interval in milliseconds (default: 30000)
 */
const MapVisualizer = ({
  riskZones = [],
  complaints = [],
  updateInterval = 30000,
  loading = false,
  error = null,
  enableClustering = true
}) => {
  const mapRef = useRef(null);

  const normalizedComplaints = useMemo(() => {
    return complaints
      .map((complaint) => {
        const coords = complaint.coordinates;
        if (!coords || (!coords.latitude && !coords[0])) {
          return null;
        }
        const lat = coords.latitude || coords[0];
        const lon = coords.longitude || coords[1];
        if (typeof lat !== 'number' || typeof lon !== 'number') {
          return null;
        }
        return { ...complaint, _lat: lat, _lon: lon };
      })
      .filter(Boolean);
  }, [complaints]);

  const { clusters, singles } = useMemo(() => {
    if (!enableClustering) {
      return { clusters: [], singles: normalizedComplaints };
    }

    const clusterMap = new Map();
    normalizedComplaints.forEach((complaint) => {
      const latKey = Math.round(complaint._lat / CLUSTER_GRID_SIZE) * CLUSTER_GRID_SIZE;
      const lonKey = Math.round(complaint._lon / CLUSTER_GRID_SIZE) * CLUSTER_GRID_SIZE;
      const key = `${latKey.toFixed(4)}-${lonKey.toFixed(4)}`;
      if (!clusterMap.has(key)) {
        clusterMap.set(key, []);
      }
      clusterMap.get(key).push(complaint);
    });

    const clusterResults = [];
    const singleResults = [];

    clusterMap.forEach((items) => {
      if (items.length <= 1) {
        singleResults.push(...items);
        return;
      }

      const latSum = items.reduce((acc, item) => acc + item._lat, 0);
      const lonSum = items.reduce((acc, item) => acc + item._lon, 0);
      const categories = items.reduce((acc, item) => {
        acc[item.category] = (acc[item.category] || 0) + 1;
        return acc;
      }, {});

      clusterResults.push({
        lat: latSum / items.length,
        lon: lonSum / items.length,
        count: items.length,
        categories,
        items
      });
    });

    return { clusters: clusterResults, singles: singleResults };
  }, [normalizedComplaints, enableClustering]);

  // Log map initialization
  useEffect(() => {
    console.log('MapVisualizer initialized with:', {
      riskZones: riskZones.length,
      complaints: complaints.length,
      center: BENGALURU_CENTER,
      zoom: DEFAULT_ZOOM
    });
  }, []);

  // Handle map updates when data changes
  useEffect(() => {
    console.log('MapVisualizer data updated:', {
      riskZones: riskZones.length,
      complaints: complaints.length
    });
  }, [riskZones, complaints]);

  return (
    <div className="map-visualizer">
      {(loading || error) && (
        <div className={`map-overlay ${error ? 'error' : ''}`}>
          {error ? error : 'Loading map data...'}
        </div>
      )}
      <MapContainer
        center={BENGALURU_CENTER}
        zoom={DEFAULT_ZOOM}
        minZoom={MIN_ZOOM}
        maxZoom={MAX_ZOOM}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        {/* OpenStreetMap Tile Layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={MAX_ZOOM}
        />
        
        {/* Map Controller for dynamic updates */}
        <MapController center={BENGALURU_CENTER} zoom={DEFAULT_ZOOM} />
        
        {/* Risk Zones - Render as colored circles */}
        {riskZones.map((zone) => {
          // Extract coordinates from zone data
          const center = zone.center_coordinates || zone.coordinates;
          if (!center || !Array.isArray(center) || center.length !== 2) {
            console.warn('Invalid zone coordinates:', zone);
            return null;
          }

          const [lat, lon] = center;
          const riskScore = zone.risk_score || 0;
          const color = getRiskZoneColor(riskScore);
          const riskLevel = getRiskLevelLabel(riskScore);
          const complaintCount = zone.complaint_count || 0;
          const radius = zone.radius_meters || 500; // Default 500m radius

          return (
            <Circle
              key={zone.zone_id || `zone-${lat}-${lon}`}
              center={[lat, lon]}
              radius={radius}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.3,
                weight: 2,
              }}
              eventHandlers={{
                click: () => {
                  console.log('Risk zone clicked:', zone);
                },
              }}
            >
              <Popup>
                <div className="risk-zone-popup">
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '16px', fontWeight: '600' }}>
                    {riskLevel}
                  </h3>
                  <div style={{ marginBottom: '4px' }}>
                    <strong>Risk Score:</strong> {riskScore.toFixed(1)}
                  </div>
                  <div style={{ marginBottom: '4px' }}>
                    <strong>Complaints:</strong> {complaintCount}
                  </div>
                  {zone.dominant_category && (
                    <div style={{ marginBottom: '4px' }}>
                      <strong>Category:</strong> {zone.dominant_category}
                    </div>
                  )}
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px' }}>
                    Location: {lat.toFixed(4)}, {lon.toFixed(4)}
                  </div>
                </div>
              </Popup>
            </Circle>
          );
        })}
        
        {/* Complaint Markers - Display individual complaints with category-specific icons */}
        {/* Validates: Requirements 11.4, 11.5 */}
        {clusters.map((cluster) => (
          <Marker
            key={`cluster-${cluster.lat}-${cluster.lon}-${cluster.count}`}
            position={[cluster.lat, cluster.lon]}
            icon={createClusterIcon(cluster.count)}
          >
            <Popup>
              <div className="complaint-popup">
                <h3 style={{ margin: '0 0 8px 0', fontSize: '16px', fontWeight: '600' }}>
                  {cluster.count} Complaints
                </h3>
                <div style={{ fontSize: '13px', marginBottom: '8px' }}>
                  Clustered complaints within ~300m grid
                </div>
                {Object.keys(cluster.categories).map((category) => (
                  <div key={category} style={{ fontSize: '13px', marginBottom: '4px' }}>
                    <strong>{category.replace('_', ' ')}:</strong> {cluster.categories[category]}
                  </div>
                ))}
              </div>
            </Popup>
          </Marker>
        ))}

        {singles.map((complaint) => {
          const icon = createComplaintIcon(complaint.category);

          return (
            <Marker
              key={complaint.complaint_id}
              position={[complaint._lat, complaint._lon]}
              icon={icon}
              eventHandlers={{
                click: () => {
                  console.log('Complaint marker clicked:', complaint);
                },
              }}
            >
              <Popup>
                <div className="complaint-popup">
                  <h3 style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '16px', 
                    fontWeight: '600',
                    textTransform: 'capitalize'
                  }}>
                    {complaint.category.replace('_', ' ')}
                  </h3>
                  <div style={{ marginBottom: '4px' }}>
                    <strong>Location:</strong> {complaint.location}
                  </div>
                  <div style={{ marginBottom: '4px' }}>
                    <strong>Description:</strong>
                    <p style={{ margin: '4px 0', fontSize: '14px', color: '#374151' }}>
                      {complaint.description}
                    </p>
                  </div>
                  <div style={{ marginBottom: '4px' }}>
                    <strong>Reported:</strong> {formatTimestamp(complaint.timestamp)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px' }}>
                    ID: {complaint.complaint_id.substring(0, 8)}...
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
      
      {/* Map Legend */}
      <div className="map-legend">
        <div className="legend-title">Map Legend</div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#22c55e' }}></span>
          <span>Low Risk (0-33)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#eab308' }}></span>
          <span>Medium Risk (34-66)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ef4444' }}></span>
          <span>High Risk (67-100)</span>
        </div>
      </div>
      
      {/* Map Stats */}
      <div className="map-stats">
        <div className="stat-item">
          <span className="stat-label">Risk Zones:</span>
          <span className="stat-value">{riskZones.length}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Complaints:</span>
          <span className="stat-value">{complaints.length}</span>
        </div>
      </div>
    </div>
  );
};

export default MapVisualizer;
