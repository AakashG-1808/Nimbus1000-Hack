"""
UrbanGuard AI System - SQS Handler
Decouples complaint submission from processing.
When SQS_COMPLAINT_QUEUE_URL is set, complaints are enqueued instead of
processed synchronously — Lambda consumers pick them up asynchronously.
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_sqs_client = None


def _get_client():
    global _sqs_client
    if _sqs_client is None:
        import boto3
        _sqs_client = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "ap-south-2"))
    return _sqs_client


def enqueue_complaint(
    location: str,
    category: str,
    description: str,
    timestamp: datetime,
    coordinates: Optional[tuple] = None,
) -> Optional[str]:
    """
    Send a complaint to the SQS queue for async processing.
    Returns the SQS MessageId, or None if SQS is not configured.
    """
    queue_url = os.getenv("SQS_COMPLAINT_QUEUE_URL")
    if not queue_url:
        return None  # SQS not configured — caller falls back to sync processing

    payload = {
        "location": location,
        "category": category,
        "description": description,
        "timestamp": timestamp.isoformat(),
        "coordinates": list(coordinates) if coordinates else None,
        "enqueued_at": datetime.now().isoformat(),
    }

    try:
        resp = _get_client().send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(payload),
            MessageAttributes={
                "category": {"DataType": "String", "StringValue": category},
                "location": {"DataType": "String", "StringValue": location},
            },
        )
        msg_id = resp.get("MessageId")
        logger.info(f"[SQS] Enqueued complaint from {location} ({category}) — id={msg_id}")
        return msg_id
    except Exception as e:
        logger.warning(f"[SQS] Failed to enqueue complaint: {e}")
        return None


def process_sqs_event(event: dict, storage) -> int:
    """
    Process SQS trigger event from Lambda (batch of complaint messages).
    Called by lambda_handler when event source is SQS.
    Returns number of complaints processed.
    """
    from complaint_processor import get_complaint_processor

    records = event.get("Records", [])
    processed = 0

    for record in records:
        try:
            body = json.loads(record["body"])
            coords = body.get("coordinates")
            ts = datetime.fromisoformat(body["timestamp"])

            processor = get_complaint_processor()
            result = processor.submit_complaint(
                location=body["location"],
                category=body["category"],
                description=body["description"],
                timestamp=ts,
                coordinates=tuple(coords) if coords else None,
            )
            if result.success:
                processed += 1
                logger.info(f"[SQS] Processed complaint {result.complaint_id}")
            else:
                logger.warning(f"[SQS] Complaint rejected: {result.error_message}")
        except Exception as e:
            logger.error(f"[SQS] Failed to process record: {e}")

    return processed
