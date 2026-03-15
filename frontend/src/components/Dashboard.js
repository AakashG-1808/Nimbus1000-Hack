import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { complaintsAPI, riskAPI, weatherAPI, trafficAPI, predictionsAPI, reportsAPI, websocketAPI } from '../services/api';
import { getCurrentUser, logout, isAdmin } from '../services/auth';
import MapVisualizer from './MapVisualizer';
import ComplaintFeed from './ComplaintFeed';
import TrendCharts from './TrendCharts';
import WeatherPanel from './WeatherPanel';
import TrafficPanel from './TrafficPanel';
import PredictionsPanel from './PredictionsPanel';
import AIInsightsPanel from './AIInsightsPanel';
import ComplaintForm from './ComplaintForm';
import './Dashboard.css';

/**
 * Main Dashboard component with grid layout
 * Implements 30-second polling for real-time updates
 * 
 * Validates: Requirements 12.1, 12.2
 */
const Dashboard = () => {
  const CATEGORY_OPTIONS = [
    { value: 'pothole', label: 'Pothole' },
    { value: 'flooding', label: 'Flooding' },
    { value: 'traffic', label: 'Traffic' },
    { value: 'garbage', label: 'Garbage' },
    { value: 'streetlight', label: 'Street Light' },
    { value: 'water_supply', label: 'Water Supply' },
    { value: 'noise', label: 'Noise' },
    { value: 'construction', label: 'Construction' },
  ];

  const TIME_RANGE_OPTIONS = [
    { value: '6h', label: 'Last 6 hours', hours: 6 },
    { value: '24h', label: 'Last 24 hours', hours: 24 },
    { value: '7d', label: 'Last 7 days', hours: 24 * 7 },
    { value: '30d', label: 'Last 30 days', hours: 24 * 30 },
    { value: 'all', label: 'All time', hours: null },
  ];

  const RISK_LEVEL_OPTIONS = [
    { value: 'all', label: 'All risk levels' },
    { value: 'high', label: 'High risk' },
    { value: 'medium', label: 'Medium risk' },
    { value: 'low', label: 'Low risk' },
  ];

  const DEFAULT_CATEGORY_TOGGLES = CATEGORY_OPTIONS.reduce((acc, option) => {
    acc[option.value] = true;
    return acc;
  }, {});

  const BASE_POLL_INTERVAL = 30000;
  const MAX_POLL_INTERVAL = 120000;

  // State for all dashboard data
  const [complaintsState, setComplaintsState] = useState({
    data: [],
    loading: true,
    error: null,
    lastUpdated: null
  });
  const [riskZonesState, setRiskZonesState] = useState({
    data: [],
    loading: true,
    error: null,
    lastUpdated: null
  });
  const [weatherState, setWeatherState] = useState({
    data: null,
    loading: true,
    error: null,
    lastUpdated: null
  });
  const [trafficState, setTrafficState] = useState({
    data: [],
    loading: true,
    error: null,
    lastUpdated: null
  });
  const [predictionsState, setPredictionsState] = useState({
    data: [],
    loading: true,
    error: null,
    lastUpdated: null
  });
  const [dailyReportState, setDailyReportState] = useState({
    data: null,
    loading: true,
    error: null,
    lastUpdated: null
  });
  const [pollIntervalMs, setPollIntervalMs] = useState(BASE_POLL_INTERVAL);
  const [isPollingPaused, setIsPollingPaused] = useState(false);
  const [wsStatus, setWsStatus] = useState('disconnected');
  // Ticks every second so relative timestamps re-render automatically
  const [, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);
  const [filters, setFilters] = useState({
    category: 'all',
    timeRange: '24h',
    riskLevel: 'all',
    showClusters: true,
    categoryToggles: DEFAULT_CATEGORY_TOGGLES
  });
  const [toast, setToast] = useState(null);
  const [showComplaintForm, setShowComplaintForm] = useState(false);
  const [isSubmittingComplaint, setIsSubmittingComplaint] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [classificationEngine, setClassificationEngine] = useState(null);
  const modalContentRef = useRef(null);
  const isTabVisibleRef = useRef(true);

  // User auth info
  const user = getCurrentUser();
  const userIsAdmin = isAdmin();
  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  // Theme configuration
  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Fetch real classification engine status from backend once on mount
  useEffect(() => {
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    fetch(`${baseUrl}/health`)
      .then(r => r.json())
      .then(data => setClassificationEngine(data.classification_engine || 'keyword_fallback'))
      .catch(() => setClassificationEngine('keyword_fallback'));
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // State handlers
  const exportToCSV = () => {
    const headers = ['Complaint ID', 'Category', 'Location', 'Risk Score', 'Description', 'Timestamp', 'AI Confidence'];
    const rows = filteredComplaints.map(c => {
      // Find matching risk score for the location if possible
      const riskZone = riskZonesState.data.find(z => z.zone_id === c.location.toLowerCase().replace(/\s+/g, '-'));
      const riskScore = riskZone ? Math.round(riskZone.risk_score) : 'N/A';
      return [
        c.complaint_id,
        c.category,
        c.location,
        riskScore,
        `"${(c.description || '').replace(/"/g, '""')}"`, // escape quotes and wrap in quotes to handle commas
        new Date(c.timestamp).toLocaleString(),
        c.classification_confidence ? Math.round(c.classification_confidence * 100) + '%' : 'N/A'
      ];
    });

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers, ...rows].map(e => e.join(",")).join("\n");
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `urbanguard_complaints_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link); // Required for FF
    link.click();
    document.body.removeChild(link);
  };

  const formatRelativeTime = (timestamp) => {
    if (!timestamp) {
      return 'No data yet';
    }
    const now = Date.now();
    const deltaSeconds = Math.floor((now - timestamp.getTime()) / 1000);
    if (deltaSeconds < 60) {
      return `${deltaSeconds}s ago`;
    }
    const deltaMinutes = Math.floor(deltaSeconds / 60);
    if (deltaMinutes < 60) {
      return `${deltaMinutes}m ago`;
    }
    const deltaHours = Math.floor(deltaMinutes / 60);
    if (deltaHours < 24) {
      return `${deltaHours}h ago`;
    }
    const deltaDays = Math.floor(deltaHours / 24);
    return `${deltaDays}d ago`;
  };

  const isStale = (state) => {
    if (!state.lastUpdated || !state.error) {
      return false;
    }
    const staleThreshold = pollIntervalMs * 2;
    return Date.now() - state.lastUpdated.getTime() > staleThreshold;
  };

  const getSinceTimestamp = (range) => {
    const option = TIME_RANGE_OPTIONS.find((item) => item.value === range);
    if (!option || !option.hours) {
      return null;
    }
    const since = new Date();
    since.setHours(since.getHours() - option.hours);
    return since;
  };

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(async ({ isInitial = false } = {}) => {
    try {
      if (isInitial) {
        setComplaintsState((prev) => ({ ...prev, loading: true }));
        setRiskZonesState((prev) => ({ ...prev, loading: true }));
        setWeatherState((prev) => ({ ...prev, loading: true }));
        setTrafficState((prev) => ({ ...prev, loading: true }));
        setPredictionsState((prev) => ({ ...prev, loading: true }));
        setDailyReportState((prev) => ({ ...prev, loading: true }));
      }

      const complaintParams = {
        offset: 0,
        limit: 500
      };
      if (filters.category !== 'all') {
        complaintParams.category = filters.category;
      }
      const since = getSinceTimestamp(filters.timeRange);
      if (since) {
        complaintParams.since = since.toISOString();
      }

      // Fetch all data in parallel
      const [complaintsRes, riskRes, weatherRes, trafficRes, predictionsRes, reportRes] = await Promise.allSettled([
        complaintsAPI.getComplaints(complaintParams),
        riskAPI.getRiskHotspots(),
        weatherAPI.getWeather(),
        trafficAPI.getTraffic(),
        predictionsAPI.getPredictions(),
        reportsAPI.getDailyReport(),
      ]);

      const now = new Date();
      let hadError = false;

      if (complaintsRes.status === 'fulfilled') {
        setComplaintsState({
          data: complaintsRes.value.data,
          loading: false,
          error: null,
          lastUpdated: now
        });
      } else {
        hadError = true;
        setComplaintsState((prev) => ({
          ...prev,
          loading: false,
          error: 'Failed to refresh complaints data'
        }));
      }

      if (riskRes.status === 'fulfilled') {
        setRiskZonesState({
          data: riskRes.value.data,
          loading: false,
          error: null,
          lastUpdated: now
        });
      } else {
        hadError = true;
        setRiskZonesState((prev) => ({
          ...prev,
          loading: false,
          error: 'Failed to refresh risk zones'
        }));
      }

      if (weatherRes.status === 'fulfilled') {
        setWeatherState({
          data: weatherRes.value.data,
          loading: false,
          error: null,
          lastUpdated: now
        });
      } else {
        hadError = true;
        setWeatherState((prev) => ({
          ...prev,
          loading: false,
          error: 'Failed to refresh weather data'
        }));
      }

      if (trafficRes.status === 'fulfilled') {
        setTrafficState({
          data: trafficRes.value.data,
          loading: false,
          error: null,
          lastUpdated: now
        });
      } else {
        hadError = true;
        setTrafficState((prev) => ({
          ...prev,
          loading: false,
          error: 'Failed to refresh traffic data'
        }));
      }

      if (predictionsRes.status === 'fulfilled') {
        setPredictionsState({
          data: predictionsRes.value.data,
          loading: false,
          error: null,
          lastUpdated: now
        });
      } else {
        hadError = true;
        setPredictionsState((prev) => ({
          ...prev,
          loading: false,
          error: 'Failed to refresh predictions'
        }));
      }

      if (reportRes.status === 'fulfilled') {
        setDailyReportState({
          data: reportRes.value.data,
          loading: false,
          error: null,
          lastUpdated: now
        });
      } else {
        // Daily report 404 is expected if no reports yet
        setDailyReportState((prev) => ({
          ...prev,
          loading: false,
          error: null,
          lastUpdated: now
        }));
      }

      setPollIntervalMs((prev) => {
        if (hadError) {
          return Math.min(prev * 2, MAX_POLL_INTERVAL);
        }
        return BASE_POLL_INTERVAL;
      });
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setPollIntervalMs((prev) => Math.min(prev * 2, MAX_POLL_INTERVAL));
      setComplaintsState((prev) => ({ ...prev, loading: false, error: 'Failed to refresh complaints data' }));
      setRiskZonesState((prev) => ({ ...prev, loading: false, error: 'Failed to refresh risk zones' }));
      setWeatherState((prev) => ({ ...prev, loading: false, error: 'Failed to refresh weather data' }));
      setTrafficState((prev) => ({ ...prev, loading: false, error: 'Failed to refresh traffic data' }));
    }
  }, [filters.category, filters.timeRange]);

  // Initial data fetch
  useEffect(() => {
    fetchDashboardData({ isInitial: true });
  }, [fetchDashboardData]);

  // Set up adaptive polling for real-time updates
  useEffect(() => {
    let timeoutId;
    let isCancelled = false;

    const schedulePoll = () => {
      timeoutId = setTimeout(async () => {
        if (!isCancelled && isTabVisibleRef.current) {
          await fetchDashboardData();
        }
        if (!isCancelled) {
          schedulePoll();
        }
      }, pollIntervalMs);
    };

    schedulePoll();

    return () => {
      isCancelled = true;
      clearTimeout(timeoutId);
    };
  }, [fetchDashboardData, pollIntervalMs]);

  // Pause polling when tab is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      const isVisible = document.visibilityState === 'visible';
      isTabVisibleRef.current = isVisible;
      setIsPollingPaused(!isVisible);
      if (isVisible) {
        fetchDashboardData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [fetchDashboardData]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    websocketAPI.connect();

    const unsubStatus = websocketAPI.onStatusChange((status) => {
      setWsStatus(status);
    });

    const unsubMessage = websocketAPI.onMessage((data) => {
      if (data.type === 'new_complaint' && data.complaint) {
        // Prepend new complaint instantly
        setComplaintsState((prev) => ({
          ...prev,
          data: [data.complaint, ...prev.data],
          lastUpdated: new Date()
        }));

        // Show toast notification
        const category = data.complaint.category
          .split('_')
          .map(w => w.charAt(0).toUpperCase() + w.slice(1))
          .join(' ');
        setToast({
          type: 'info',
          message: `New complaint: ${category} at ${data.complaint.location}`
        });
      }
    });

    return () => {
      unsubStatus();
      unsubMessage();
      websocketAPI.disconnect();
    };
  }, []);

  // Handle successful complaint submission
  const handleComplaintSubmitStart = () => {
    setIsSubmittingComplaint(true);
  };

  const handleComplaintSubmitSuccess = () => {
    setIsSubmittingComplaint(false);
    setShowComplaintForm(false);
    setToast({ type: 'success', message: 'Complaint submitted successfully.' });
    fetchDashboardData();
  };

  const handleComplaintSubmitError = (message) => {
    setIsSubmittingComplaint(false);
    setToast({ type: 'error', message: message || 'Failed to submit complaint.' });
  };

  const closeComplaintForm = useCallback(() => {
    if (!isSubmittingComplaint) {
      setShowComplaintForm(false);
    }
  }, [isSubmittingComplaint]);

  useEffect(() => {
    if (!showComplaintForm) {
      return undefined;
    }

    const modalElement = modalContentRef.current;
    const previousActive = document.activeElement;
    if (!modalElement) {
      return undefined;
    }

    const focusableElements = modalElement.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (firstElement) {
      firstElement.focus();
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        closeComplaintForm();
      }
      if (event.key === 'Tab' && focusableElements.length > 0) {
        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (previousActive && previousActive.focus) {
        previousActive.focus();
      }
    };
  }, [showComplaintForm, closeComplaintForm]);

  useEffect(() => {
    if (!toast) {
      return undefined;
    }
    const timeoutId = setTimeout(() => {
      setToast(null);
    }, 4000);
    return () => clearTimeout(timeoutId);
  }, [toast]);

  const filteredComplaints = useMemo(() => {
    const activeCategories = Object.keys(filters.categoryToggles).filter(
      (category) => filters.categoryToggles[category]
    );
    return complaintsState.data.filter((complaint) =>
      activeCategories.includes(complaint.category)
    );
  }, [complaintsState.data, filters.categoryToggles]);

  // Only show open (unresolved) complaints on the map
  const openComplaints = useMemo(() => {
    return filteredComplaints.filter(c => (c.status || 'open') === 'open');
  }, [filteredComplaints]);

  const filteredRiskZones = useMemo(() => {
    if (filters.riskLevel === 'all') {
      return riskZonesState.data;
    }
    return riskZonesState.data.filter((zone) => {
      if (zone.risk_level) {
        return zone.risk_level === filters.riskLevel;
      }
      if (filters.riskLevel === 'high') {
        return zone.risk_score >= 67;
      }
      if (filters.riskLevel === 'medium') {
        return zone.risk_score >= 34 && zone.risk_score < 67;
      }
      return zone.risk_score < 34;
    });
  }, [riskZonesState.data, filters.riskLevel]);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="dashboard-header-top">
          <div className="dashboard-title-group">
            <h1>UrbanGuard AI Dashboard</h1>
            <p className="dashboard-subtitle">Live infrastructure signals across Bengaluru</p>
          </div>
          <div className="dashboard-header-right" style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <button 
              className="theme-toggle-btn" 
              onClick={toggleTheme}
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
              style={{
                background: 'transparent', border: '1px solid var(--border-light)', 
                borderRadius: '50%', width: '36px', height: '36px', 
                cursor: 'pointer', fontSize: '18px',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
              }}
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            
            {user && (
              <div className="user-profile">
                <span className="user-email">{user.email}</span>
                <span className={`user-role-badge ${user.role}`}>{user.role}</span>
                <button className="logout-btn" onClick={handleLogout}>Logout</button>
              </div>
            )}
          </div>
        </div>
        <div className="dashboard-filters">
          <div className="filter-group">
            <label htmlFor="filter-category">Category</label>
            <select
              id="filter-category"
              value={filters.category}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, category: event.target.value }))
              }
            >
              <option value="all">All categories</option>
              {CATEGORY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="filter-time-range">Time range</label>
            <select
              id="filter-time-range"
              value={filters.timeRange}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, timeRange: event.target.value }))
              }
            >
              {TIME_RANGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="filter-risk">Risk level</label>
            <select
              id="filter-risk"
              value={filters.riskLevel}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, riskLevel: event.target.value }))
              }
            >
              {RISK_LEVEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="dashboard-actions">
          {userIsAdmin && (
            <button 
              className="export-csv-button"
              onClick={exportToCSV}
              title="Export filtered complaints to CSV"
            >
              <span role="img" aria-label="download">⬇️</span> Export CSV
            </button>
          )}
          <button 
            className="report-complaint-button"
            onClick={() => setShowComplaintForm(true)}
            disabled={isSubmittingComplaint}
          >
            {isSubmittingComplaint ? 'Submitting...' : '+ Report Complaint'}
          </button>
        </div>
        <div className="dashboard-status">
          <span className={`status-indicator ${wsStatus === 'connected' ? 'realtime' : isPollingPaused ? 'paused' : 'live'}`}>
            {wsStatus === 'connected'
              ? '🟢 Real-time connected'
              : isPollingPaused
                ? 'Paused (tab hidden)'
                : `Live updates every ${pollIntervalMs / 1000}s`}
          </span>
        </div>
      </div>

      {/* Complaint Form Modal */}
      {showComplaintForm && (
        <div className="modal-overlay" onClick={closeComplaintForm}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Report a complaint"
            ref={modalContentRef}
          >
            <button 
              className="modal-close"
              onClick={closeComplaintForm}
              aria-label="Close"
            >
              ×
            </button>
            <ComplaintForm
              onSubmitStart={handleComplaintSubmitStart}
              onSubmitSuccess={handleComplaintSubmitSuccess}
              onSubmitError={handleComplaintSubmitError}
            />
          </div>
        </div>
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`} role="status" aria-live="polite">
          {toast.message}
        </div>
      )}

      <div className="dashboard-grid">
        {/* Map Section - Main visualization area */}
        <section className="dashboard-section map-section">
          <div className="section-header">
            <h2>Risk Map</h2>
            <div className="section-meta">
              <span className="section-badge">{filteredRiskZones.length} zones</span>
              <span className={`section-status ${isStale(riskZonesState) ? 'stale' : ''}`}>
                {riskZonesState.loading && !riskZonesState.lastUpdated
                  ? 'Loading...'
                  : `Updated ${formatRelativeTime(riskZonesState.lastUpdated)}`}
              </span>
            </div>
          </div>
          <div className="section-toolbar">
            <div className="toolbar-group">
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={filters.showClusters}
                  onChange={(event) =>
                    setFilters((prev) => ({ ...prev, showClusters: event.target.checked }))
                  }
                />
                <span>Cluster markers</span>
              </label>
            </div>
            <div className="toolbar-group categories">
              {CATEGORY_OPTIONS.map((option) => (
                <label key={option.value} className="chip-toggle">
                  <input
                    type="checkbox"
                    checked={filters.categoryToggles[option.value]}
                    onChange={(event) =>
                      setFilters((prev) => ({
                        ...prev,
                        categoryToggles: {
                          ...prev.categoryToggles,
                          [option.value]: event.target.checked
                        }
                      }))
                    }
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="section-content">
            {/* MapVisualizer component - Task 15.1 */}
            <MapVisualizer 
              riskZones={filteredRiskZones}
              complaints={openComplaints}
              updateInterval={30000}
              loading={riskZonesState.loading}
              error={riskZonesState.error}
              enableClustering={filters.showClusters}
            />
          </div>
        </section>

        {/* Complaint Feed Section */}
        <section className="dashboard-section feed-section">
          <div className="section-header">
            <h2>Recent Complaints</h2>
            <div className="section-meta">
              <span className="section-badge">{Math.min(20, filteredComplaints.length)}</span>
              <span className={`section-status ${isStale(complaintsState) ? 'stale' : ''}`}>
                {complaintsState.loading && !complaintsState.lastUpdated
                  ? 'Loading...'
                  : `Updated ${formatRelativeTime(complaintsState.lastUpdated)}`}
              </span>
            </div>
          </div>
          <div className="section-content">
            <ComplaintFeed
              complaints={filteredComplaints}
              loading={complaintsState.loading}
              error={complaintsState.error}
              stale={isStale(complaintsState)}
              isAdmin={userIsAdmin}
              onComplaintUpdate={fetchDashboardData}
            />
          </div>
        </section>

        {/* Weather Panel Section */}
        <section className="dashboard-section weather-section">
          <div className="section-header">
            <h2>Weather Conditions</h2>
            <span className={`section-status ${isStale(weatherState) ? 'stale' : ''}`}>
              {weatherState.loading && !weatherState.lastUpdated
                ? 'Loading...'
                : `Updated ${formatRelativeTime(weatherState.lastUpdated)}`}
            </span>
          </div>
          <div className="section-content">
            {/* WeatherPanel component - Task 18.1 */}
            <WeatherPanel
              weather={weatherState.data}
              loading={weatherState.loading}
              error={weatherState.error}
              stale={isStale(weatherState)}
            />
          </div>
        </section>

        {/* Traffic Panel Section */}
        <section className="dashboard-section traffic-section">
          <div className="section-header">
            <h2>Traffic Status</h2>
            <div className="section-meta">
              <span className="section-badge">{trafficState.data.length} locations</span>
              <span className={`section-status ${isStale(trafficState) ? 'stale' : ''}`}>
                {trafficState.loading && !trafficState.lastUpdated
                  ? 'Loading...'
                  : `Updated ${formatRelativeTime(trafficState.lastUpdated)}`}
              </span>
            </div>
          </div>
          <div className="section-content">
            {/* TrafficPanel component - Task 19.1 */}
            <TrafficPanel
              trafficData={trafficState.data}
              loading={trafficState.loading}
              error={trafficState.error}
              stale={isStale(trafficState)}
            />
          </div>
        </section>

        {/* Trend Charts Section */}
        <section className="dashboard-section charts-section">
          <div className="section-header">
            <h2>Trend Analysis</h2>
            <span className={`section-status ${isStale(riskZonesState) || isStale(complaintsState) ? 'stale' : ''}`}>
              {complaintsState.loading && riskZonesState.loading
                ? 'Loading...'
                : `Updated ${formatRelativeTime(complaintsState.lastUpdated || riskZonesState.lastUpdated)}`}
            </span>
          </div>
          <div className="section-content">
            <TrendCharts
              complaints={filteredComplaints}
              riskZones={filteredRiskZones}
              loading={complaintsState.loading || riskZonesState.loading}
            />
          </div>
        </section>

        {/* Predictions Section */}
        {userIsAdmin && (
        <section className="dashboard-section predictions-section">
          <div className="section-header">
            <h2>Incident Predictions</h2>
            <div className="section-meta">
              <span className="section-badge">{predictionsState.data.length} active</span>
              <span className={`section-status ${isStale(predictionsState) ? 'stale' : ''}`}>
                {predictionsState.loading && !predictionsState.lastUpdated
                  ? 'Loading...'
                  : `Updated ${formatRelativeTime(predictionsState.lastUpdated)}`}
              </span>
            </div>
          </div>
          <div className="section-content">
            <PredictionsPanel
              predictions={predictionsState.data}
              loading={predictionsState.loading}
              error={predictionsState.error}
              stale={isStale(predictionsState)}
            />
          </div>
        </section>
        )}

        {/* AI Insights Section */}
        {userIsAdmin && (
        <section className="dashboard-section ai-section">
          <div className="section-header">
            <h2>AI Insights</h2>
            <span className={`section-status ${isStale(dailyReportState) ? 'stale' : ''}`}>
              {dailyReportState.loading && !dailyReportState.lastUpdated
                ? 'Loading...'
                : `Updated ${formatRelativeTime(dailyReportState.lastUpdated)}`}
            </span>
          </div>
          <div className="section-content">
            <AIInsightsPanel
              dailyReport={dailyReportState.data}
              complaints={complaintsState.data}
              loading={dailyReportState.loading}
              error={dailyReportState.error}
              classificationEngine={classificationEngine}
            />
          </div>
        </section>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
