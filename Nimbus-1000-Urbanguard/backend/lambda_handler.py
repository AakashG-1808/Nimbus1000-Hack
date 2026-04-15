"""
UrbanGuard AI System - AWS Lambda Handler
Lambda handler wrapper for FastAPI using Mangum adapter.
Also handles SQS trigger events for async complaint processing.
"""
import os
from mangum import Mangum
from main import app

# Create Lambda handler using Mangum adapter
handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    Routes to SQS processor for SQS trigger events,
    otherwise delegates to FastAPI via Mangum for API Gateway events.
    """
    # SQS trigger — process queued complaints asynchronously
    if event.get("Records") and event["Records"][0].get("eventSource") == "aws:sqs":
        from sqs_handler import process_sqs_event
        from storage import storage
        count = process_sqs_event(event, storage)
        return {"statusCode": 200, "body": f"Processed {count} complaints from SQS"}

    # EventBridge scheduled rule — generate daily report
    if event.get("source") == "aws.events" or event.get("detail-type") == "Scheduled Event":
        try:
            from report_generator import get_report_generator
            from storage import storage
            from weather_integrator import get_weather_integrator
            from risk_engine import get_risk_engine
            rg = get_report_generator()
            report = rg.generate_daily_report()
            # Also save to S3
            try:
                from s3_storage import save_daily_report
                save_daily_report({
                    "report_id": report.report_id,
                    "date": report.date.isoformat(),
                    "total_complaints": report.total_complaints,
                    "ai_generated_summary": report.ai_generated_summary,
                    "high_risk_zone_count": len(report.high_risk_zones),
                })
            except Exception:
                pass
            # SNS notification
            try:
                from sns_notifier import notify_daily_report
                notify_daily_report(
                    report.ai_generated_summary,
                    report.total_complaints,
                    len(report.high_risk_zones),
                )
            except Exception:
                pass
            return {"statusCode": 200, "body": "Daily report generated"}
        except Exception as e:
            return {"statusCode": 500, "body": f"Report generation failed: {e}"}

    # Default: API Gateway → FastAPI
    return handler(event, context)
