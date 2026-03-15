"""
UrbanGuard AI System - Incident Predictor
Forecasts potential urban incidents based on high-risk zones
"""
import logging
from datetime import datetime
from typing import List, Optional
from models import (
    RiskZone, IncidentPrediction, WeatherData, TrafficData
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncidentPredictor:
    """
    Forecasts potential urban incidents for high-risk zones.
    
    Prediction Logic:
    - Only generates predictions for zones with risk_score > 70
    - Incident type based on dominant complaint category
    - Special rules:
      * High rainfall + flooding complaints → flooding incident
      * High traffic congestion + traffic complaints → gridlock incident
    - Time windows: "next 6 hours" (score > 85) or "next 24 hours" (score 70-85)
    
    Validates: Requirements 9.1, 9.2, 9.3, 9.4
    """
    
    # Risk score threshold for generating predictions
    PREDICTION_THRESHOLD = 25.0
    
    def __init__(self):
        """Initialize Incident Predictor."""
        pass
    
    def predict_incidents(
        self,
        risk_zones: List[RiskZone],
        weather: Optional[WeatherData] = None,
        traffic_data: Optional[dict] = None
    ) -> List[IncidentPrediction]:
        """
        Generates incident predictions for high-risk zones.
        
        Args:
            risk_zones: Zones with calculated risk scores
            weather: Current weather conditions (optional)
            traffic_data: Traffic data dict (location -> TrafficData) (optional)
            
        Returns:
            List of incident predictions with type and time window
            
        Logic:
            - Only predict for zones with risk_score > 70
            - Incident type based on dominant complaint category
            - Special rules:
              * High rainfall + flooding complaints → flooding incident
              * High traffic + traffic complaints → gridlock incident
            - Time windows: next 6 hours or next 24 hours
            
        Validates: Requirements 9.1, 9.2, 9.3, 9.4
        """
        predictions = []
        
        # Filter zones with risk_score > 70
        high_risk_zones = [
            zone for zone in risk_zones
            if zone.risk_score > self.PREDICTION_THRESHOLD
        ]
        
        if not high_risk_zones:
            logger.info("No high-risk zones (score > 25) found for incident prediction")
            return predictions
        
        logger.info(f"Generating predictions for {len(high_risk_zones)} high-risk zones")
        
        for zone in high_risk_zones:
            # Determine incident type
            incident_type = self._determine_incident_type(
                zone,
                weather=weather,
                traffic_data=traffic_data
            )
            
            # Determine time window
            time_window = self._determine_time_window(zone.risk_score)
            
            # Determine contributing factors
            contributing_factors = self._determine_contributing_factors(
                zone,
                weather=weather,
                traffic_data=traffic_data
            )
            
            # Create prediction
            prediction = IncidentPrediction(
                zone_id=zone.zone_id,
                incident_type=incident_type,
                risk_score=zone.risk_score,
                time_window=time_window,
                contributing_factors=contributing_factors,
                created_at=datetime.now()
            )
            
            predictions.append(prediction)
            
            logger.info(
                f"Predicted {incident_type} incident for zone {zone.zone_id} "
                f"(risk_score: {zone.risk_score:.1f}, time_window: {time_window})"
            )
        
        return predictions
    
    def _determine_incident_type(
        self,
        zone: RiskZone,
        weather: Optional[WeatherData] = None,
        traffic_data: Optional[dict] = None
    ) -> str:
        """
        Determines incident type based on zone characteristics.
        
        Args:
            zone: Risk zone to analyze
            weather: Current weather conditions (optional)
            traffic_data: Traffic data dict (optional)
            
        Returns:
            Incident type string
            
        Logic:
            - Special rule: High rainfall + flooding complaints → "flooding"
            - Special rule: High traffic + traffic complaints → "traffic_gridlock"
            - Default: Use dominant complaint category
            
        Validates: Requirements 9.2, 9.3, 9.4
        """
        # Special rule: Flooding incident prediction
        # High rainfall + flooding complaints → flooding incident
        if weather and weather.high_rainfall_flag:
            if zone.dominant_category == "flooding":
                logger.debug(
                    f"Zone {zone.zone_id}: High rainfall + flooding complaints "
                    f"→ flooding incident"
                )
                return "flooding"
        
        # Special rule: Traffic gridlock prediction
        # High traffic congestion + traffic complaints → gridlock incident
        if traffic_data and zone.dominant_category == "traffic":
            # Check if any location in the zone has high traffic
            # Since we don't have location info in RiskZone, we check if
            # any traffic data shows high congestion (score = 10)
            has_high_traffic = any(
                traffic.congestion_score == 10
                for traffic in traffic_data.values()
            )
            
            if has_high_traffic:
                logger.debug(
                    f"Zone {zone.zone_id}: High traffic + traffic complaints "
                    f"→ traffic gridlock incident"
                )
                return "traffic_gridlock"
        
        # Default: Use dominant complaint category
        # Map category to incident type
        incident_type = self._map_category_to_incident_type(zone.dominant_category)
        
        logger.debug(
            f"Zone {zone.zone_id}: Dominant category '{zone.dominant_category}' "
            f"→ {incident_type} incident"
        )
        
        return incident_type
    
    def _map_category_to_incident_type(self, category: str) -> str:
        """
        Maps complaint category to incident type.
        
        Args:
            category: Complaint category
            
        Returns:
            Incident type string
        """
        # Map categories to incident types
        category_mapping = {
            "pothole": "road_damage",
            "flooding": "flooding",
            "traffic": "traffic_congestion",
            "garbage": "waste_accumulation",
            "streetlight": "lighting_failure",
            "water_supply": "water_shortage",
            "noise": "noise_pollution",
            "construction": "construction_hazard",
            "mixed": "infrastructure_issue"
        }
        
        return category_mapping.get(category, "infrastructure_issue")
    
    def _determine_time_window(self, risk_score: float) -> str:
        """
        Determines prediction time window based on risk score.
        
        - "next 6 hours" for risk_score > 85
        - "next 24 hours" for risk_score 70-85
        - "next 48 hours" for lower scores
        """
        if risk_score > 85:
            return "next 6 hours"
        elif risk_score > 60:
            return "next 24 hours"
        else:
            return "next 48 hours"
    
    def _determine_contributing_factors(
        self,
        zone: RiskZone,
        weather: Optional[WeatherData] = None,
        traffic_data: Optional[dict] = None
    ) -> List[str]:
        """
        Determines contributing factors for the prediction.
        
        Args:
            zone: Risk zone to analyze
            weather: Current weather conditions (optional)
            traffic_data: Traffic data dict (optional)
            
        Returns:
            List of contributing factor strings
        """
        factors = []
        
        # Always include complaint density as a factor
        factors.append("high_complaint_density")
        
        # Check for weather factors
        if weather:
            if weather.high_rainfall_flag:
                factors.append("high_rainfall")
            
            if weather.wind_speed_kmh > 40:
                factors.append("high_wind")
        
        # Check for traffic factors
        if traffic_data:
            has_high_traffic = any(
                traffic.congestion_score == 10
                for traffic in traffic_data.values()
            )
            
            if has_high_traffic:
                factors.append("high_traffic_congestion")
        
        # Add dominant category as a factor
        factors.append(f"{zone.dominant_category}_complaints")
        
        return factors


# Global incident predictor instance
_incident_predictor: Optional[IncidentPredictor] = None


def get_incident_predictor() -> IncidentPredictor:
    """
    Gets or creates the global IncidentPredictor instance.
    
    Returns:
        IncidentPredictor singleton instance
    """
    global _incident_predictor
    
    if _incident_predictor is None:
        _incident_predictor = IncidentPredictor()
    
    return _incident_predictor
