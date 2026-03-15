import React, { useState, useRef, useEffect, useCallback } from 'react';
import { complaintsAPI } from '../services/api';
import LocationPicker from './LocationPicker';
import './ComplaintForm.css';

const categories = [
  { value: 'pothole', label: 'Pothole' },
  { value: 'flooding', label: 'Flooding' },
  { value: 'traffic', label: 'Traffic' },
  { value: 'garbage', label: 'Garbage' },
  { value: 'streetlight', label: 'Street Light' },
  { value: 'water_supply', label: 'Water Supply' },
  { value: 'noise', label: 'Noise' },
  { value: 'construction', label: 'Construction' },
];

/**
 * LocationSearch — free-text address search with Nominatim autocomplete.
 * Restricts results to Bengaluru bounding box for relevance.
 */
const BENGALURU_VIEWBOX = '77.4601,12.8340,77.7840,13.1390';

function LocationSearch({ value, coords, onChange, disabled }) {
  const [query, setQuery] = useState(value || '');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const wrapperRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setSuggestions([]);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const search = useCallback(async (q) => {
    if (q.trim().length < 3) { setSuggestions([]); return; }
    setLoading(true);
    try {
      // Use structured query: street/place + city fixed to Bengaluru
      // bounded=0 so specific places (apartments, streets) aren't excluded
      // viewbox still biases results toward Bengaluru without hard-cutting
      const url = `https://nominatim.openstreetmap.org/search?` +
        `q=${encodeURIComponent(q)},Bengaluru` +
        `&format=json&limit=8&countrycodes=in&addressdetails=1` +
        `&viewbox=${BENGALURU_VIEWBOX}&bounded=0`;
      const res = await fetch(url, {
        headers: { 'Accept-Language': 'en', 'User-Agent': 'UrbanGuardAI/1.0' },
      });
      const data = await res.json();
      // Filter to results that are actually in/near Bengaluru
      const filtered = data.filter(item => {
        const addr = item.address || {};
        const city = (addr.city || addr.town || addr.county || '').toLowerCase();
        return city.includes('bengaluru') || city.includes('bangalore') ||
          item.display_name.toLowerCase().includes('bengaluru') ||
          item.display_name.toLowerCase().includes('bangalore');
      });
      setSuggestions(filtered.length > 0 ? filtered : data.slice(0, 5));
    } catch {
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInput = (e) => {
    const q = e.target.value;
    setQuery(q);
    // Clear confirmed selection if user edits
    onChange('', null);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(q), 350);
  };

  const handleSelect = (item) => {
    const parts = item.display_name.split(',').map(p => p.trim());
    const label = parts.slice(0, 3).join(', ');
    setQuery(label);
    setSuggestions([]);
    onChange(label, { lat: parseFloat(item.lat), lng: parseFloat(item.lon) });
  };

  return (
    <div className="location-search-wrapper" ref={wrapperRef}>
      <input
        type="text"
        className="location-search-input"
        placeholder="Type your area, e.g. Electronic City Phase 2"
        value={query}
        onChange={handleInput}
        disabled={disabled}
        autoComplete="off"
      />
      {coords && (
        <span className="location-confirmed" title="Location confirmed">✓ pinned</span>
      )}
      {loading && <span className="location-loading">Searching…</span>}
      {suggestions.length > 0 && (
        <ul className="location-suggestions">
          {suggestions.map((s) => {
            // Show short name + neighbourhood context, not the full address string
            const parts = s.display_name.split(',').map(p => p.trim());
            const short = parts.slice(0, 3).join(', ');
            const context = parts.slice(3, 5).join(', ');
            return (
              <li key={s.place_id} onMouseDown={() => handleSelect(s)}>
                <span className="suggestion-main">{short}</span>
                {context && <span className="suggestion-sub">{context}</span>}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/**
 * ComplaintForm — submit a civic complaint with precise geocoded location.
 */
const ComplaintForm = ({ onSubmitStart, onSubmitSuccess, onSubmitError }) => {
  const [location, setLocation] = useState('');
  const [locationCoords, setLocationCoords] = useState(null);
  const [locationMode, setLocationMode] = useState('search'); // 'search' | 'map'
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState(null);
  const [lastPayload, setLastPayload] = useState(null);
  const [showRetry, setShowRetry] = useState(false);

  const clearMessage = () => { setMessage(null); setMessageType(null); setShowRetry(false); };

  const handleLocationChange = (label, coords) => {
    setLocation(label);
    setLocationCoords(coords);
    clearMessage();
  };

  const validate = () => {
    if (!location.trim()) {
      setMessage('Please enter and select a location'); setMessageType('error'); return false;
    }
    if (!locationCoords) {
      setMessage('Please select a location from the suggestions'); setMessageType('error'); return false;
    }
    if (!category) {
      setMessage('Please select a category'); setMessageType('error'); return false;
    }
    if (description.trim().length < 10) {
      setMessage('Description must be at least 10 characters'); setMessageType('error'); return false;
    }
    return true;
  };

  const submitComplaint = async (payload) => {
    setIsSubmitting(true);
    clearMessage();
    if (onSubmitStart) onSubmitStart();
    try {
      await complaintsAPI.submitComplaint(payload);
      setMessage('Complaint submitted successfully!');
      setMessageType('success');
      setLocation(''); setLocationCoords(null); setCategory(''); setDescription('');
      if (onSubmitSuccess) setTimeout(onSubmitSuccess, 800);
    } catch (error) {
      const msg = error.response?.data?.detail || error.message || 'Failed to submit complaint.';
      setMessage(msg); setMessageType('error'); setShowRetry(true); setLastPayload(payload);
      if (onSubmitError) onSubmitError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    const payload = {
      location: location.trim(),
      category,
      description: description.trim(),
      timestamp: new Date().toISOString(),
      coordinates: locationCoords,
    };
    setLastPayload(payload);
    await submitComplaint(payload);
  };

  return (
    <div className="complaint-form-container">
      <h2>Report a Complaint</h2>
      <p className="form-description">
        Help us improve Bengaluru by reporting infrastructure issues in your area.
      </p>

      <form onSubmit={handleSubmit} className="complaint-form">
        <div className="form-group">
          <label htmlFor="location">
            Location <span className="required">*</span>
          </label>

          {/* Toggle between text search and map picker */}
          <div className="location-mode-toggle">
            <button
              type="button"
              className={`mode-btn ${locationMode === 'search' ? 'active' : ''}`}
              onClick={() => setLocationMode('search')}
            >
              🔍 Search
            </button>
            <button
              type="button"
              className={`mode-btn ${locationMode === 'map' ? 'active' : ''}`}
              onClick={() => setLocationMode('map')}
            >
              🗺 Pick on Map
            </button>
          </div>

          {locationMode === 'search' ? (
            <LocationSearch
              value={location}
              coords={locationCoords}
              onChange={handleLocationChange}
              disabled={isSubmitting}
            />
          ) : (
            <LocationPicker
              onSelect={(label, coords) => {
                handleLocationChange(label, coords);
                setLocationMode('search'); // switch back to show confirmed address
              }}
            />
          )}
        </div>

        <div className="form-group">
          <label htmlFor="category">
            Category <span className="required">*</span>
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => { setCategory(e.target.value); clearMessage(); }}
            disabled={isSubmitting}
            required
          >
            <option value="">Select a category</option>
            {categories.map(c => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="description">
            Description <span className="required">*</span>
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => { setDescription(e.target.value); clearMessage(); }}
            placeholder="Describe the issue in detail..."
            rows="4"
            disabled={isSubmitting}
            required
          />
          <div className="char-count">{description.length} characters</div>
        </div>

        {message && (
          <div className={`form-message ${messageType}`}>
            <span>{messageType === 'success' ? '✓ ' : '✗ '}{message}</span>
            {showRetry && (
              <button type="button" className="retry-button"
                onClick={() => lastPayload && submitComplaint(lastPayload)}
                disabled={isSubmitting}>
                Retry
              </button>
            )}
          </div>
        )}

        <button type="submit" className="submit-button" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting…' : 'Submit Complaint'}
        </button>
      </form>
    </div>
  );
};

export default ComplaintForm;
