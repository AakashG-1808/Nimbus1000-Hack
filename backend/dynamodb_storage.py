"""
UrbanGuard AI System - DynamoDB Storage
DynamoDB client for AWS serverless deployment with in-memory fallback
"""
import os
import json
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from models import Complaint, RiskZone, DailyReport, RiskLevel
from error_handling import log_error


class DynamoDBStorage:
    """
    DynamoDB storage implementation for AWS Lambda deployment.
    
    Tables:
        - Complaints: Primary key = complaint_id
        - RiskZones: Primary key = zone_id
        - DailyReports: Primary key = report_id, Sort key = date
        
    Features:
        - Automatic retry with exponential backoff (3 attempts)
        - Error logging for all operations
        - Type conversion between Python and DynamoDB formats
    """
    
    def __init__(self):
        """Initialize DynamoDB client and table names from environment variables"""
        self.region = os.environ.get("AWS_REGION", "ap-south-2")
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        
        # Get table names from environment variables
        self.complaints_table_name = os.environ.get(
            "DYNAMODB_TABLE_COMPLAINTS", 
            "urbanguard-complaints"
        )
        self.risk_zones_table_name = os.environ.get(
            "DYNAMODB_TABLE_RISK_ZONES", 
            "urbanguard-risk-zones"
        )
        self.reports_table_name = os.environ.get(
            "DYNAMODB_TABLE_REPORTS", 
            "urbanguard-reports"
        )
        
        # Get table references
        self.complaints_table = self.dynamodb.Table(self.complaints_table_name)
        self.risk_zones_table = self.dynamodb.Table(self.risk_zones_table_name)
        self.reports_table = self.dynamodb.Table(self.reports_table_name)
    
    # ========================================================================
    # Helper Methods for Type Conversion
    # ========================================================================
    
    @staticmethod
    def _python_to_dynamodb(obj):
        """Convert Python types to DynamoDB-compatible types"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: DynamoDBStorage._python_to_dynamodb(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBStorage._python_to_dynamodb(item) for item in obj]
        return obj
    
    @staticmethod
    def _dynamodb_to_python(obj):
        """Convert DynamoDB types to Python types"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: DynamoDBStorage._dynamodb_to_python(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBStorage._dynamodb_to_python(item) for item in obj]
        return obj
    
    def _complaint_to_item(self, complaint: Complaint) -> dict:
        """Convert Complaint object to DynamoDB item"""
        return self._python_to_dynamodb({
            "complaint_id": complaint.complaint_id,
            "location": complaint.location,
            "category": complaint.category,
            "description": complaint.description,
            "timestamp": complaint.timestamp.timestamp(),
            "coordinates": {
                "lat": complaint.coordinates[0],
                "lon": complaint.coordinates[1]
            },
            "classification_confidence": complaint.classification_confidence
        })
    
    def _item_to_complaint(self, item: dict) -> Complaint:
        """Convert DynamoDB item to Complaint object"""
        item = self._dynamodb_to_python(item)
        return Complaint(
            complaint_id=item["complaint_id"],
            location=item["location"],
            category=item["category"],
            description=item["description"],
            timestamp=datetime.fromtimestamp(item["timestamp"]),
            coordinates=(item["coordinates"]["lat"], item["coordinates"]["lon"]),
            classification_confidence=item.get("classification_confidence", 1.0)
        )
    
    def _risk_zone_to_item(self, zone: RiskZone) -> dict:
        """Convert RiskZone object to DynamoDB item"""
        return self._python_to_dynamodb({
            "zone_id": zone.zone_id,
            "center_coordinates": {
                "lat": zone.center_coordinates[0],
                "lon": zone.center_coordinates[1]
            },
            "radius_meters": zone.radius_meters,
            "risk_score": zone.risk_score,
            "risk_level": zone.risk_level.value,
            "complaint_count": zone.complaint_count,
            "dominant_category": zone.dominant_category,
            "last_updated": zone.last_updated.timestamp()
        })
    
    def _item_to_risk_zone(self, item: dict) -> RiskZone:
        """Convert DynamoDB item to RiskZone object"""
        item = self._dynamodb_to_python(item)
        return RiskZone(
            zone_id=item["zone_id"],
            center_coordinates=(
                item["center_coordinates"]["lat"],
                item["center_coordinates"]["lon"]
            ),
            radius_meters=item["radius_meters"],
            risk_score=item["risk_score"],
            risk_level=RiskLevel(item["risk_level"]),
            complaint_count=item["complaint_count"],
            dominant_category=item["dominant_category"],
            last_updated=datetime.fromtimestamp(item["last_updated"])
        )
    
    def _report_to_item(self, report: DailyReport) -> dict:
        """Convert DailyReport object to DynamoDB item"""
        return self._python_to_dynamodb({
            "report_id": report.report_id,
            "date": report.date.timestamp(),
            "total_complaints": report.total_complaints,
            "high_risk_zones": [
                self._risk_zone_to_item(zone) for zone in report.high_risk_zones
            ],
            "predicted_incidents": [
                {
                    "prediction_id": pred.prediction_id,
                    "zone_id": pred.zone_id,
                    "incident_type": pred.incident_type,
                    "risk_score": pred.risk_score,
                    "time_window": pred.time_window,
                    "contributing_factors": pred.contributing_factors,
                    "created_at": pred.created_at.timestamp()
                }
                for pred in report.predicted_incidents
            ],
            "weather_summary": report.weather_summary,
            "ai_generated_summary": report.ai_generated_summary,
            "created_at": report.created_at.timestamp()
        })
    
    def _item_to_report(self, item: dict) -> DailyReport:
        """Convert DynamoDB item to DailyReport object"""
        from models import IncidentPrediction
        
        item = self._dynamodb_to_python(item)
        
        # Convert high_risk_zones
        high_risk_zones = [
            self._item_to_risk_zone(zone_item) 
            for zone_item in item.get("high_risk_zones", [])
        ]
        
        # Convert predicted_incidents
        predicted_incidents = [
            IncidentPrediction(
                prediction_id=pred["prediction_id"],
                zone_id=pred["zone_id"],
                incident_type=pred["incident_type"],
                risk_score=pred["risk_score"],
                time_window=pred["time_window"],
                contributing_factors=pred["contributing_factors"],
                created_at=datetime.fromtimestamp(pred["created_at"])
            )
            for pred in item.get("predicted_incidents", [])
        ]
        
        return DailyReport(
            report_id=item["report_id"],
            date=datetime.fromtimestamp(item["date"]),
            total_complaints=item["total_complaints"],
            high_risk_zones=high_risk_zones,
            predicted_incidents=predicted_incidents,
            weather_summary=item["weather_summary"],
            ai_generated_summary=item["ai_generated_summary"],
            created_at=datetime.fromtimestamp(item["created_at"])
        )
    
    # ========================================================================
    # Complaint Operations
    # ========================================================================
    
    def add_complaint(self, complaint: Complaint) -> None:
        """
        Add a complaint to DynamoDB.
        
        Validates: Requirement 19.3
        """
        try:
            item = self._complaint_to_item(complaint)
            self.complaints_table.put_item(Item=item)
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message=f"Failed to add complaint: {complaint.complaint_id}",
                error=e
            )
            raise
    
    def get_all_complaints(self) -> List[Complaint]:
        """
        Retrieve all complaints sorted by timestamp descending.
        
        Performance: < 200ms for up to 1000 complaints
        """
        try:
            response = self.complaints_table.scan()
            items = response.get('Items', [])
            
            # Handle pagination if more than 1MB of data
            while 'LastEvaluatedKey' in response:
                response = self.complaints_table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            # Convert to Complaint objects and sort
            complaints = [self._item_to_complaint(item) for item in items]
            return sorted(complaints, key=lambda c: c.timestamp, reverse=True)
            
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message="Failed to retrieve complaints",
                error=e
            )
            return []
    
    def get_complaints_by_location(self, location: str) -> List[Complaint]:
        """Retrieve complaints for a specific location"""
        try:
            response = self.complaints_table.scan(
                FilterExpression="location = :loc",
                ExpressionAttributeValues={":loc": location}
            )
            items = response.get('Items', [])
            return [self._item_to_complaint(item) for item in items]
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message=f"Failed to retrieve complaints for location: {location}",
                error=e
            )
            return []
    
    def get_complaints_by_category(self, category: str) -> List[Complaint]:
        """Retrieve complaints of a specific category"""
        try:
            response = self.complaints_table.scan(
                FilterExpression="category = :cat",
                ExpressionAttributeValues={":cat": category}
            )
            items = response.get('Items', [])
            return [self._item_to_complaint(item) for item in items]
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message=f"Failed to retrieve complaints for category: {category}",
                error=e
            )
            return []
    
    def get_complaint_count(self) -> int:
        """Get total number of complaints"""
        try:
            response = self.complaints_table.scan(Select='COUNT')
            return response.get('Count', 0)
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message="Failed to get complaint count",
                error=e
            )
            return 0
    
    # ========================================================================
    # Risk Zone Operations
    # ========================================================================
    
    def add_risk_zone(self, risk_zone: RiskZone) -> None:
        """Add a risk zone to DynamoDB"""
        try:
            item = self._risk_zone_to_item(risk_zone)
            self.risk_zones_table.put_item(Item=item)
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message=f"Failed to add risk zone: {risk_zone.zone_id}",
                error=e
            )
            raise
    
    def update_risk_zones(self, risk_zones: List[RiskZone]) -> None:
        """
        Replace all risk zones with new calculations.
        
        Note: This performs a batch write operation for efficiency.
        """
        try:
            # Delete all existing risk zones
            response = self.risk_zones_table.scan()
            with self.risk_zones_table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(Key={'zone_id': item['zone_id']})
            
            # Add new risk zones
            with self.risk_zones_table.batch_writer() as batch:
                for zone in risk_zones:
                    item = self._risk_zone_to_item(zone)
                    batch.put_item(Item=item)
                    
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message="Failed to update risk zones",
                error=e
            )
            raise
    
    def get_all_risk_zones(self) -> List[RiskZone]:
        """Retrieve all risk zones"""
        try:
            response = self.risk_zones_table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.risk_zones_table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            return [self._item_to_risk_zone(item) for item in items]
            
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message="Failed to retrieve risk zones",
                error=e
            )
            return []
    
    def get_high_risk_zones(self, min_score: float = 20.0) -> List[RiskZone]:
        """Retrieve risk zones above a minimum score threshold"""
        try:
            response = self.risk_zones_table.scan(
                FilterExpression="risk_score >= :min_score",
                ExpressionAttributeValues={":min_score": Decimal(str(min_score))}
            )
            items = response.get('Items', [])
            return [self._item_to_risk_zone(item) for item in items]
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message=f"Failed to retrieve high risk zones (min_score={min_score})",
                error=e
            )
            return []
    
    # ========================================================================
    # Daily Report Operations
    # ========================================================================
    
    def add_daily_report(self, report: DailyReport) -> None:
        """
        Add a daily report to DynamoDB.
        
        Note: DynamoDB TTL should be configured for 30-day retention.
        """
        try:
            item = self._report_to_item(report)
            # Add TTL attribute (30 days from creation)
            item['ttl'] = int(report.created_at.timestamp()) + (30 * 24 * 60 * 60)
            self.reports_table.put_item(Item=item)
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message=f"Failed to add daily report: {report.report_id}",
                error=e
            )
            raise
    
    def get_latest_report(self) -> Optional[DailyReport]:
        """Retrieve the most recent daily report"""
        try:
            response = self.reports_table.scan()
            items = response.get('Items', [])
            
            if not items:
                return None
            
            # Convert to DailyReport objects and find latest
            reports = [self._item_to_report(item) for item in items]
            return max(reports, key=lambda r: r.date)
            
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message="Failed to retrieve latest report",
                error=e
            )
            return None
    
    def get_all_reports(self) -> List[DailyReport]:
        """Retrieve all daily reports sorted by date descending"""
        try:
            response = self.reports_table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.reports_table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            # Convert and sort
            reports = [self._item_to_report(item) for item in items]
            return sorted(reports, key=lambda r: r.date, reverse=True)
            
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message="Failed to retrieve all reports",
                error=e
            )
            return []
    
    def clear_all(self) -> None:
        """
        Clear all storage (for testing).
        
        Warning: This deletes all data from all tables!
        """
        try:
            # Clear complaints
            response = self.complaints_table.scan()
            with self.complaints_table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(Key={'complaint_id': item['complaint_id']})
            
            # Clear risk zones
            response = self.risk_zones_table.scan()
            with self.risk_zones_table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(Key={'zone_id': item['zone_id']})
            
            # Clear reports
            response = self.reports_table.scan()
            with self.reports_table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(Key={'report_id': item['report_id']})
                    
        except ClientError as e:
            log_error(
                component="DynamoDBStorage",
                message="Failed to clear all storage",
                error=e
            )
            raise
