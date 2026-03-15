import React, { useEffect, useRef, useMemo, memo } from 'react';
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
  const initializedRef = useRef(false);
  
  useEffect(() => {
    // Only set view once on mount, never on re-renders
    if (!initializedRef.current && center && zoom) {
      map.setView(center, zoom);
      initializedRef.current = true;
    }
  }, [map, center, zoom]);
  
  return null;
};

/**
 * Get color for risk zone based on risk score
 * Green: 0-20 (low risk)
 * Yellow: 21-45 (medium risk)
 * Red: 46-100 (high risk)
 */
const getRiskZoneColor = (riskScore) => {
  if (riskScore <= 20) {
    return '#22c55e'; // Green - low risk
  } else if (riskScore <= 45) {
    return '#eab308'; // Yellow - medium risk
  } else {
    return '#ef4444'; // Red - high risk
  }
  return '#9ca3af';
};

/**
 * Get risk level label based on risk score
 */
const getRiskLevelLabel = (riskScore) => {
  if (riskScore <= 20) {
    return 'Low Risk';
  } else if (riskScore <= 45) {
    return 'Medium Risk';
  } else {
    return 'High Risk';
  }
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
    <div style="
      width:${size}px;height:${size}px;
      border-radius:50%;
      background:radial-gradient(circle at 30% 30%,#1d4ed8,#0f172a);
      box-shadow:0 4px 12px rgba(15,23,42,0.35);
      border:2.5px solid rgba(255,255,255,0.95);
      display:flex;align-items:center;justify-content:center;
    ">
      <span style="
        color:#fff;font-weight:700;font-size:${fontSize}px;
        font-family:system-ui,sans-serif;line-height:1;
      ">${count}</span>
    </div>
  `;
  return L.divIcon({
    html,
    className: '',
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
        if (!coords) return null;
        const lat = coords.latitude != null ? coords.latitude : coords[0];
        const lon = coords.longitude != null ? coords.longitude : coords[1];
        if (typeof lat !== 'number' || typeof lon !== 'number' || isNaN(lat) || isNaN(lon)) {
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
      const latBucket = Math.round(complaint._lat / CLUSTER_GRID_SIZE);
      const lonBucket = Math.round(complaint._lon / CLUSTER_GRID_SIZE);
      const key = `${latBucket}-${lonBucket}`;
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

  // intentionally empty — map is initialized via MapContainer props

  return (
    <div className="map-visualizer">
      {(loading && riskZones.length === 0 && !error) && (
        <div className="map-overlay">
          Loading map data...
        </div>
      )}
      {error && riskZones.length === 0 && (
        <div className="map-overlay error">
          {error}
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
          // Extract coordinates — backend returns { latitude, longitude } object
          const raw = zone.center_coordinates || zone.coordinates;
          if (!raw) {
            console.warn('Invalid zone coordinates:', zone);
            return null;
          }
          const lat = Array.isArray(raw) ? raw[0] : raw.latitude;
          const lon = Array.isArray(raw) ? raw[1] : raw.longitude;
          if (typeof lat !== 'number' || typeof lon !== 'number') {
            console.warn('Invalid zone coordinates:', zone);
            return null;
          }
          const riskScore = zone.risk_score || 0;
          const color = getRiskZoneColor(riskScore);
          const riskLevel = getRiskLevelLabel(riskScore);
          const complaintCount = zone.complaint_count || 0;
          // Make radius visually meaningful — minimum 1km, scale up with score
          const radius = Math.max(zone.radius_meters || 500, 1000) + (riskScore * 20);

          return (
            <Circle
              key={zone.zone_id || `zone-${lat}-${lon}`}
              center={[lat, lon]}
              radius={radius}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.35,
                weight: 3,
                opacity: 0.9,
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
            key={`cluster-${cluster.lat.toFixed(4)}-${cluster.lon.toFixed(4)}`}
            position={[cluster.lat, cluster.lon]}
            icon={createClusterIcon(cluster.count)}
          >
            <Popup minWidth={280} maxWidth={320}>
              <div className="complaint-popup">
                <h3 style={{ margin: '0 0 8px 0', fontSize: '15px', fontWeight: '600' }}>
                  {cluster.count} Complaints in this area
                </h3>
                <div style={{ maxHeight: '260px', overflowY: 'auto' }}>
                  {cluster.items.map((complaint, idx) => (
                    <div key={complaint.complaint_id} style={{
                      borderTop: idx > 0 ? '1px solid #e5e7eb' : 'none',
                      paddingTop: idx > 0 ? '8px' : '0',
                      marginTop: idx > 0 ? '8px' : '0',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                        <strong style={{ fontSize: '13px', textTransform: 'capitalize', color: '#111827' }}>
                          {complaint.category.replace('_', ' ')}
                        </strong>
                        <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                          {formatTimestamp(complaint.timestamp)}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#374151', marginBottom: '2px' }}>
                        <strong>Location:</strong> {complaint.location}
                      </div>
                      <div style={{ fontSize: '12px', color: '#4b5563' }}>
                        {complaint.description}
                      </div>
                    </div>
                  ))}
                </div>
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
          <span>Low Risk (0-20)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#eab308' }}></span>
          <span>Medium Risk (21-45)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ef4444' }}></span>
          <span>High Risk (46-100)</span>
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

export default memo(MapVisualizer);
