"""
Test suite for DynamoDBStorage using moto to mock AWS DynamoDB.

Covers all CRUD operations for:
- Complaints
- Risk Zones
- Daily Reports
"""
import os
import pytest
from datetime import datetime
from unittest.mock import patch

import boto3
from moto import mock_aws

from models import Complaint, RiskZone, RiskLevel, IncidentPrediction, DailyReport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def aws_credentials():
    """Provide fake AWS credentials so boto3 never tries to reach real AWS."""
    with patch.dict(os.environ, {
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "DYNAMODB_TABLE_COMPLAINTS": "urbanguard-complaints",
        "DYNAMODB_TABLE_RISK_ZONES": "urbanguard-risk-zones",
        "DYNAMODB_TABLE_REPORTS": "urbanguard-reports",
    }):
        yield


def _create_tables(dynamodb):
    """Create the three DynamoDB tables required by DynamoDBStorage."""
    dynamodb.create_table(
        TableName="urbanguard-complaints",
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "complaint_id", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "complaint_id", "KeyType": "HASH"}],
    )
    dynamodb.create_table(
        TableName="urbanguard-risk-zones",
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "zone_id", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "zone_id", "KeyType": "HASH"}],
    )
    dynamodb.create_table(
        TableName="urbanguard-reports",
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "report_id", "AttributeType": "S"},
            {"AttributeName": "date", "AttributeType": "N"},
        ],
        KeySchema=[
            {"AttributeName": "report_id", "KeyType": "HASH"},
            {"AttributeName": "date", "KeyType": "RANGE"},
        ],
    )


@pytest.fixture
def dynamo_storage():
    """Return a DynamoDBStorage backed by moto-mocked tables."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        _create_tables(dynamodb)
        from dynamodb_storage import DynamoDBStorage
        yield DynamoDBStorage()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_complaint(**kwargs) -> Complaint:
    defaults = dict(
        location="Koramangala",
        category="pothole",
        description="Large pothole on main road",
        timestamp=datetime(2024, 1, 15, 10, 30),
        coordinates=(12.9352, 77.6245),
        classification_confidence=0.95,
    )
    defaults.update(kwargs)
    return Complaint(**defaults)


def _make_risk_zone(**kwargs) -> RiskZone:
    defaults = dict(
        center_coordinates=(12.9352, 77.6245),
        radius_meters=500.0,
        risk_score=75.5,
        risk_level=RiskLevel.HIGH,
        complaint_count=8,
        dominant_category="pothole",
        last_updated=datetime(2024, 1, 15, 12, 0),
    )
    defaults.update(kwargs)
    return RiskZone(**defaults)


def _make_report(zones=None, predictions=None) -> DailyReport:
    zone = _make_risk_zone()
    pred = IncidentPrediction(
        zone_id=zone.zone_id,
        incident_type="road_damage",
        risk_score=75.5,
        time_window="next 6 hours",
        contributing_factors=["high_complaint_density"],
        created_at=datetime(2024, 1, 15, 12, 0),
    )
    return DailyReport(
        date=datetime(2024, 1, 15),
        total_complaints=8,
        high_risk_zones=zones or [zone],
        predicted_incidents=predictions or [pred],
        weather_summary="Clear sky, 28°C",
        ai_generated_summary="High risk of road damage in Koramangala.",
        created_at=datetime(2024, 1, 15, 6, 0),
    )


# ---------------------------------------------------------------------------
# Complaint tests
# ---------------------------------------------------------------------------

class TestComplaintOperations:
    def test_add_and_retrieve_complaint(self, dynamo_storage):
        complaint = _make_complaint()
        dynamo_storage.add_complaint(complaint)

        complaints = dynamo_storage.get_all_complaints()
        assert len(complaints) == 1
        assert complaints[0].complaint_id == complaint.complaint_id
        assert complaints[0].location == "Koramangala"
        assert complaints[0].category == "pothole"
        assert complaints[0].description == "Large pothole on main road"
        assert abs(complaints[0].classification_confidence - 0.95) < 1e-6

    def test_add_multiple_complaints_sorted_by_timestamp(self, dynamo_storage):
        c1 = _make_complaint(
            description="Older complaint",
            timestamp=datetime(2024, 1, 14, 8, 0),
        )
        c2 = _make_complaint(
            description="Newer complaint",
            timestamp=datetime(2024, 1, 15, 10, 0),
        )
        dynamo_storage.add_complaint(c1)
        dynamo_storage.add_complaint(c2)

        complaints = dynamo_storage.get_all_complaints()
        assert len(complaints) == 2
        assert complaints[0].timestamp >= complaints[1].timestamp

    def test_get_complaints_by_location(self, dynamo_storage):
        c1 = _make_complaint(location="Koramangala")
        c2 = _make_complaint(location="Indiranagar")
        dynamo_storage.add_complaint(c1)
        dynamo_storage.add_complaint(c2)

        result = dynamo_storage.get_complaints_by_location("Koramangala")
        assert len(result) == 1
        assert result[0].location == "Koramangala"

    def test_get_complaints_by_category(self, dynamo_storage):
        c1 = _make_complaint(category="flooding")
        c2 = _make_complaint(category="pothole")
        dynamo_storage.add_complaint(c1)
        dynamo_storage.add_complaint(c2)

        result = dynamo_storage.get_complaints_by_category("flooding")
        assert len(result) == 1
        assert result[0].category == "flooding"

    def test_get_complaint_count(self, dynamo_storage):
        assert dynamo_storage.get_complaint_count() == 0
        dynamo_storage.add_complaint(_make_complaint())
        dynamo_storage.add_complaint(_make_complaint())
        assert dynamo_storage.get_complaint_count() == 2

    def test_coordinates_round_trip(self, dynamo_storage):
        complaint = _make_complaint(coordinates=(12.9352, 77.6245))
        dynamo_storage.add_complaint(complaint)
        stored = dynamo_storage.get_all_complaints()[0]
        assert abs(stored.coordinates[0] - 12.9352) < 1e-4
        assert abs(stored.coordinates[1] - 77.6245) < 1e-4

    def test_get_all_complaints_empty(self, dynamo_storage):
        assert dynamo_storage.get_all_complaints() == []

    def test_get_complaints_by_location_no_match(self, dynamo_storage):
        dynamo_storage.add_complaint(_make_complaint(location="Koramangala"))
        result = dynamo_storage.get_complaints_by_location("Whitefield")
        assert result == []


# ---------------------------------------------------------------------------
# Risk Zone tests
# ---------------------------------------------------------------------------

class TestRiskZoneOperations:
    def test_add_and_retrieve_risk_zone(self, dynamo_storage):
        zone = _make_risk_zone()
        dynamo_storage.add_risk_zone(zone)

        zones = dynamo_storage.get_all_risk_zones()
        assert len(zones) == 1
        assert zones[0].zone_id == zone.zone_id
        assert zones[0].risk_level == RiskLevel.HIGH
        assert abs(zones[0].risk_score - 75.5) < 1e-4

    def test_update_risk_zones_replaces_existing(self, dynamo_storage):
        old_zone = _make_risk_zone()
        dynamo_storage.add_risk_zone(old_zone)

        new_zone = _make_risk_zone(risk_score=45.0, risk_level=RiskLevel.MEDIUM)
        dynamo_storage.update_risk_zones([new_zone])

        zones = dynamo_storage.get_all_risk_zones()
        assert len(zones) == 1
        assert zones[0].zone_id == new_zone.zone_id
        assert abs(zones[0].risk_score - 45.0) < 1e-4

    def test_update_risk_zones_with_empty_list(self, dynamo_storage):
        dynamo_storage.add_risk_zone(_make_risk_zone())
        dynamo_storage.update_risk_zones([])
        assert dynamo_storage.get_all_risk_zones() == []

    def test_get_high_risk_zones_filters_correctly(self, dynamo_storage):
        low = _make_risk_zone(risk_score=10.0, risk_level=RiskLevel.LOW)
        high = _make_risk_zone(risk_score=80.0, risk_level=RiskLevel.HIGH)
        dynamo_storage.add_risk_zone(low)
        dynamo_storage.add_risk_zone(high)

        result = dynamo_storage.get_high_risk_zones(min_score=50.0)
        assert len(result) == 1
        assert result[0].zone_id == high.zone_id

    def test_get_all_risk_zones_empty(self, dynamo_storage):
        assert dynamo_storage.get_all_risk_zones() == []


# ---------------------------------------------------------------------------
# Daily Report tests
# ---------------------------------------------------------------------------

class TestDailyReportOperations:
    def test_add_and_retrieve_latest_report(self, dynamo_storage):
        report = _make_report()
        dynamo_storage.add_daily_report(report)

        latest = dynamo_storage.get_latest_report()
        assert latest is not None
        assert latest.report_id == report.report_id
        assert latest.total_complaints == 8
        assert latest.ai_generated_summary == "High risk of road damage in Koramangala."

    def test_get_latest_report_returns_most_recent(self, dynamo_storage):
        r1 = _make_report()
        r1.date = datetime(2024, 1, 14)
        r2 = _make_report()
        r2.date = datetime(2024, 1, 15)
        dynamo_storage.add_daily_report(r1)
        dynamo_storage.add_daily_report(r2)

        latest = dynamo_storage.get_latest_report()
        assert latest.report_id == r2.report_id

    def test_get_all_reports_sorted_descending(self, dynamo_storage):
        r1 = _make_report()
        r1.date = datetime(2024, 1, 13)
        r2 = _make_report()
        r2.date = datetime(2024, 1, 15)
        r3 = _make_report()
        r3.date = datetime(2024, 1, 14)
        for r in [r1, r2, r3]:
            dynamo_storage.add_daily_report(r)

        reports = dynamo_storage.get_all_reports()
        assert len(reports) == 3
        assert reports[0].date >= reports[1].date >= reports[2].date

    def test_get_latest_report_empty(self, dynamo_storage):
        assert dynamo_storage.get_latest_report() is None

    def test_report_nested_risk_zones_round_trip(self, dynamo_storage):
        zone = _make_risk_zone(risk_score=88.0, risk_level=RiskLevel.HIGH)
        report = _make_report(zones=[zone])
        dynamo_storage.add_daily_report(report)

        latest = dynamo_storage.get_latest_report()
        assert len(latest.high_risk_zones) == 1
        assert abs(latest.high_risk_zones[0].risk_score - 88.0) < 1e-4

    def test_report_nested_predictions_round_trip(self, dynamo_storage):
        zone = _make_risk_zone()
        pred = IncidentPrediction(
            zone_id=zone.zone_id,
            incident_type="flooding",
            risk_score=80.0,
            time_window="next 6 hours",
            contributing_factors=["high_rainfall", "flooding_complaints"],
            created_at=datetime(2024, 1, 15, 12, 0),
        )
        report = _make_report(zones=[zone], predictions=[pred])
        dynamo_storage.add_daily_report(report)

        latest = dynamo_storage.get_latest_report()
        assert len(latest.predicted_incidents) == 1
        assert latest.predicted_incidents[0].incident_type == "flooding"
        assert latest.predicted_incidents[0].contributing_factors == [
            "high_rainfall", "flooding_complaints"
        ]


# ---------------------------------------------------------------------------
# Clear all
# ---------------------------------------------------------------------------

class TestClearAll:
    def test_clear_all_removes_all_data(self, dynamo_storage):
        dynamo_storage.add_complaint(_make_complaint())
        dynamo_storage.add_risk_zone(_make_risk_zone())
        dynamo_storage.add_daily_report(_make_report())

        dynamo_storage.clear_all()

        assert dynamo_storage.get_all_complaints() == []
        assert dynamo_storage.get_all_risk_zones() == []
        assert dynamo_storage.get_latest_report() is None


# ---------------------------------------------------------------------------
# Storage factory
# ---------------------------------------------------------------------------

class TestStorageFactory:
    def test_use_dynamodb_env_selects_dynamodb(self):
        """get_storage() returns DynamoDBStorage when USE_DYNAMODB=true."""
        with mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            _create_tables(dynamodb)
            with patch.dict(os.environ, {"USE_DYNAMODB": "true"}):
                import importlib
                import storage as storage_module
                importlib.reload(storage_module)
                from dynamodb_storage import DynamoDBStorage
                assert isinstance(storage_module.get_storage(), DynamoDBStorage)
                # Restore original module state
                importlib.reload(storage_module)

    def test_default_env_selects_in_memory(self):
        """get_storage() returns InMemoryStorage by default."""
        with patch.dict(os.environ, {}, clear=False):
            env_backup = os.environ.pop("USE_DYNAMODB", None)
            env_backup2 = os.environ.pop("AWS_EXECUTION_ENV", None)
            try:
                import importlib
                import storage as storage_module
                importlib.reload(storage_module)
                from storage import InMemoryStorage
                assert isinstance(storage_module.get_storage(), InMemoryStorage)
            finally:
                if env_backup is not None:
                    os.environ["USE_DYNAMODB"] = env_backup
                if env_backup2 is not None:
                    os.environ["AWS_EXECUTION_ENV"] = env_backup2
                importlib.reload(storage_module)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
