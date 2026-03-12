# UrbanGuard AI System

Urban infrastructure risk prediction platform that transforms citizen complaints into actionable insights for city authorities.

## Project Structure

```
urbanguard-ai-system/
├── backend/              # Python FastAPI backend
│   ├── main.py          # Application entry point
│   ├── requirements.txt # Python dependencies
│   ├── .env.example     # Environment variables template
│   └── .gitignore       # Git ignore rules
├── frontend/            # React frontend
│   ├── public/          # Static files
│   ├── src/             # React components
│   ├── package.json     # Node dependencies
│   ├── .env.example     # Environment variables template
│   └── .gitignore       # Git ignore rules
└── README.md            # This file
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create `.env` file from template:
   ```bash
   cp .env.example .env
   ```

6. Edit `.env` and add your API keys:
   - OpenWeatherMap API key
   - AWS credentials for Bedrock

7. Run the development server:
   ```bash
   python main.py
   ```

   The API will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create `.env` file from template:
   ```bash
   cp .env.example .env
   ```

4. Start the development server:
   ```bash
   npm start
   ```

   The application will open at http://localhost:3000

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server with hot-reload
- **Boto3**: AWS SDK for Bedrock integration
- **Requests**: HTTP library for OpenWeatherMap API
- **Hypothesis**: Property-based testing framework
- **Pytest**: Testing framework

### Frontend
- **React**: UI library
- **Leaflet.js**: Interactive maps
- **Chart.js**: Data visualizations
- **Axios**: HTTP client
- **fast-check**: Property-based testing framework

## API Endpoints

- `GET /` - API health check
- `POST /report-complaint` - Submit citizen complaint
- `GET /complaints` - Retrieve all complaints
- `GET /risk-hotspots` - Get high-risk zones
- `GET /daily-report` - Get latest daily report
- `GET /weather` - Get current weather data
- `GET /traffic` - Get traffic congestion data

## Development

- Backend runs on port 8000 with hot-reload enabled
- Frontend runs on port 3000 with hot-reload enabled
- CORS is configured to allow frontend access from port 3000

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

The system is designed for AWS serverless deployment:
- Backend: AWS Lambda + API Gateway
- Database: DynamoDB
- AI: Amazon Bedrock
- Monitoring: CloudWatch

See deployment documentation for detailed instructions.
