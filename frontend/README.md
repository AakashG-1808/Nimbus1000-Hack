# UrbanGuard AI Frontend

React-based frontend for the UrbanGuard AI urban infrastructure risk prediction system.

## Project Structure

```
frontend/
├── public/              # Static assets
│   └── index.html      # HTML template
├── src/
│   ├── components/     # React components (Dashboard, Map, Charts, etc.)
│   ├── services/       # API client and service layer
│   │   └── api.js     # Axios-based API client
│   ├── utils/          # Utility functions
│   ├── App.js          # Main application component with routing
│   ├── App.css         # Application styles
│   ├── index.js        # Application entry point
│   └── index.css       # Global styles
├── .env                # Environment variables (API URL, map config)
├── .env.example        # Environment variables template
└── package.json        # Dependencies and scripts
```

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env if needed (default: backend on localhost:8000)
```

3. Start development server:
```bash
npm start
```

The app will run on http://localhost:3000

## API Client

The API client is configured in `src/services/api.js` and provides:

- **complaintsAPI**: Submit and retrieve complaints
- **riskAPI**: Get risk hotspots
- **reportsAPI**: Get daily reports
- **weatherAPI**: Get weather data
- **trafficAPI**: Get traffic data

All API calls use the base URL from `REACT_APP_API_URL` environment variable.

## Available Scripts

- `npm start` - Start development server (port 3000)
- `npm build` - Create production build
- `npm test` - Run tests
- `npm eject` - Eject from Create React App (one-way operation)

## Dependencies

- **React 18.2** - UI framework
- **React Router DOM 6** - Client-side routing
- **Axios** - HTTP client for API communication
- **Leaflet.js** - Interactive maps
- **Chart.js** - Data visualizations
- **fast-check** - Property-based testing

## Backend Communication

The frontend communicates with the FastAPI backend running on port 8000. CORS is configured on the backend to allow requests from http://localhost:3000.

## Next Steps

Task 14.2 will implement the main Dashboard component with:
- Grid layout for map, complaint feed, weather panel, traffic panel, and trend charts
- 30-second polling for real-time updates
