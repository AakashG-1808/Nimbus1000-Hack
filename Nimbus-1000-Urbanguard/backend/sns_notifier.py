"""
UrbanGuard AI System - SNS Notifier
Sends real-time alerts to city officials when zones hit HIGH risk.
Topic ARN is read from SNS_ALERT_TOPIC_ARN env var.
"""
import json
import logging
import os
from typing import Optional
from models import RiskZone, RiskLevel

logger = logging.getLogger(__name__)

_sns_client = None


def _get_client():
    global _sns_client
    if _sns_client is None:
        import boto3
        _sns_client = boto3.client("sns", region_name=os.getenv("AWS_REGION", "ap-south-2"))
    return _sns_client


def _nearest_area(lat: float, lng: float) -> str:
    """Quick nearest-area lookup (same table used elsewhere)."""
    areas = [
        ("Koramangala", 12.9352, 77.6245), ("Indiranagar", 12.9784, 77.6408),
        ("Whitefield", 12.9698, 77.7499), ("Marathahalli", 12.9591, 77.6974),
        ("HSR Layout", 12.9116, 77.6389), ("BTM Layout", 12.9166, 77.6101),
        ("Jayanagar", 12.9308, 77.5838), ("Malleshwaram", 13.0035, 77.5710),
        ("Hebbal", 13.0350, 77.5970), ("Yelahanka", 13.1007, 77.5963),
        ("Electronic City", 12.8399, 77.6770), ("Bannerghatta Road", 12.8892, 77.5957),
        ("Rajajinagar", 12.9907, 77.5530), ("Yeshwanthpur", 13.0280, 77.5390),
        ("KR Puram", 13.0050, 77.6960), ("Bellandur", 12.9257, 77.6762),
        ("JP Nagar", 12.9063, 77.5857), ("Vijayanagar", 12.9716, 77.5322),
        ("City Center", 12.9716, 77.5946),
    ]
    return min(areas, key=lambda a: (a[1] - lat) ** 2 + (a[2] - lng) ** 2)[0]


def notify_high_risk_zone(zone: RiskZone) -> bool:
    """
    Publish an SNS alert for a HIGH-risk zone.
    Returns True if published, False if SNS not configured or call failed.
    """
    topic_arn = os.getenv("SNS_ALERT_TOPIC_ARN")
    if not topic_arn:
        return False  # SNS not configured — silent no-op

    lat, lng = zone.center_coordinates
    area = _nearest_area(lat, lng)

    subject = f"[UrbanGuard] HIGH RISK ALERT — {area}"
    message = (
        f"HIGH RISK ZONE DETECTED\n"
        f"Area: {area}\n"
        f"Risk Score: {zone.risk_score:.0f}/100\n"
        f"Dominant Issue: {zone.dominant_category.replace('_', ' ').title()}\n"
        f"Complaints in Zone: {zone.complaint_count}\n"
        f"Coordinates: {lat:.4f}, {lng:.4f}\n"
        f"Detected at: {zone.last_updated.strftime('%Y-%m-%d %H:%M IST')}\n\n"
        f"Immediate inspection recommended."
    )

    try:
        _get_client().publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message,
            MessageAttributes={
                "risk_level": {"DataType": "String", "StringValue": zone.risk_level.value},
                "area": {"DataType": "String", "StringValue": area},
                "risk_score": {"DataType": "Number", "StringValue": str(int(zone.risk_score))},
            },
        )
        logger.info(f"[SNS] Alert sent for HIGH risk zone in {area} (score={zone.risk_score:.0f})")
        return True
    except Exception as e:
        logger.warning(f"[SNS] Failed to publish alert: {e}")
        return False


def notify_daily_report(report_summary: str, total_complaints: int, high_risk_count: int) -> bool:
    """Publish a daily report summary to SNS."""
    topic_arn = os.getenv("SNS_ALERT_TOPIC_ARN")
    if not topic_arn:
        return False

    subject = "[UrbanGuard] Daily Risk Report Ready"
    message = (
        f"DAILY CIVIC RISK REPORT\n"
        f"Total Complaints: {total_complaints}\n"
        f"High-Risk Zones: {high_risk_count}\n\n"
        f"{report_summary}"
    )

    try:
        _get_client().publish(TopicArn=topic_arn, Subject=subject, Message=message)
        logger.info("[SNS] Daily report notification sent")
        return True
    except Exception as e:
        logger.warning(f"[SNS] Failed to publish daily report: {e}")
        return False
