"""
UrbanGuard AI System - In-Memory Data Storage
Storage classes for complaints, risk zones, and reports
"""
from typing import List, Dict, Optional
from datetime import datetime
from models import Complaint, RiskZone, DailyReport
import threading


class InMemoryStorage:
    """
    Thread-safe in-memory storage for local development.
    Stores complaints, risk zones, and daily reports.
    """
    
    def __init__(self):
        """Initialize empty storage with thread locks"""
        self._complaints: List[Complaint] = []
        self._risk_zones: List[RiskZone] = []
        self._daily_reports: List[DailyReport] = []
        self._lock = threading.Lock()
    
    # Complaint operations
    def add_complaint(self, complaint: Complaint) -> None:
        """Add a complaint to storage"""
        with self._lock:
            self._complaints.append(complaint)
    
    def get_all_complaints(self) -> List[Complaint]:
        """Retrieve all complaints sorted by timestamp descending"""
        with self._lock:
            # Sort complaints, handling both timezone-aware and naive datetimes
            def get_timestamp(complaint):
                ts = complaint.timestamp
                # Convert timezone-aware to naive for comparison
                if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                    return ts.replace(tzinfo=None)
                return ts
            
            return sorted(self._complaints, key=get_timestamp, reverse=True)
    
    def get_complaints_by_location(self, location: str) -> List[Complaint]:
        """Retrieve complaints for a specific location"""
        with self._lock:
            return [c for c in self._complaints if c.location == location]
    
    def get_complaints_by_category(self, category: str) -> List[Complaint]:
        """Retrieve complaints of a specific category"""
        with self._lock:
            return [c for c in self._complaints if c.category == category]
    
    def get_complaint_count(self) -> int:
        """Get total number of complaints"""
        with self._lock:
            return len(self._complaints)
    
    # Risk zone operations
    def add_risk_zone(self, risk_zone: RiskZone) -> None:
        """Add a risk zone to storage"""
        with self._lock:
            self._risk_zones.append(risk_zone)
    
    def update_risk_zones(self, risk_zones: List[RiskZone]) -> None:
        """Replace all risk zones with new calculations"""
        with self._lock:
            self._risk_zones = risk_zones
    
    def get_all_risk_zones(self) -> List[RiskZone]:
        """Retrieve all risk zones"""
        with self._lock:
            return self._risk_zones.copy()
    
    def get_high_risk_zones(self, min_score: float = 20.0) -> List[RiskZone]:
        """Retrieve risk zones above a minimum score threshold"""
        with self._lock:
            return [z for z in self._risk_zones if z.risk_score >= min_score]
    
    # Daily report operations
    def add_daily_report(self, report: DailyReport) -> None:
        """Add a daily report to storage"""
        with self._lock:
            self._daily_reports.append(report)
            # Keep only last 30 days of reports
            if len(self._daily_reports) > 30:
                self._daily_reports = sorted(
                    self._daily_reports, 
                    key=lambda r: r.date, 
                    reverse=True
                )[:30]
    
    def get_latest_report(self) -> Optional[DailyReport]:
        """Retrieve the most recent daily report"""
        with self._lock:
            if not self._daily_reports:
                return None
            return max(self._daily_reports, key=lambda r: r.date)
    
    def get_all_reports(self) -> List[DailyReport]:
        """Retrieve all daily reports sorted by date descending"""
        with self._lock:
            return sorted(self._daily_reports, key=lambda r: r.date, reverse=True)
    
    def clear_all(self) -> None:
        """Clear all storage (for testing)"""
        with self._lock:
            self._complaints.clear()
            self._risk_zones.clear()
            self._daily_reports.clear()


# Global storage instance
storage = InMemoryStorage()
