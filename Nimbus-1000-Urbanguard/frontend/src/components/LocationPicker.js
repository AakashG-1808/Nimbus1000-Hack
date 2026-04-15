import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './LocationPicker.css';

const BENGALURU_CENTER = [12.9716, 77.5946];
const DEFAULT_ZOOM = 13;

// Fix Leaflet default icon paths broken by webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

/** Reverse-geocode lat/lng → human-readable address via Nominatim */
async function reverseGeocode(lat, lng) {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`,
      { headers: { 'Accept-Language': 'en', 'User-Agent': 'UrbanGuardAI/1.0' } }
    );
    const data = await res.json();
    if (data.display_name) {
      // Return first 3 meaningful parts
      return data.display_name.split(',').slice(0, 3).join(', ').trim();
    }
  } catch { /* fall through */ }
  return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

/** Invisible component that listens for map clicks to drop a pin */
function ClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

/**
 * LocationPicker
 *
 * Props:
 *   onSelect(label, { lat, lng }) — called when a location is confirmed
 */
export default function LocationPicker({ onSelect }) {
  const [pin, setPin] = useState(null);          // { lat, lng }
  const [label, setLabel] = useState('');
  const [resolving, setResolving] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsError, setGpsError] = useState('');
  const mapRef = useRef(null);

  const pickCoords = useCallback(async (lat, lng) => {
    setPin({ lat, lng });
    setResolving(true);
    setLabel('');
    const addr = await reverseGeocode(lat, lng);
    setLabel(addr);
    setResolving(false);
    // Pan map to pin
    if (mapRef.current) {
      mapRef.current.panTo([lat, lng]);
    }
  }, []);

  const handleGPS = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation not supported by your browser.');
      return;
    }
    setGpsLoading(true);
    setGpsError('');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsLoading(false);
        pickCoords(pos.coords.latitude, pos.coords.longitude);
      },
      (err) => {
        setGpsLoading(false);
        setGpsError('Could not get your location. Please allow location access.');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleConfirm = () => {
    if (pin && label) {
      onSelect(label, { lat: pin.lat, lng: pin.lng });
    }
  };

  return (
    <div className="location-picker">
      <div className="lp-hint">
        Tap the map to drop a pin, or use <strong>Current Location</strong>.
      </div>

      <div className="lp-map-wrap">
        <MapContainer
          center={BENGALURU_CENTER}
          zoom={DEFAULT_ZOOM}
          className="lp-map"
          ref={mapRef}
          zoomControl={true}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          <ClickHandler onPick={pickCoords} />
          {pin && <Marker position={[pin.lat, pin.lng]} />}
        </MapContainer>
      </div>

      <div className="lp-controls">
        <button
          type="button"
          className="lp-gps-btn"
          onClick={handleGPS}
          disabled={gpsLoading}
        >
          {gpsLoading ? '📡 Locating…' : '📍 Current Location'}
        </button>

        {resolving && <span className="lp-resolving">Resolving address…</span>}

        {label && !resolving && (
          <div className="lp-address">
            <span className="lp-address-text">📌 {label}</span>
            <button
              type="button"
              className="lp-confirm-btn"
              onClick={handleConfirm}
            >
              Use this location
            </button>
          </div>
        )}

        {gpsError && <p className="lp-error">{gpsError}</p>}
      </div>
    </div>
  );
}
