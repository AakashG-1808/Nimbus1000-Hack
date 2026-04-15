# Implementation Plan: UrbanGuard AI System

## Overview

This implementation plan breaks down the UrbanGuard AI system into discrete coding tasks. The system consists of a Python FastAPI backend with 8 core components, a React frontend with Leaflet.js mapping and Chart.js visualizations, Amazon Bedrock AI integration with keyword fallback, and integration with OpenWeatherMap API and simulated traffic data.

The implementation follows an incremental approach: project setup → backend components → API endpoints → frontend components → integration → property-based testing. Each task builds on previous work, with checkpoints to validate progress.

## Tasks

- [ ] 1. Project setup and initialization
  - [x] 1.1 Create project directory structure and configuration files
    - Create backend directory with FastAPI project structure
    - Create frontend directory with React project structure
    - Set up Python virtual environment and requirements.txt
    - Set up package.json with React, Leaflet.js, Chart.js dependencies
    - Create .env files for API keys (OpenWeatherMap, AWS Bedrock)
    - _Requirements: 18.1, 18.2, 18.3_

  - [x] 1.2 Initialize Bengaluru location data and complaint categories
    - Create constants.py with 40+ Bengaluru locations and coordinates
    - Define 8 complaint categories (pothole, flooding, traffic, garbage, streetlight, water_supply, noise, construction)
    - Create data models for Complaint, RiskZone, WeatherData, TrafficData, IncidentPrediction, DailyReport
    - _Requirements: 1.2, 1.3_

  - [x] 1.3 Set up in-memory data storage and initialize with simulated complaints
    - Create in-memory storage classes for complaints, risk zones, reports
    - Generate 40+ simulated complaints across Bengaluru locations
    - Initialize storage with simulated data for local development
    - _Requirements: 18.4_

- [ ] 2. Implement Complaint_Processor component
  - [x] 2.1 Implement complaint validation logic
    - Write location validation against Bengaluru locations
    - Write category validation against 8 supported types
    - Write required field validation (location, category, description, timestamp)
    - Implement error message generation for validation failures
    - _Requirements: 1.2, 1.3, 1.4_

  - [x] 2.2 Write property tests for complaint validation
    - **Property 2: Location Validation** - Invalid locations should be rejected
    - **Property 3: Category Validation** - Invalid categories should be rejected
    - **Property 4: Invalid Complaint Error Response** - Invalid data returns descriptive errors
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [x] 2.3 Implement complaint submission and storage
    - Write submit_complaint method with validation and storage
    - Generate unique complaint IDs (UUID)
    - Store complaints with coordinates lookup from location
    - Return success confirmation within 500ms
    - _Requirements: 1.5_

  - [x] 2.4 Write property test for complaint storage round-trip
    - **Property 5: Valid Complaint Storage Round-Trip** - Submitted complaints should be retrievable
    - **Validates: Requirements 1.5**

  - [x] 2.5 Implement complaint retrieval with sorting
    - Write get_all_complaints method
    - Sort complaints by timestamp descending
    - Include coordinates with each complaint
    - Optimize for < 200ms response time for 1000 complaints
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 2.6 Write property tests for complaint retrieval
    - **Property 9: Complaint Retrieval Sorting** - Complaints sorted by timestamp descending
    - **Property 10: Complaint Response Completeness** - Coordinates included with complaints
    - **Validates: Requirements 3.2, 3.4**

- [ ] 3. Implement AI_Classifier component
  - [x] 3.1 Implement keyword-based fallback classification
    - Create keyword mapping for 8 categories
    - Write keyword matching logic with confidence scoring
    - Ensure always returns exactly one category
    - _Requirements: 2.2, 2.3_

  - [x] 3.2 Implement Amazon Bedrock integration with fallback
    - Write Bedrock API client with boto3
    - Create classification prompt for 8 categories
    - Implement timeout handling (3 seconds)
    - Implement fallback to keyword classification on Bedrock failure
    - Add circuit breaker pattern for Bedrock calls
    - _Requirements: 2.1, 2.2, 2.4_

  - [x] 3.3 Write property tests for AI classification
    - **Property 6: AI Classification Attempts Bedrock First** - Bedrock attempted before fallback
    - **Property 7: Classification Fallback on Bedrock Failure** - Fallback returns valid category
    - **Property 8: Single Category Assignment** - Exactly one category assigned
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [ ] 4. Implement Weather_Integrator component
  - [x] 4.1 Implement OpenWeatherMap API integration
    - Write OpenWeatherMap API client with requests library
    - Extract temperature, humidity, precipitation, wind speed
    - Implement 30-minute fetch interval with background scheduler
    - Implement caching mechanism for weather data
    - _Requirements: 5.1, 5.2_

  - [x] 4.2 Implement weather data fallback and high rainfall detection
    - Implement fallback to cached data on API failure
    - Add warning logging for API failures
    - Implement high rainfall flagging (> 10mm/hr)
    - Provide weather data within 100ms from cache
    - _Requirements: 5.3, 5.4, 5.5_

  - [x] 4.3 Write property tests for weather integration
    - **Property 14: Weather Data Extraction Completeness** - All fields extracted
    - **Property 15: Weather Data Fallback on API Failure** - Cached data returned on failure
    - **Property 16: High Rainfall Flagging** - Precipitation > 10mm/hr flagged
    - **Validates: Requirements 5.2, 5.3, 5.5**

- [ ] 5. Implement Traffic_Analyzer component
  - [x] 5.1 Implement simulated traffic data generation
    - Create traffic data generator for all Bengaluru locations
    - Implement congestion level assignment (LOW, MEDIUM, HIGH)
    - Implement congestion score mapping (low=1, medium=5, high=10)
    - Update traffic data every 10 minutes with background scheduler
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 5.2 Implement traffic data retrieval
    - Write get_traffic_data method for specific locations
    - Provide traffic data within 50ms
    - Return congestion level and score
    - _Requirements: 6.4_

  - [x] 5.3 Write property tests for traffic analysis
    - **Property 17: Traffic Congestion Processing** - All locations have congestion levels
    - **Property 18: Congestion Score Mapping** - Scores match mapping (low=1, medium=5, high=10)
    - **Validates: Requirements 6.1, 6.3**

- [ ] 6. Implement Cluster_Detector component
  - [x] 6.1 Implement geographic clustering algorithm
    - Implement Haversine distance calculation for coordinates
    - Group complaints within 500m radius
    - Calculate cluster center coordinates
    - Filter complaints by 24-hour time window
    - _Requirements: 4.1_

  - [x] 6.2 Implement density calculation and high-density flagging
    - Calculate complaints per square kilometer for each cluster
    - Flag clusters with 5+ complaints in 24h as high-density
    - Implement 15-minute recalculation scheduler
    - _Requirements: 4.2, 4.3, 4.4_

  - [x] 6.3 Write property tests for cluster detection
    - **Property 11: Geographic Clustering** - Complaints within 500m grouped together
    - **Property 12: Density Calculation Correctness** - Density accurately calculated
    - **Property 13: High-Density Cluster Flagging** - 5+ complaints flagged as high-density
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [ ] 7. Implement Risk_Engine component
  - [x] 7.1 Implement base risk score calculation
    - Calculate base score from complaint density
    - Implement complaint density threshold logic (5+ per km² → +20 points)
    - Ensure risk scores bounded 0-100
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 7.2 Implement weather and traffic modifiers
    - Add weather modifier for high rainfall + flood complaints (+30 points)
    - Add traffic modifier for high congestion + traffic complaints (+15 points)
    - Integrate Weather_Integrator and Traffic_Analyzer data
    - Cap final risk score at 100
    - _Requirements: 7.4, 7.5_

  - [x] 7.3 Implement risk level classification and zone filtering
    - Classify risk levels: LOW (0-33), MEDIUM (34-66), HIGH (67-100)
    - Implement 15-minute recalculation scheduler
    - Filter zones with risk_score > 20 for API responses
    - _Requirements: 7.6, 8.1, 8.2_

  - [x] 7.4 Write property tests for risk calculation
    - **Property 19: Risk Score Calculation Uses All Factors** - All three factors influence score
    - **Property 20: Risk Score Bounds** - Scores between 0-100
    - **Property 21: High Complaint Density Score Increase** - Density > 5 adds 20+ points
    - **Property 22: High Rainfall Flood Risk Increase** - High rainfall + floods adds 30+ points
    - **Property 23: High Traffic Congestion Risk Increase** - High traffic + complaints adds 15+ points
    - **Property 24: Risk Level Classification** - Correct classification by score ranges
    - **Property 25: Risk Zone Filtering** - Only zones with score > 20 returned
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2**

- [ ] 8. Implement Incident_Predictor component
  - [x] 8.1 Implement incident prediction logic
    - Generate predictions for zones with risk_score > 70
    - Determine incident type from dominant complaint category
    - Implement special rules for flooding (high rainfall + flood complaints)
    - Implement special rules for gridlock (high traffic + traffic complaints)
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 8.2 Implement time window determination
    - Assign "next 6 hours" for risk_score > 85
    - Assign "next 24 hours" for risk_score 70-85
    - Include contributing factors in predictions
    - _Requirements: 9.5_

  - [x] 8.3 Write property tests for incident prediction
    - **Property 27: Incident Prediction for High-Risk Zones** - Predictions for score > 70
    - **Property 28: Incident Type Matches Dominant Category** - Type matches dominant category
    - **Property 29: Flooding Incident Prediction** - High rainfall + floods predicts flooding
    - **Property 30: Traffic Gridlock Prediction** - High traffic + complaints predicts gridlock
    - **Property 31: Incident Prediction Time Window Inclusion** - Time window included
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

- [ ] 9. Implement Report_Generator component
  - [x] 9.1 Implement daily report generation
    - Create daily report at 06:00 local time with scheduler
    - Aggregate total complaints count
    - Collect high-risk zones list
    - Collect predicted incidents
    - Generate weather summary
    - _Requirements: 10.1, 10.2_

  - [x] 9.2 Implement AI-generated summary with Bedrock
    - Use Amazon Bedrock to generate natural language risk pattern summary
    - Include risk trends and patterns in summary
    - Implement fallback summary generation if Bedrock unavailable
    - _Requirements: 10.3_

  - [x] 9.3 Implement report storage and retrieval
    - Store reports with 30-day retention
    - Implement get_latest_report method
    - Return reports within 200ms
    - _Requirements: 10.4, 10.5_

  - [x] 9.4 Write property tests for report generation
    - **Property 32: Daily Report Completeness** - All required fields included
    - **Property 33: AI Summary Generation** - AI generates natural language summary
    - **Validates: Requirements 10.2, 10.3**

- [x] 10. Checkpoint - Backend components complete
  - Ensure all backend components implemented and unit tests pass
  - Verify background schedulers working (15-minute risk updates, 30-minute weather, 10-minute traffic)
  - Test component integration (complaints → classification → clustering → risk calculation)
  - Ask the user if questions arise

- [ ] 11. Implement Dashboard_API endpoints
  - [x] 11.1 Create FastAPI application with CORS middleware
    - Initialize FastAPI app on port 8000
    - Configure CORS for http://localhost:3000
    - Set up Uvicorn with hot-reload for development
    - Add request logging middleware
    - _Requirements: 17.8, 18.1, 18.5_

  - [x] 11.2 Implement complaint endpoints
    - POST /report-complaint endpoint with validation
    - GET /complaints endpoint with sorting
    - Return JSON responses with appropriate HTTP status codes
    - Implement error handling with descriptive messages
    - _Requirements: 17.1, 17.2, 17.7_

  - [x] 11.3 Write property tests for complaint endpoints
    - **Property 1: Complaint Structure Acceptance** - Valid complaints accepted
    - **Property 45: API JSON Response Format** - JSON with HTTP status codes
    - **Validates: Requirements 1.1, 17.7**

  - [x] 11.4 Implement risk and contextual data endpoints
    - GET /risk-hotspots endpoint with filtering (score > 20)
    - GET /weather endpoint with current conditions
    - GET /traffic endpoint with congestion data
    - Optimize response times (< 100ms, < 200ms, < 300ms per requirement)
    - _Requirements: 17.3, 17.5, 17.6, 8.3, 8.4_

  - [x] 11.5 Write property test for risk zone response
    - **Property 26: Risk Zone Response Completeness** - Coordinates, score, level included
    - **Validates: Requirements 8.3**

  - [x] 11.6 Implement daily report endpoint
    - GET /daily-report endpoint
    - Return most recent report within 200ms
    - Handle case when no report exists
    - _Requirements: 17.4_

- [ ] 12. Implement error handling and logging
  - [x] 12.1 Implement comprehensive error handling
    - Add input validation error handlers (400 Bad Request)
    - Add external API failure handlers with retry logic (3 attempts, exponential backoff)
    - Add database error handlers (500 Internal Server Error)
    - Implement graceful error responses after retry exhaustion
    - _Requirements: 20.2, 20.3_

  - [x] 12.2 Implement logging system
    - Add error logging with timestamp, component name, error details
    - Add request logging with method, path, response time
    - Configure log levels (ERROR, WARN, INFO, DEBUG)
    - Format logs as JSON for structured logging
    - _Requirements: 20.1, 20.4, 20.5_

  - [x] 12.3 Write property tests for error handling
    - **Property 46: Error Logging Completeness** - Errors logged with required fields
    - **Property 47: External API Retry Behavior** - 3 retries with exponential backoff
    - **Property 48: Graceful Error Response After Retries** - Graceful response after failures
    - **Property 49: Request Logging Completeness** - Requests logged with method, path, time
    - **Property 50: Error Response Format** - HTTP status code and descriptive message
    - **Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5**

- [x] 13. Checkpoint - Backend API complete
  - Ensure all API endpoints functional and returning correct data
  - Test error handling with invalid inputs and simulated failures
  - Verify CORS configuration allows frontend access
  - Verify logging captures all required information
  - Ask the user if questions arise

- [ ] 14. Implement React frontend foundation
  - [x] 14.1 Create React app structure and routing
    - Initialize React app with Create React App or Vite
    - Set up component directory structure
    - Configure API client with axios for backend communication
    - Set up environment variables for API base URL
    - _Requirements: 18.2_

  - [x] 14.2 Create main Dashboard component layout
    - Create Dashboard component with grid layout
    - Add sections for map, complaint feed, weather panel, traffic panel, trend charts
    - Implement 30-second polling for real-time updates
    - _Requirements: 12.1, 12.2_

- [ ] 15. Implement Map_Visualizer component
  - [x] 15.1 Implement Leaflet.js map with Bengaluru view
    - Initialize Leaflet map centered on Bengaluru
    - Configure map tiles and zoom levels
    - Set up map container with responsive sizing
    - _Requirements: 11.1_

  - [x] 15.2 Implement risk zone visualization
    - Render risk zones as colored polygons/circles
    - Apply color coding: green (0-33), yellow (34-66), red (67-100)
    - Implement zone click handler to display details
    - Show risk_score and complaint count in popup
    - _Requirements: 11.2, 11.3_

  - [x] 15.3 Write property tests for risk zone visualization
    - **Property 34: Risk Zone Color Coding** - Correct colors for risk levels
    - **Validates: Requirements 11.2**

  - [x] 15.4 Implement complaint marker display
    - Render complaint locations as map markers
    - Add marker icons for different complaint categories
    - Implement marker click handler to show complaint details
    - Update markers every 30 seconds with new data
    - _Requirements: 11.4, 11.5_

  - [x] 15.5 Write property test for complaint markers
    - **Property 35: Complaint Marker Display** - All complaints shown as markers
    - **Validates: Requirements 11.4**

- [ ] 16. Implement ComplaintFeed component
  - [x] 16.1 Create complaint feed display
    - Display 20 most recent complaints in chronological order
    - Show location, category, description, timestamp for each
    - Implement auto-scroll for new complaints
    - Add new complaints to top of feed within 5 seconds
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [x] 16.2 Write property tests for complaint feed
    - **Property 36: Recent Complaints Feed Selection** - 20 most recent shown
    - **Property 37: Complaint Feed Display Completeness** - All fields displayed
    - **Validates: Requirements 13.1, 13.3**

- [ ] 17. Implement TrendCharts component
  - [x] 17.1 Implement Chart.js visualizations
    - Create 7-day complaint volume trend chart
    - Create risk score trend chart for top 5 high-risk zones
    - Configure chart styling and responsive sizing
    - Update charts every 5 minutes
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [x] 17.2 Write property tests for trend charts
    - **Property 38: Seven-Day Complaint Volume Trend** - 7 days of data shown
    - **Property 39: Top Five Risk Zone Trends** - Top 5 zones identified and displayed
    - **Validates: Requirements 14.2, 14.3**

- [ ] 18. Implement WeatherPanel component
  - [x] 18.1 Create weather display panel
    - Display temperature, humidity, precipitation, wind speed
    - Show weather icons for current conditions
    - Highlight panel in red when high rainfall detected
    - Update display every 30 minutes
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 18.2 Write property tests for weather panel
    - **Property 40: Weather Display Completeness** - All weather fields shown
    - **Property 41: High Rainfall Weather Panel Highlighting** - Red highlight for high rainfall
    - **Property 42: Weather Icon Selection** - Icons match conditions
    - **Validates: Requirements 15.1, 15.3, 15.4**

- [ ] 19. Implement TrafficPanel component
  - [x] 19.1 Create traffic display panel
    - Display traffic congestion for 10+ key Bengaluru locations
    - Apply color coding: green (low), yellow (medium), red (high)
    - Update display every 10 minutes
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 19.2 Write property test for traffic panel
    - **Property 43: Traffic Location Display** - Major locations shown
    - **Property 44: Traffic Congestion Color Coding** - Correct colors for levels
    - **Validates: Requirements 16.1, 16.2**

- [x] 20. Checkpoint - Frontend components complete
  - Ensure all frontend components render correctly with test data
  - Verify real-time updates working (30-second polling)
  - Test responsive design on different screen sizes
  - Verify all visualizations (map, charts, panels) functional
  - Ask the user if questions arise

- [x] 21. Integration and end-to-end testing
  - [x] 21.1 Implement complaint submission flow
    - Create complaint submission form in React
    - Connect form to POST /report-complaint endpoint
    - Display success/error messages to user
    - Update map and feed with new complaint within 5 seconds
    - _Requirements: 1.1, 12.2_

  - [x] 21.2 Test real-time dashboard updates
    - Verify new complaints appear in feed within 5 seconds
    - Verify risk zone colors update within 10 seconds of score changes
    - Test with multiple simulated complaints
    - _Requirements: 12.2, 12.3_

  - [x] 21.3 Test performance requirements
    - Verify API response times meet requirements (< 100ms, < 200ms, < 300ms, < 500ms)
    - Test with 1000+ complaints
    - Simulate 100 concurrent users (if load testing tools available)
    - _Requirements: 1.4, 1.5, 3.3, 5.4, 6.4, 8.4, 10.4, 12.4_

- [ ] 22. AWS deployment preparation
  - [x] 22.1 Configure AWS Lambda compatibility
    - Add Lambda handler wrapper for FastAPI
    - Configure environment variables for AWS services
    - Add DynamoDB client code (with in-memory fallback for local dev)
    - Test Lambda cold start performance
    - _Requirements: 19.1, 19.3, 19.4, 19.5_

  - [x] 22.2 Create deployment configuration files
    - Create AWS SAM or Serverless Framework configuration
    - Configure API Gateway integration
    - Set up DynamoDB table definitions
    - Add CloudWatch logging configuration
    - _Requirements: 19.2_

- [x] 23. Final checkpoint and documentation
  - Ensure all tests pass (unit tests and property-based tests)
  - Verify system runs locally on ports 8000 (backend) and 3000 (frontend)
  - Test all 20 requirements with acceptance criteria
  - Verify all 50 correctness properties validated
  - Create README with setup and run instructions
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Checkpoints ensure incremental validation at major milestones
- Background schedulers run automatically: 15-minute risk updates, 30-minute weather fetches, 10-minute traffic updates
- Local development uses in-memory storage; AWS deployment uses DynamoDB
- All property-based tests should run with minimum 100 iterations using Hypothesis (Python) or fast-check (TypeScript)
