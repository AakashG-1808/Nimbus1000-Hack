import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
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

  // Get all complaints
  getAllComplaints: () => {
    return api.get('/complaints');
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

export default api;
