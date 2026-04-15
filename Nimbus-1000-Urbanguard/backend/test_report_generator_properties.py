"""
Property-Based Tests for Report Generator
Tests for Task 9.4: Property tests for report generation using Hypothesis

**Validates: Requirements 10.2, 10.3**

Properties tested:
- Property 32: Daily Report Completeness
- Property 33: AI Summary Generation
"""
import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings
from report_generator import ReportGenerator
from models import (
    RiskZone, RiskLevel, IncidentPrediction, WeatherData, Complaint
)


# ============================================================================
# Strategy Helpers
# ============================================================================

@st.composite
def complaint_list_strategy(draw, min_size=0, max_size=100):
    """Generate a list of valid Complaints."""
    locations = ["Koramangala", "Indiranagar", "Whitefield", "Electronic City"]
    categories = Complaint.CATEGORIES
    
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    
    complaints = []
    for _ in range(count):
        complaint = Complaint(
            location=draw(st.sampled_from(locations)),
            category=draw(st.sampled_from(categories)),
            description=draw(st.text(min_size=1, max_size=100)),
            timestamp=datetime.now(),
            coordinates=(
                draw(st.floats(min_value=12.8, max_value=13.2)),
                draw(st.floats(min_value=77.4, max_value=77.8))
            )
        )
        complaints.append(complaint)
    
    return complaints


@st.composite
def risk_zone_list_strategy(draw, min_size=0, max_size=20):
    """Generate a list of valid RiskZones."""
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    
    zones = []
    for _ in range(count):
        risk_score = draw(st.floats(min_value=0.0, max_value=100.0))
        
        if risk_score <= 33:
            risk_level = RiskLevel.LOW
        elif risk_score <= 66:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        zone = RiskZone(
            center_coordinates=(
                draw(st.floats(min_value=12.8, max_value=13.2)),
                draw(st.floats(min_value=77.4, max_value=77.8))
            ),
            radius_meters=500.0,
            risk_score=risk_score,
            risk_level=risk_level,
            complaint_count=draw(st.integers(min_value=1, max_value=50)),
            dominant_category=draw(st.sampled_from(Complaint.CATEGORIES)),
            last_updated=datetime.now()
        )
        zones.append(zone)
    
    return zones


@st.composite
def prediction_list_strategy(draw, min_size=0, max_size=20):
    """Generate a list of valid IncidentPredictions."""
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    
    incident_types = [
        "flooding", "road_damage", "traffic_gridlock", "traffic_congestion",
        "waste_accumulation", "lighting_failure", "water_shortage",
        "noise_pollution", "construction_hazard"
    ]
    
    predictions = []
    for _ in range(count):
        risk_score = draw(st.floats(min_value=70.1, max_value=100.0))
        
        prediction = IncidentPrediction(
            zone_id=f"zone-{draw(st.integers(min_value=1, max_value=100))}",
            incident_type=draw(st.sampled_from(incident_types)),
            risk_score=risk_score,
            time_window=draw(st.sampled_from(["next 6 hours", "next 24 hours"])),
            contributing_factors=draw(st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=5)),
            created_at=datetime.now()
        )
        predictions.append(prediction)
    
    return predictions


@st.composite
def weather_strategy(draw):
    """Generate valid WeatherData."""
    precipitation = draw(st.floats(min_value=0.0, max_value=100.0))
    
    return WeatherData(
        temperature_celsius=draw(st.floats(min_value=15.0, max_value=40.0)),
        humidity_percent=draw(st.floats(min_value=20.0, max_value=100.0)),
        precipitation_mm_per_hour=precipitation,
        wind_speed_kmh=draw(st.floats(min_value=0.0, max_value=60.0)),
        high_rainfall_flag=precipitation > 10.0,
        timestamp=datetime.now(),
        source="test"
    )


# ============================================================================
# Property Tests
# ============================================================================

class TestReportGeneratorProperties:
    """Property-based tests for ReportGenerator"""
    
    # Feature: urbanguard-ai-system, Property 32: Daily Report Completeness
    @given(
        complaints=complaint_list_strategy(),
        risk_zones=risk_zone_list_strategy(),
        predictions=prediction_list_strategy(),
        weather=weather_strategy()
    )
    @settings(max_examples=100)
    def test_property_32_daily_report_completeness(
        self,
        complaints,
        risk_zones,
        predictions,
        weather
    ):
        """
        Property 32: For any daily report generated, it should include
        total complaints count, high-risk zones list, predicted incidents,
        and weather summary.
        
        Validates: Requirement 10.2
        """
        # Create generator with test data
        generator = ReportGenerator(
            auto_start=False,
            get_complaints_callback=lambda: complaints,
            get_risk_zones_callback=lambda: risk_zones,
            get_predictions_callback=lambda: predictions,
            get_weather_callback=lambda: weather
        )
        
        # Generate report
        report = generator.generate_daily_report()
        
        # Check all required fields are present
        assert report.total_complaints is not None
        assert report.high_risk_zones is not None
        assert report.predicted_incidents is not None
        assert report.weather_summary is not None
        
        # Check field types
        assert isinstance(report.total_complaints, int)
        assert isinstance(report.high_risk_zones, list)
        assert isinstance(report.predicted_incidents, list)
        assert isinstance(report.weather_summary, str)
        
        # Check values match input data
        assert report.total_complaints == len(complaints)
        
        # High-risk zones should only include zones with score > 66
        expected_high_risk = [z for z in risk_zones if z.risk_score > 66]
        assert len(report.high_risk_zones) == len(expected_high_risk)
        
        # Predictions should match input
        assert len(report.predicted_incidents) == len(predictions)
        
        # Weather summary should be non-empty
        assert len(report.weather_summary) > 0
    
    # Feature: urbanguard-ai-system, Property 32: Report metadata completeness
    @given(
        complaints=complaint_list_strategy(min_size=0, max_size=50),
        risk_zones=risk_zone_list_strategy(min_size=0, max_size=10),
        predictions=prediction_list_strategy(min_size=0, max_size=10)
    )
    @settings(max_examples=100)
    def test_property_32_report_metadata_completeness(
        self,
        complaints,
        risk_zones,
        predictions
    ):
        """
        Property 32 (extended): Report should have complete metadata
        (report_id, date, created_at).
        
        Validates: Requirement 10.2
        """
        generator = ReportGenerator(
            auto_start=False,
            get_complaints_callback=lambda: complaints,
            get_risk_zones_callback=lambda: risk_zones,
            get_predictions_callback=lambda: predictions
        )
        
        report = generator.generate_daily_report()
        
        # Check metadata fields
        assert report.report_id is not None
        assert report.date is not None
        assert report.created_at is not None
        
        # Check field types
        assert isinstance(report.report_id, str)
        assert isinstance(report.date, datetime)
        assert isinstance(report.created_at, datetime)
        
        # Report ID should be non-empty
        assert len(report.report_id) > 0
    
    # Feature: urbanguard-ai-system, Property 33: AI Summary Generation
    @given(
        complaints=complaint_list_strategy(min_size=1, max_size=50),
        risk_zones=risk_zone_list_strategy(min_size=1, max_size=10),
        predictions=prediction_list_strategy(min_size=1, max_size=10)
    )
    @settings(max_examples=100)
    def test_property_33_ai_summary_generation(
        self,
        complaints,
        risk_zones,
        predictions
    ):
        """
        Property 33: For any daily report, the Report_Generator should use AI
        to generate a natural language summary of risk patterns
        (the summary should be non-empty and generated via AI).
        
        Validates: Requirement 10.3
        """
        # Create generator with AI callback
        ai_summary = "AI-generated risk analysis: High activity detected in multiple zones."
        
        generator = ReportGenerator(
            auto_start=False,
            get_complaints_callback=lambda: complaints,
            get_risk_zones_callback=lambda: risk_zones,
            get_predictions_callback=lambda: predictions,
            generate_ai_summary_callback=lambda context: ai_summary
        )
        
        report = generator.generate_daily_report()
        
        # AI summary should be present
        assert report.ai_generated_summary is not None
        
        # AI summary should be non-empty
        assert len(report.ai_generated_summary) > 0
        
        # AI summary should match the AI-generated content
        assert report.ai_generated_summary == ai_summary
    
    # Feature: urbanguard-ai-system, Property 33: Fallback summary generation
    @given(
        complaints=complaint_list_strategy(min_size=1, max_size=50),
        risk_zones=risk_zone_list_strategy(min_size=1, max_size=10),
        predictions=prediction_list_strategy(min_size=1, max_size=10)
    )
    @settings(max_examples=100)
    def test_property_33_fallback_summary_generation(
        self,
        complaints,
        risk_zones,
        predictions
    ):
        """
        Property 33 (fallback): When AI is unavailable, the Report_Generator
        should generate a fallback summary that is still non-empty and informative.
        
        Validates: Requirement 10.3
        """
        # Create generator without AI callback (fallback mode)
        generator = ReportGenerator(
            auto_start=False,
            get_complaints_callback=lambda: complaints,
            get_risk_zones_callback=lambda: risk_zones,
            get_predictions_callback=lambda: predictions
        )
        
        report = generator.generate_daily_report()
        
        # Fallback summary should be present
        assert report.ai_generated_summary is not None
        
        # Fallback summary should be non-empty
        assert len(report.ai_generated_summary) > 0
        
        # Fallback summary should contain key information
        summary_lower = report.ai_generated_summary.lower()
        assert "complaint" in summary_lower or "zone" in summary_lower or "incident" in summary_lower
    
    # Feature: urbanguard-ai-system, Additional property: Report storage
    @given(
        report_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50)
    def test_report_storage_and_retrieval(self, report_count):
        """
        Additional property: All generated reports should be stored and retrievable.
        """
        generator = ReportGenerator(auto_start=False)
        
        # Generate multiple reports
        reports = []
        for i in range(report_count):
            date = datetime.now() - timedelta(days=i)
            report = generator.generate_daily_report(date=date)
            reports.append(report)
        
        # All reports should be stored
        stored_reports = generator.get_all_reports()
        assert len(stored_reports) == report_count
        
        # Latest report should be retrievable
        latest = generator.get_latest_report()
        assert latest is not None
        assert latest.report_id == reports[0].report_id
    
    # Feature: urbanguard-ai-system, Additional property: Report uniqueness
    @given(
        report_count=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=50)
    def test_report_uniqueness(self, report_count):
        """
        Additional property: Each report should have a unique report_id.
        """
        generator = ReportGenerator(auto_start=False)
        
        # Generate multiple reports
        reports = []
        for i in range(report_count):
            date = datetime.now() - timedelta(days=i)
            report = generator.generate_daily_report(date=date)
            reports.append(report)
        
        # All report IDs should be unique
        report_ids = [r.report_id for r in reports]
        assert len(report_ids) == len(set(report_ids)), \
            "All report IDs should be unique"
    
    # Feature: urbanguard-ai-system, Additional property: High-risk zone filtering
    @given(
        risk_zones=risk_zone_list_strategy(min_size=5, max_size=20)
    )
    @settings(max_examples=100)
    def test_high_risk_zone_filtering(self, risk_zones):
        """
        Additional property: Report should only include zones with risk_score > 66
        in the high_risk_zones list.
        """
        generator = ReportGenerator(
            auto_start=False,
            get_risk_zones_callback=lambda: risk_zones
        )
        
        report = generator.generate_daily_report()
        
        # All zones in high_risk_zones should have score > 66
        for zone in report.high_risk_zones:
            assert zone.risk_score > 66, \
                f"Zone with score {zone.risk_score} should not be in high_risk_zones"
        
        # Count should match expected high-risk zones
        expected_count = sum(1 for z in risk_zones if z.risk_score > 66)
        assert len(report.high_risk_zones) == expected_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
