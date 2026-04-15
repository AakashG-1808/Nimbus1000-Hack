"""
UrbanGuard AI System - S3 Storage
Persists BBMP CSV datasets and daily reports to S3.
Bucket name is read from S3_BUCKET_NAME env var.
"""
import io
import json
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-2"))
    return _s3_client


def _bucket() -> Optional[str]:
    return os.getenv("S3_BUCKET_NAME")


# ── BBMP Dataset ──────────────────────────────────────────────────────────────

def upload_bbmp_csv(local_path: str) -> bool:
    """Upload a BBMP CSV file to S3 under bbmp-data/ prefix."""
    bucket = _bucket()
    if not bucket:
        return False
    key = f"bbmp-data/{os.path.basename(local_path)}"
    try:
        _get_client().upload_file(local_path, bucket, key)
        logger.info(f"[S3] Uploaded {local_path} → s3://{bucket}/{key}")
        return True
    except Exception as e:
        logger.warning(f"[S3] Upload failed: {e}")
        return False


def download_bbmp_csvs(local_dir: str) -> int:
    """
    Download all BBMP CSVs from s3://<bucket>/bbmp-data/ to local_dir.
    Returns number of files downloaded.
    """
    bucket = _bucket()
    if not bucket:
        return 0
    try:
        paginator = _get_client().get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix="bbmp-data/")
        count = 0
        os.makedirs(local_dir, exist_ok=True)
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".csv"):
                    continue
                filename = os.path.basename(key)
                dest = os.path.join(local_dir, filename)
                _get_client().download_file(bucket, key, dest)
                logger.info(f"[S3] Downloaded s3://{bucket}/{key} → {dest}")
                count += 1
        return count
    except Exception as e:
        logger.warning(f"[S3] Download failed: {e}")
        return 0


# ── Daily Reports ─────────────────────────────────────────────────────────────

def save_daily_report(report_dict: dict) -> bool:
    """
    Save a daily report as JSON to s3://<bucket>/reports/YYYY-MM-DD.json
    """
    bucket = _bucket()
    if not bucket:
        return False
    date_str = datetime.now().strftime("%Y-%m-%d")
    key = f"reports/{date_str}.json"
    try:
        body = json.dumps(report_dict, default=str).encode("utf-8")
        _get_client().put_object(Bucket=bucket, Key=key, Body=body,
                                  ContentType="application/json")
        logger.info(f"[S3] Saved daily report → s3://{bucket}/{key}")
        return True
    except Exception as e:
        logger.warning(f"[S3] Failed to save report: {e}")
        return False


def load_latest_report() -> Optional[dict]:
    """Load the most recent daily report JSON from S3."""
    bucket = _bucket()
    if not bucket:
        return None
    try:
        paginator = _get_client().get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix="reports/")
        keys = []
        for page in pages:
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".json"):
                    keys.append(obj["Key"])
        if not keys:
            return None
        latest_key = sorted(keys)[-1]
        resp = _get_client().get_object(Bucket=bucket, Key=latest_key)
        return json.loads(resp["Body"].read())
    except Exception as e:
        logger.warning(f"[S3] Failed to load report: {e}")
        return None


# ── BBMP Insights Cache ───────────────────────────────────────────────────────

def save_bbmp_insights(insights: dict) -> bool:
    """Persist Bedrock-generated BBMP insights to S3 so they survive Lambda restarts."""
    bucket = _bucket()
    if not bucket:
        return False
    try:
        body = json.dumps(insights, default=str).encode("utf-8")
        _get_client().put_object(Bucket=bucket, Key="bbmp-insights/latest.json",
                                  Body=body, ContentType="application/json")
        logger.info("[S3] Saved BBMP insights cache")
        return True
    except Exception as e:
        logger.warning(f"[S3] Failed to save insights: {e}")
        return False


def load_bbmp_insights() -> Optional[dict]:
    """Load cached BBMP insights from S3 (avoids re-running Bedrock on every cold start)."""
    bucket = _bucket()
    if not bucket:
        return None
    try:
        resp = _get_client().get_object(Bucket=bucket, Key="bbmp-insights/latest.json")
        return json.loads(resp["Body"].read())
    except Exception as e:
        logger.debug(f"[S3] No cached insights found: {e}")
        return None
