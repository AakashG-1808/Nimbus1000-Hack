import axios from 'axios';
import { getToken, logout } from './auth';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: (process.env.REACT_APP_API_URL || 'http://localhost:8000') + '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging and auth
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error Response:', error.response.status, error.response.data);
      if (error.response.status === 401) {
        logout();
        window.location.href = '/login';
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('API No Response:', error.request);
    } else {
      // Error in request setup
      console.error('API Request Setup Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const complaintsAPI = {
  // Submit a new complaint
  submitComplaint: (complaintData) => {
    return api.post('/report-complaint', complaintData);
  },

  // Get complaints with optional filters
  getComplaints: (params = {}) => {
    return api.get('/complaints', { params });
  },

  // Get all complaints (legacy helper)
  getAllComplaints: () => {
    return api.get('/complaints');
  },

  // Admin: resolve / update a complaint
  resolveComplaint: (complaintId, data) => {
    return api.patch(`/complaints/${complaintId}/resolve`, data);
  },

  // Admin: upload image to S3, returns { url }
  uploadImage: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/upload-image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
  },
};

export const riskAPI = {
  // Get risk hotspots
  getRiskHotspots: () => {
    return api.get('/risk-hotspots');
  },
};

export const reportsAPI = {
  // Get daily report
  getDailyReport: () => {
    return api.get('/daily-report');
  },
};

export const weatherAPI = {
  // Get current weather data
  getWeather: () => {
    return api.get('/weather');
  },
};

export const trafficAPI = {
  // Get traffic data
  getTraffic: () => {
    return api.get('/traffic');
  },
};

export const predictionsAPI = {
  // Get incident predictions
  getPredictions: () => {
    return api.get('/predictions');
  },
};

// WebSocket service for real-time updates
export const websocketAPI = (() => {
  let ws = null;
  let messageCallbacks = [];
  let statusCallbacks = [];
  let reconnectTimer = null;
  let reconnectDelay = 1000;
  const MAX_RECONNECT_DELAY = 30000;
  let intentionalClose = false;

  const getWsUrl = () => {
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    return baseUrl.replace(/^http/, 'ws') + '/ws';
  };

  const notifyStatus = (status) => {
    statusCallbacks.forEach(cb => {
      try { cb(status); } catch (e) { console.error('WS status callback error:', e); }
    });
  };

  const connect = () => {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    intentionalClose = false;
    const url = getWsUrl();
    console.log('WebSocket connecting to:', url);

    try {
      ws = new WebSocket(url);
    } catch (e) {
      console.error('WebSocket creation failed:', e);
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      console.log('WebSocket connected');
      reconnectDelay = 1000; // Reset backoff
      notifyStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        messageCallbacks.forEach(cb => {
          try { cb(data); } catch (e) { console.error('WS message callback error:', e); }
        });
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      notifyStatus('disconnected');
      if (!intentionalClose) {
        scheduleReconnect();
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const scheduleReconnect = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    console.log(`WebSocket reconnecting in ${reconnectDelay / 1000}s...`);
    reconnectTimer = setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
      connect();
    }, reconnectDelay);
  };

  const disconnect = () => {
    intentionalClose = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (ws) {
      ws.close();
      ws = null;
    }
    notifyStatus('disconnected');
  };

  const onMessage = (callback) => {
    messageCallbacks.push(callback);
    return () => {
      messageCallbacks = messageCallbacks.filter(cb => cb !== callback);
    };
  };

  const onStatusChange = (callback) => {
    statusCallbacks.push(callback);
    return () => {
      statusCallbacks = statusCallbacks.filter(cb => cb !== callback);
    };
  };

  return { connect, disconnect, onMessage, onStatusChange };
})();

export default api;

