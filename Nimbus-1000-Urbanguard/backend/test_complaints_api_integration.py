"""
Integration tests for complaints API endpoints.
Validates filtering, pagination, and request validation.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from complaint_processor import ComplaintProcessor
from storage import storage
from main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before and after each test."""
    storage.clear_all()
    yield
    storage.clear_all()


def seed_complaints():
    """Seed storage with sample complaints and return metadata."""
    processor = ComplaintProcessor()
    now = datetime.now()
    payloads = [
        {
            "location": "Koramangala",
            "category": "pothole",
            "description": "Large pothole on main road",
            "timestamp": now - timedelta(minutes=2)
        },
        {
            "location": "Indiranagar",
            "category": "flooding",
            "description": "Waterlogging after rain",
            "timestamp": now - timedelta(minutes=1)
        },
        {
            "location": "Whitefield",
            "category": "traffic",
            "description": "Traffic jam at junction",
            "timestamp": now
        }
    ]

    results = []
    for payload in payloads:
        result = processor.submit_complaint(**payload)
        assert result.success
        results.append({
            "timestamp": payload["timestamp"],
            "complaint_id": result.complaint_id
        })

    return {
        "now": now,
        "payloads": payloads,
        "results": results
    }


def test_get_complaints_sorted_by_timestamp_desc():
    """GET /complaints returns complaints sorted by timestamp desc."""
    seeded = seed_complaints()

    response = client.get("/complaints")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3

    expected_ids = [
        r["complaint_id"]
        for r in sorted(seeded["results"], key=lambda r: r["timestamp"], reverse=True)
    ]
    actual_ids = [item["complaint_id"] for item in data]

    assert actual_ids == expected_ids


def test_get_complaints_filters_by_location_and_category():
    """GET /complaints filters by location and category."""
    seed_complaints()

    response = client.get("/complaints", params={
        "location": "Koramangala",
        "category": "pothole"
    })
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["location"] == "Koramangala"
    assert data[0]["category"] == "pothole"


def test_get_complaints_filters_by_time_range():
    """GET /complaints filters by since/until timestamps."""
    seeded = seed_complaints()
    middle_timestamp = seeded["payloads"][1]["timestamp"]

    response = client.get("/complaints", params={
        "since": (middle_timestamp - timedelta(seconds=1)).isoformat(),
        "until": (middle_timestamp + timedelta(seconds=1)).isoformat()
    })
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["location"] == "Indiranagar"


def test_get_complaints_pagination_offset_limit():
    """GET /complaints supports offset and limit pagination."""
    seeded = seed_complaints()

    response = client.get("/complaints", params={
        "offset": 1,
        "limit": 1
    })
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    sorted_ids = [
        r["complaint_id"]
        for r in sorted(seeded["results"], key=lambda r: r["timestamp"], reverse=True)
    ]
    assert data[0]["complaint_id"] == sorted_ids[1]


def test_get_complaints_rejects_invalid_location():
    """GET /complaints rejects invalid location filter."""
    response = client.get("/complaints", params={"location": "InvalidPlace"})
    assert response.status_code == 400


def test_get_complaints_rejects_invalid_category():
    """GET /complaints rejects invalid category filter."""
    response = client.get("/complaints", params={"category": "invalid_category"})
    assert response.status_code == 400


def test_get_complaints_rejects_invalid_time_range():
    """GET /complaints rejects invalid time range."""
    response = client.get("/complaints", params={
        "since": "2024-01-02T00:00:00",
        "until": "2024-01-01T00:00:00"
    })
    assert response.status_code == 400


def test_report_complaint_rejects_blank_description():
    """POST /report-complaint rejects blank descriptions."""
    response = client.post("/report-complaint", json={
        "location": "Koramangala",
        "category": "pothole",
        "description": "   "
    })
    assert response.status_code == 422
