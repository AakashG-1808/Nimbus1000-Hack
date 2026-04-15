"""
UrbanGuard AI System - Report Generator
Creates daily AI-generated civic risk reports
"""
import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from threading import Thread, Lock
from models import (
    DailyReport, RiskZone, IncidentPrediction, WeatherData
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Creates daily AI-generated civic risk reports.
    
    Features:
    - Generates reports at 06:00 local time with scheduler
    - Aggregates total complaints, high-risk zones, predicted incidents
    - Creates weather summary
    - Uses AI (Amazon Bedrock) to generate natural language risk pattern analysis
    - Stores reports with 30-day retention
    - Provides reports within 200ms
    
    Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
    """
    
    # Report generation time: 06:00 local time
    REPORT_GENERATION_HOUR = 6
    REPORT_GENERATION_MINUTE = 0
    
    # Report retention: 30 days
    REPORT_RETENTION_DAYS = 30
    
    def __init__(
        self,
        auto_start: bool = False,
        get_complaints_callback: Optional[Callable[[], List]] = None,
        get_risk_zones_callback: Optional[Callable[[], List[RiskZone]]] = None,
        get_predictions_callback: Optional[Callable[[], List[IncidentPrediction]]] = None,
        get_weather_callback: Optional[Callable[[], WeatherData]] = None,
        generate_ai_summary_callback: Optional[Callable[[dict], str]] = None
    ):
        """
        Initialize Report Generator.
        
        Args:
            auto_start: Whether to start background scheduler automatically
            get_complaints_callback: Callback to retrieve all complaints
            get_risk_zones_callback: Callback to retrieve risk zones
            get_predictions_callback: Callback to retrieve incident predictions
            get_weather_callback: Callback to retrieve weather data
            generate_ai_summary_callback: Callback to generate AI summary (Bedrock)
        """
        self.get_complaints_callback = get_complaints_callback
        self.get_risk_zones_callback = get_risk_zones_callback
        self.get_predictions_callback = get_predictions_callback
        self.get_weather_callback = get_weather_callback
        self.generate_ai_summary_callback = generate_ai_summary_callback
        
        # Storage for reports (in-memory for local dev, DynamoDB for production)
        self._reports: List[DailyReport] = []
        self._reports_lock = Lock()
        
        # Background scheduler state
        self._scheduler_thread: Optional[Thread] = None
        self._scheduler_running = False
        self._last_report_date: Optional[datetime] = None
        
        if auto_start:
            self.start_scheduler()
    
    def generate_daily_report(
        self,
        date: Optional[datetime] = None
    ) -> DailyReport:
        """
        Creates daily report at 06:00 local time.
        
        Args:
            date: Report date (defaults to today)
            
        Returns:
            DailyReport with statistics and AI-generated summary
            
        Content:
            - Total complaints count
            - High-risk zones list
            - Predicted incidents
            - Weather summary
            - AI-generated natural language risk pattern analysis
            
        Validates: Requirements 10.1, 10.2, 10.3
        """
        if date is None:
            date = datetime.now()
        
        logger.info(f"Generating daily report for {date.strftime('%Y-%m-%d')}")
        
        # Aggregate total complaints count
        total_complaints = 0
        if self.get_complaints_callback:
            try:
                complaints = self.get_complaints_callback()
                total_complaints = len(complaints)
            except Exception as e:
                logger.error(f"Failed to get complaints count: {e}")
        
        # Collect high-risk zones list
        high_risk_zones = []
        if self.get_risk_zones_callback:
            try:
                all_zones = self.get_risk_zones_callback()
                # Filter for high-risk zones (score > 66)
                high_risk_zones = [
                    zone for zone in all_zones
                    if zone.risk_score > 66
                ]
            except Exception as e:
                logger.error(f"Failed to get risk zones: {e}")
        
        # Collect predicted incidents
        predicted_incidents = []
        if self.get_predictions_callback:
            try:
                predicted_incidents = self.get_predictions_callback()
            except Exception as e:
                logger.error(f"Failed to get predictions: {e}")
        
        # Generate weather summary
        weather_summary = self._generate_weather_summary()
        
        # Generate AI summary
        ai_summary = self._generate_ai_summary(
            total_complaints=total_complaints,
            high_risk_zones=high_risk_zones,
            predicted_incidents=predicted_incidents,
            weather_summary=weather_summary
        )
        
        # Create report
        report = DailyReport(
            date=date,
            total_complaints=total_complaints,
            high_risk_zones=high_risk_zones,
            predicted_incidents=predicted_incidents,
            weather_summary=weather_summary,
            ai_generated_summary=ai_summary,
            created_at=datetime.now()
        )
        
        # Store report
        self._store_report(report)
        
        logger.info(
            f"Daily report generated: {total_complaints} complaints, "
            f"{len(high_risk_zones)} high-risk zones, "
            f"{len(predicted_incidents)} predictions"
        )
        
        return report
    
    def _generate_weather_summary(self) -> str:
        """
        Generates weather summary text.
        
        Returns:
            Weather summary string
        """
        if not self.get_weather_callback:
            return "Weather data unavailable"
        
        try:
            weather = self.get_weather_callback()
            
            # Create summary
            summary_parts = [
                f"Temperature: {weather.temperature_celsius:.1f}°C",
                f"Humidity: {weather.humidity_percent:.0f}%",
                f"Precipitation: {weather.precipitation_mm_per_hour:.1f}mm/hr",
                f"Wind: {weather.wind_speed_kmh:.1f}km/h"
            ]
            
            if weather.high_rainfall_flag:
                summary_parts.append("⚠️ High rainfall conditions")
            
            return ", ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate weather summary: {e}")
            return "Weather data unavailable"
    
    def _generate_ai_summary(
        self,
        total_complaints: int,
        high_risk_zones: List[RiskZone],
        predicted_incidents: List[IncidentPrediction],
        weather_summary: str
    ) -> str:
        """
        Generates AI-powered natural language risk pattern summary.
        
        Args:
            total_complaints: Total complaint count
            high_risk_zones: List of high-risk zones
            predicted_incidents: List of incident predictions
            weather_summary: Weather summary text
            
        Returns:
            AI-generated summary string
            
        Validates: Requirement 10.3
        """
        # Prepare context for AI
        context = {
            "total_complaints": total_complaints,
            "high_risk_zone_count": len(high_risk_zones),
            "high_risk_zones": [
                {
                    "location": f"({zone.center_coordinates[0]:.4f}, {zone.center_coordinates[1]:.4f})",
                    "risk_score": zone.risk_score,
                    "complaint_count": zone.complaint_count,
                    "dominant_category": zone.dominant_category
                }
                for zone in high_risk_zones[:5]  # Top 5 zones
            ],
            "prediction_count": len(predicted_incidents),
            "predicted_incidents": [
                {
                    "incident_type": pred.incident_type,
                    "risk_score": pred.risk_score,
                    "time_window": pred.time_window
                }
                for pred in predicted_incidents[:5]  # Top 5 predictions
            ],
            "weather_summary": weather_summary
        }
        
        # Try AI-generated summary
        if self.generate_ai_summary_callback:
            try:
                ai_summary = self.generate_ai_summary_callback(context)
                if ai_summary and len(ai_summary.strip()) > 0:
                    return ai_summary
            except Exception as e:
                logger.warning(f"AI summary generation failed: {e}, using fallback")
        
        # Fallback summary generation
        return self._generate_fallback_summary(
            total_complaints,
            high_risk_zones,
            predicted_incidents
        )
    
    def _generate_fallback_summary(
        self,
        total_complaints: int,
        high_risk_zones: List[RiskZone],
        predicted_incidents: List[IncidentPrediction]
    ) -> str:
        """
        Generates fallback summary when AI is unavailable.
        
        Args:
            total_complaints: Total complaint count
            high_risk_zones: List of high-risk zones
            predicted_incidents: List of incident predictions
            
        Returns:
            Fallback summary string
        """
        summary_parts = []
        
        # Overall statistics
        summary_parts.append(
            f"Today's civic risk analysis shows {total_complaints} total complaints "
            f"across Bengaluru."
        )
        
        # High-risk zones
        if high_risk_zones:
            summary_parts.append(
                f"{len(high_risk_zones)} high-risk zones have been identified, "
                f"requiring immediate attention."
            )
            
            # Dominant categories in high-risk zones
            categories = {}
            for zone in high_risk_zones:
                cat = zone.dominant_category
                categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                top_category = max(categories, key=categories.get)
                summary_parts.append(
                    f"The most common issue in high-risk zones is {top_category} "
                    f"({categories[top_category]} zones)."
                )
        else:
            summary_parts.append("No high-risk zones identified at this time.")
        
        # Incident predictions
        if predicted_incidents:
            summary_parts.append(
                f"{len(predicted_incidents)} potential incidents have been predicted. "
            )
            
            # Urgent predictions (next 6 hours)
            urgent = [p for p in predicted_incidents if p.time_window == "next 6 hours"]
            if urgent:
                summary_parts.append(
                    f"{len(urgent)} incidents are predicted within the next 6 hours, "
                    f"requiring immediate response."
                )
        else:
            summary_parts.append("No immediate incidents predicted.")
        
        # Recommendations
        if high_risk_zones or predicted_incidents:
            summary_parts.append(
                "City authorities should prioritize resource allocation to high-risk zones "
                "and prepare for predicted incidents."
            )
        
        return " ".join(summary_parts)
    
    def _store_report(self, report: DailyReport) -> None:
        """
        Stores report with 30-day retention.
        
        Args:
            report: Report to store
            
        Validates: Requirement 10.4
        """
        with self._reports_lock:
            # Add new report
            self._reports.append(report)
            
            # Remove reports older than 30 days
            cutoff_date = datetime.now() - timedelta(days=self.REPORT_RETENTION_DAYS)
            self._reports = [
                r for r in self._reports
                if r.date >= cutoff_date
            ]
            
            # Sort by date descending (most recent first)
            self._reports.sort(key=lambda r: r.date, reverse=True)
        
        logger.info(f"Report stored. Total reports in storage: {len(self._reports)}")
    
    def get_latest_report(self) -> Optional[DailyReport]:
        """
        Retrieves most recent report.
        
        Returns:
            Most recent DailyReport or None if no reports exist
            
        Performance:
            - < 200ms response time
            
        Validates: Requirement 10.5
        """
        with self._reports_lock:
            if self._reports:
                return self._reports[0]  # Already sorted by date descending
            return None
    
    def get_all_reports(self) -> List[DailyReport]:
        """
        Retrieves all stored reports.
        
        Returns:
            List of all reports sorted by date descending
        """
        with self._reports_lock:
            return self._reports.copy()
    
    def start_scheduler(self) -> None:
        """
        Starts background scheduler to generate reports at 06:00 daily.
        
        Validates: Requirement 10.1
        """
        if self._scheduler_running:
            logger.warning("Report Generator scheduler already running")
            return
        
        self._scheduler_running = True
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info(
            f"Started daily report generation scheduler "
            f"(time: {self.REPORT_GENERATION_HOUR:02d}:{self.REPORT_GENERATION_MINUTE:02d})"
        )
    
    def stop_scheduler(self) -> None:
        """
        Stops background scheduler.
        """
        if not self._scheduler_running:
            return
        
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        logger.info("Stopped daily report generation scheduler")
    
    def _scheduler_loop(self) -> None:
        """
        Background scheduler loop that generates reports at 06:00 daily.
        """
        while self._scheduler_running:
            now = datetime.now()
            
            # Check if it's time to generate report
            if (now.hour == self.REPORT_GENERATION_HOUR and
                now.minute == self.REPORT_GENERATION_MINUTE):
                
                # Check if we already generated a report today
                if (self._last_report_date is None or
                    self._last_report_date.date() != now.date()):
                    
                    try:
                        self.generate_daily_report(date=now)
                        self._last_report_date = now
                    except Exception as e:
                        logger.error(f"Error in daily report generation: {e}")
            
            # Sleep for 60 seconds before checking again
            time.sleep(60)


# Global report generator instance
_report_generator: Optional[ReportGenerator] = None


def get_report_generator(
    get_complaints_callback: Optional[Callable[[], List]] = None,
    get_risk_zones_callback: Optional[Callable[[], List[RiskZone]]] = None,
    get_predictions_callback: Optional[Callable[[], List[IncidentPrediction]]] = None,
    get_weather_callback: Optional[Callable[[], WeatherData]] = None,
    generate_ai_summary_callback: Optional[Callable[[dict], str]] = None
) -> ReportGenerator:
    """
    Gets or creates the global ReportGenerator instance.
    
    Args:
        get_complaints_callback: Callback to retrieve complaints
        get_risk_zones_callback: Callback to retrieve risk zones
        get_predictions_callback: Callback to retrieve predictions
        get_weather_callback: Callback to retrieve weather data
        generate_ai_summary_callback: Callback to generate AI summary
    
    Returns:
        ReportGenerator singleton instance
    """
    global _report_generator
    
    if _report_generator is None:
        _report_generator = ReportGenerator(
            auto_start=True,
            get_complaints_callback=get_complaints_callback,
            get_risk_zones_callback=get_risk_zones_callback,
            get_predictions_callback=get_predictions_callback,
            get_weather_callback=get_weather_callback,
            generate_ai_summary_callback=generate_ai_summary_callback
        )
    
    return _report_generator
