"""
Unit tests for Report Generator - Task 9.1, 9.2, 9.3
Tests daily report generation, AI summary, and report storage/retrieval
"""
import pytest
from datetime import datetime, timedelta
from models import (
    DailyReport, RiskZone, RiskLevel, IncidentPrediction,
    WeatherData, Complaint
)
from report_generator import ReportGenerator, get_report_generator


class TestReportGenerator:
    """Unit tests for ReportGenerator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create test data
        self.test_complaints = [
            Complaint(
                location="Koramangala",
                category="pothole",
                description="Large pothole",
                timestamp=datetime.now(),
                coordinates=(12.9352, 77.6245)
            )
            for _ in range(15)
        ]
        
        self.test_risk_zones = [
            RiskZone(
                center_coordinates=(12.9352, 77.6245),
                radius_meters=500.0,
                risk_score=75.0,
                risk_level=RiskLevel.HIGH,
                complaint_count=8,
                dominant_category="pothole",
                last_updated=datetime.now()
            ),
            RiskZone(
                center_coordinates=(12.9716, 77.6412),
                radius_meters=500.0,
                risk_score=88.0,
                risk_level=RiskLevel.HIGH,
                complaint_count=12,
                dominant_category="flooding",
                last_updated=datetime.now()
            ),
            RiskZone(
                center_coordinates=(12.9698, 77.7499),
                radius_meters=500.0,
                risk_score=45.0,
                risk_level=RiskLevel.MEDIUM,
                complaint_count=5,
                dominant_category="traffic",
                last_updated=datetime.now()
            )
        ]
        
        self.test_predictions = [
            IncidentPrediction(
                zone_id="zone-1",
                incident_type="road_damage",
                risk_score=75.0,
                time_window="next 24 hours",
                contributing_factors=["high_complaint_density", "pothole_complaints"],
                created_at=datetime.now()
            ),
            IncidentPrediction(
                zone_id="zone-2",
                incident_type="flooding",
                risk_score=88.0,
                time_window="next 6 hours",
                contributing_factors=["high_complaint_density", "high_rainfall", "flooding_complaints"],
                created_at=datetime.now()
            )
        ]
        
        self.test_weather = WeatherData(
            temperature_celsius=28.0,
            humidity_percent=75.0,
            precipitation_mm_per_hour=5.0,
            wind_speed_kmh=15.0,
            high_rainfall_flag=False,
            timestamp=datetime.now(),
            source="test"
        )
        
        # Create report generator with callbacks
        self.generator = ReportGenerator(
            auto_start=False,
            get_complaints_callback=lambda: self.test_complaints,
            get_risk_zones_callback=lambda: self.test_risk_zones,
            get_predictions_callback=lambda: self.test_predictions,
            get_weather_callback=lambda: self.test_weather
        )
    
    def test_generate_daily_report_creates_report(self):
        """Test that generate_daily_report creates a DailyReport"""
        report = self.generator.generate_daily_report()
        
        assert isinstance(report, DailyReport)
        assert report.report_id is not None
        assert report.date is not None
        assert report.created_at is not None
    
    def test_report_includes_total_complaints(self):
        """Test that report includes total complaints count"""
        report = self.generator.generate_daily_report()
        
        assert report.total_complaints == 15
    
    def test_report_includes_high_risk_zones(self):
        """Test that report includes high-risk zones (score > 66)"""
        report = self.generator.generate_daily_report()
        
        # Should include 2 high-risk zones (scores 75 and 88)
        assert len(report.high_risk_zones) == 2
        assert all(zone.risk_score > 66 for zone in report.high_risk_zones)
    
    def test_report_includes_predicted_incidents(self):
        """Test that report includes predicted incidents"""
        report = self.generator.generate_daily_report()
        
        assert len(report.predicted_incidents) == 2
        assert all(isinstance(pred, IncidentPrediction) for pred in report.predicted_incidents)
    
    def test_report_includes_weather_summary(self):
        """Test that report includes weather summary"""
        report = self.generator.generate_daily_report()
        
        assert report.weather_summary is not None
        assert len(report.weather_summary) > 0
        assert "28.0°C" in report.weather_summary
        assert "75%" in report.weather_summary
    
    def test_weather_summary_with_high_rainfall(self):
        """Test that weather summary includes high rainfall warning"""
        # Update weather to high rainfall
        self.test_weather.high_rainfall_flag = True
        self.test_weather.precipitation_mm_per_hour = 15.0
        
        report = self.generator.generate_daily_report()
        
        assert "High rainfall" in report.weather_summary
    
    def test_report_includes_ai_summary(self):
        """Test that report includes AI-generated summary"""
        report = self.generator.generate_daily_report()
        
        assert report.ai_generated_summary is not None
        assert len(report.ai_generated_summary) > 0
    
    def test_ai_summary_with_custom_callback(self):
        """Test that custom AI summary callback is used"""
        custom_summary = "Custom AI-generated risk analysis"
        
        generator = ReportGenerator(
            auto_start=False,
            get_complaints_callback=lambda: self.test_complaints,
            get_risk_zones_callback=lambda: self.test_risk_zones,
            get_predictions_callback=lambda: self.test_predictions,
            get_weather_callback=lambda: self.test_weather,
            generate_ai_summary_callback=lambda context: custom_summary
        )
        
        report = generator.generate_daily_report()
        
        assert report.ai_generated_summary == custom_summary
    
    def test_fallback_summary_when_ai_unavailable(self):
        """Test that fallback summary is generated when AI is unavailable"""
        # No AI callback provided
        report = self.generator.generate_daily_report()
        
        # Should have fallback summary
        assert report.ai_generated_summary is not None
        assert "complaints" in report.ai_generated_summary.lower()
        assert "high-risk zones" in report.ai_generated_summary.lower()
    
    def test_fallback_summary_includes_statistics(self):
        """Test that fallback summary includes key statistics"""
        report = self.generator.generate_daily_report()
        
        summary = report.ai_generated_summary
        assert "15 total complaints" in summary
        assert "2 high-risk zones" in summary
        assert "2 potential incidents" in summary
    
    def test_store_report(self):
        """Test that reports are stored"""
        report = self.generator.generate_daily_report()
        
        # Report should be stored
        stored_reports = self.generator.get_all_reports()
        assert len(stored_reports) == 1
        assert stored_reports[0].report_id == report.report_id
    
    def test_get_latest_report(self):
        """Test that get_latest_report returns most recent report"""
        # Generate first report
        report1 = self.generator.generate_daily_report(date=datetime.now() - timedelta(days=1))
        
        # Generate second report
        report2 = self.generator.generate_daily_report(date=datetime.now())
        
        # Latest should be report2
        latest = self.generator.get_latest_report()
        assert latest.report_id == report2.report_id
    
    def test_get_latest_report_returns_none_when_empty(self):
        """Test that get_latest_report returns None when no reports exist"""
        generator = ReportGenerator(auto_start=False)
        
        latest = generator.get_latest_report()
        assert latest is None
    
    def test_report_retention_30_days(self):
        """Test that reports older than 30 days are removed"""
        # Generate reports for different dates
        dates = [
            datetime.now() - timedelta(days=35),  # Should be removed
            datetime.now() - timedelta(days=31),  # Should be removed
            datetime.now() - timedelta(days=29),  # Should be kept
            datetime.now() - timedelta(days=15),  # Should be kept
            datetime.now()  # Should be kept
        ]
        
        for date in dates:
            self.generator.generate_daily_report(date=date)
        
        # Should only have 3 reports (within 30 days)
        stored_reports = self.generator.get_all_reports()
        assert len(stored_reports) == 3
        
        # All stored reports should be within 30 days
        cutoff = datetime.now() - timedelta(days=30)
        assert all(report.date >= cutoff for report in stored_reports)
    
    def test_reports_sorted_by_date_descending(self):
        """Test that reports are sorted by date descending"""
        # Generate reports for different dates
        dates = [
            datetime.now() - timedelta(days=5),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=10),
            datetime.now()
        ]
        
        for date in dates:
            self.generator.generate_daily_report(date=date)
        
        stored_reports = self.generator.get_all_reports()
        
        # Should be sorted by date descending
        for i in range(len(stored_reports) - 1):
            assert stored_reports[i].date >= stored_reports[i + 1].date
    
    def test_report_generation_without_callbacks(self):
        """Test that report generation works without callbacks (with defaults)"""
        generator = ReportGenerator(auto_start=False)
        
        report = generator.generate_daily_report()
        
        assert report.total_complaints == 0
        assert len(report.high_risk_zones) == 0
        assert len(report.predicted_incidents) == 0
        assert "unavailable" in report.weather_summary.lower()
    
    def test_report_generation_with_callback_errors(self):
        """Test that report generation handles callback errors gracefully"""
        def failing_callback():
            raise Exception("Callback error")
        
        generator = ReportGenerator(
            auto_start=False,
            get_complaints_callback=failing_callback,
            get_risk_zones_callback=failing_callback,
            get_predictions_callback=failing_callback,
            get_weather_callback=failing_callback
        )
        
        # Should not raise exception
        report = generator.generate_daily_report()
        
        assert report.total_complaints == 0
        assert len(report.high_risk_zones) == 0
        assert len(report.predicted_incidents) == 0


class TestReportGeneratorSingleton:
    """Test the global report generator singleton"""
    
    def test_get_report_generator_returns_instance(self):
        """Test that get_report_generator returns a ReportGenerator instance"""
        generator = get_report_generator()
        assert isinstance(generator, ReportGenerator)
    
    def test_get_report_generator_returns_same_instance(self):
        """Test that get_report_generator returns the same instance"""
        generator1 = get_report_generator()
        generator2 = get_report_generator()
        assert generator1 is generator2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
