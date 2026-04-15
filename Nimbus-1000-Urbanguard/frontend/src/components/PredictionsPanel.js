import React from 'react';
import './PredictionsPanel.css';

const BENGALURU_AREAS = [
  { name: 'Koramangala', lat: 12.9352, lng: 77.6245 },
  { name: 'Indiranagar', lat: 12.9784, lng: 77.6408 },
  { name: 'Whitefield', lat: 12.9698, lng: 77.7499 },
  { name: 'Electronic City', lat: 12.8399, lng: 77.6770 },
  { name: 'Marathahalli', lat: 12.9591, lng: 77.6974 },
  { name: 'HSR Layout', lat: 12.9116, lng: 77.6389 },
  { name: 'BTM Layout', lat: 12.9166, lng: 77.6101 },
  { name: 'Jayanagar', lat: 12.9308, lng: 77.5838 },
  { name: 'Banashankari', lat: 12.9255, lng: 77.5468 },
  { name: 'Rajajinagar', lat: 12.9907, lng: 77.5530 },
  { name: 'Malleshwaram', lat: 13.0035, lng: 77.5710 },
  { name: 'Hebbal', lat: 13.0350, lng: 77.5970 },
  { name: 'Yelahanka', lat: 13.1007, lng: 77.5963 },
  { name: 'Bannerghatta', lat: 12.8635, lng: 77.5975 },
  { name: 'Vijayanagar', lat: 12.9719, lng: 77.5322 },
  { name: 'Yeshwanthpur', lat: 13.0280, lng: 77.5390 },
  { name: 'JP Nagar', lat: 12.9063, lng: 77.5857 },
  { name: 'Bellandur', lat: 12.9257, lng: 77.6762 },
  { name: 'Sarjapur', lat: 12.8604, lng: 77.7857 },
  { name: 'KR Puram', lat: 13.0050, lng: 77.6960 },
  { name: 'City Center', lat: 12.9716, lng: 77.5946 },
];

const nearestArea = (coords) => {
  if (!coords) return null;
  const { latitude: lat, longitude: lng } = coords;
  let best = BENGALURU_AREAS[0];
  let bestDist = Infinity;
  for (const area of BENGALURU_AREAS) {
    const d = Math.hypot(area.lat - lat, area.lng - lng);
    if (d < bestDist) { bestDist = d; best = area; }
  }
  return best.name;
};

/**
 * PredictionsPanel Component
 * Displays active incident predictions from the risk engine
 * 
 * Props:
 * - predictions: Array of prediction objects
 * - loading: Boolean loading state
 * - error: Error message string
 * - stale: Boolean stale data indicator
 * - onPredictionClick: Callback when a prediction card is clicked (zone_id)
 */
const PredictionsPanel = ({ predictions = [], loading = false, error = null, stale = false, onPredictionClick }) => {

  const INCIDENT_ICONS = {
    flooding: '🌊',
    traffic_congestion: '🚗',
    traffic_gridlock: '🚗',
    road_damage: '🕳️',
    waste_accumulation: '🗑️',
    lighting_failure: '💡',
    water_shortage: '🚰',
    noise_pollution: '🔊',
    construction_hazard: '🚧',
    infrastructure_issue: '⚠️',
  };

  const FACTOR_LABELS = {
    high_complaint_density: 'High Complaint Density',
    high_rainfall: 'Heavy Rainfall',
    high_wind: 'Strong Winds',
    high_traffic_congestion: 'Traffic Congestion',
    pothole_complaints: 'Pothole Reports',
    flooding_complaints: 'Flooding Reports',
    traffic_complaints: 'Traffic Reports',
    garbage_complaints: 'Garbage Reports',
    streetlight_complaints: 'Streetlight Reports',
    water_supply_complaints: 'Water Supply Reports',
    noise_complaints: 'Noise Reports',
    construction_complaints: 'Construction Reports',
    mixed_complaints: 'Mixed Reports',
  };

  const formatIncidentType = (type) => {
    return type
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getUrgencyClass = (riskScore) => {
    if (riskScore > 85) return 'urgency-critical';
    return 'urgency-high';
  };

  const getFactorLabel = (factor) => {
    return FACTOR_LABELS[factor] || factor.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  if (loading && predictions.length === 0) {
    return (
      <div className="predictions-panel">
        {[...Array(3)].map((_, index) => (
          <div key={index} className="prediction-skeleton">
            <div className="skeleton skeleton-icon"></div>
            <div className="skeleton skeleton-line"></div>
            <div className="skeleton skeleton-line short"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error && predictions.length === 0) {
    return (
      <div className="predictions-panel">
        <div className="predictions-error">{error}</div>
      </div>
    );
  }

  if (predictions.length === 0) {
    return (
      <div className="predictions-panel">
        <div className="predictions-empty">
          <span className="empty-icon">✅</span>
          <p>No incidents predicted</p>
          <span className="empty-detail">All zones are within safe thresholds</span>
        </div>
        {stale && <span className="stale-indicator">Showing stale data</span>}
      </div>
    );
  }

  return (
    <div className="predictions-panel">
      {predictions.map((prediction) => (
        <div
          key={prediction.prediction_id}
          className={`prediction-card ${getUrgencyClass(prediction.risk_score)}`}
          onClick={() => onPredictionClick && onPredictionClick(prediction.zone_id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onPredictionClick && onPredictionClick(prediction.zone_id)}
        >
          <div className="prediction-header">
            <span className="prediction-icon">
              {INCIDENT_ICONS[prediction.incident_type] || '⚠️'}
            </span>
            <div className="prediction-title">
              <span className="prediction-type">{formatIncidentType(prediction.incident_type)}</span>
              {nearestArea(prediction.coordinates) && (
                <span className="prediction-location">
                  📍 {nearestArea(prediction.coordinates)}
                </span>
              )}
              <span className={`prediction-window ${prediction.time_window === 'next 6 hours' ? 'urgent' : ''}`}>
                {prediction.time_window === 'next 6 hours' ? '⏰ ' : '🕐 '}
                {prediction.time_window}
              </span>
            </div>
          </div>

          <div className="prediction-score-bar">
            <div className="score-bar-bg">
              <div
                className="score-bar-fill"
                style={{ width: `${Math.min(prediction.risk_score, 100)}%` }}
              ></div>
            </div>
            <span className="score-value">{prediction.risk_score.toFixed(0)}</span>
          </div>

          <div className="prediction-factors">
            {prediction.explanation && (
              <p className="prediction-explanation">{prediction.explanation}</p>
            )}
            {prediction.contributing_factors.map((factor, index) => (
              <span key={index} className="factor-tag">
                {getFactorLabel(factor)}
              </span>
            ))}
          </div>
        </div>
      ))}

      {stale && <div className="predictions-stale">Showing stale data</div>}
    </div>
  );
};

export default PredictionsPanel;
