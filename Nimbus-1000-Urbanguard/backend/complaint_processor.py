"""
UrbanGuard AI System - Complaint Processor
Validates and stores citizen complaints
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from models import Complaint
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES
from storage import storage


@dataclass
class ComplaintResult:
    """
    Result of complaint submission.
    
    Attributes:
        success: Whether the complaint was successfully processed
        complaint_id: ID of the created complaint (if successful)
        error_message: Error description (if failed)
    """
    success: bool
    complaint_id: Optional[str] = None
    error_message: Optional[str] = None


class ComplaintProcessor:
    """
    Validates and processes citizen complaints.
    
    Validates:
    - Location must match predefined Bengaluru locations
    - Category must be one of 8 supported types
    - Required fields: location, category, description, timestamp
    """
    
    def validate_location(self, location: str) -> tuple[bool, Optional[str]]:
        """
        Validates location. Accepts any non-empty string — free-text addresses
        are supported since coordinates are now geocoded on the frontend.
        """
        if not location or not location.strip():
            return False, "Missing required field: location"
        return True, None
    
    def validate_category(self, category: str) -> tuple[bool, Optional[str]]:
        """
        Validates that category is one of the 8 supported types.
        
        Args:
            category: Category to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not category:
            return False, "Missing required field: category"
        
        if category not in COMPLAINT_CATEGORIES:
            categories_str = ", ".join(COMPLAINT_CATEGORIES)
            return False, f"Invalid category: {category}. Must be one of: {categories_str}"
        
        return True, None
    
    def validate_description(self, description: str) -> tuple[bool, Optional[str]]:
        """
        Validates that description is non-empty.
        
        Args:
            description: Description to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not description:
            return False, "Missing required field: description"
        
        if not isinstance(description, str):
            return False, "Invalid description: must be a string"
        
        if not description.strip():
            return False, "Invalid description: cannot be empty or whitespace only"
        
        return True, None
    
    def validate_timestamp(self, timestamp: datetime) -> tuple[bool, Optional[str]]:
        """
        Validates that timestamp is a valid datetime.
        
        Args:
            timestamp: Timestamp to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not timestamp:
            return False, "Missing required field: timestamp"
        
        if not isinstance(timestamp, datetime):
            return False, "Invalid timestamp: must be a datetime object"
        
        return True, None
    
    def validate_complaint(
        self,
        location: str,
        category: str,
        description: str,
        timestamp: datetime
    ) -> tuple[bool, Optional[str]]:
        """
        Validates all complaint fields.
        
        Args:
            location: Complaint location
            category: Complaint category
            description: Complaint description
            timestamp: Complaint timestamp
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate location
        is_valid, error_msg = self.validate_location(location)
        if not is_valid:
            return False, error_msg
        
        # Validate category
        is_valid, error_msg = self.validate_category(category)
        if not is_valid:
            return False, error_msg
        
        # Validate description
        is_valid, error_msg = self.validate_description(description)
        if not is_valid:
            return False, error_msg
        
        # Validate timestamp
        is_valid, error_msg = self.validate_timestamp(timestamp)
        if not is_valid:
            return False, error_msg
        
        return True, None
    
    def get_coordinates(self, location: str) -> tuple[float, float]:
        """Returns coordinates for a location, defaulting to Bengaluru centre."""
        return BENGALURU_LOCATIONS.get(location, (12.9716, 77.5946))
    
    def submit_complaint(
        self,
        location: str,
        category: str,
        description: str,
        timestamp: datetime,
        coordinates: tuple[float, float] | None = None
    ) -> ComplaintResult:
        """
        Validates and stores a citizen complaint.
        
        Args:
            location: Must match predefined Bengaluru_Location
            category: One of 8 supported types
            description: Free-text complaint details
            timestamp: Submission time
            
        Returns:
            ComplaintResult with success status and complaint_id or error message
            
        Performance:
            - Invalid data: < 100ms response
            - Valid data: < 500ms response including storage
        """
        # Validate the complaint
        is_valid, error_message = self.validate_complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp
        )
        
        if not is_valid:
            return ComplaintResult(
                success=False,
                error_message=error_message
            )
        
        # Generate unique complaint ID
        complaint_id = str(uuid4())
        
        # Use provided precise coordinates, or fall back to fixed location lookup
        coordinates = coordinates or self.get_coordinates(location)
        
        # Create complaint object
        complaint = Complaint(
            complaint_id=complaint_id,
            location=location,
            category=category,
            description=description,
            timestamp=timestamp,
            coordinates=coordinates,
            classification_confidence=1.0  # Default confidence
        )
        
        # Store complaint
        storage.add_complaint(complaint)
        
        # Return success confirmation
        return ComplaintResult(
            success=True,
            complaint_id=complaint_id
        )
    
    def get_all_complaints(self):
        """
        Retrieves all complaints sorted by timestamp descending.
        
        Returns:
            List of complaints with coordinates for map visualization
            
        Performance:
            - < 200ms for up to 1000 complaints
        """
        return storage.get_all_complaints()

    def _normalize_timestamp(self, timestamp: datetime) -> datetime:
        """
        Normalize timestamps so naive and aware datetimes can be compared safely.

        Args:
            timestamp: Timestamp to normalize

        Returns:
            Naive datetime for comparison
        """
        if hasattr(timestamp, "tzinfo") and timestamp.tzinfo is not None:
            return timestamp.replace(tzinfo=None)
        return timestamp

    def get_filtered_complaints(
        self,
        location: Optional[str] = None,
        category: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> List[Complaint]:
        """
        Retrieve complaints with optional filters and pagination.

        Args:
            location: Optional location filter
            category: Optional category filter
            since: Optional start timestamp (inclusive)
            until: Optional end timestamp (inclusive)
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Filtered, sorted list of complaints
        """
        complaints = storage.get_all_complaints()

        if location:
            complaints = [c for c in complaints if c.location == location]

        if category:
            complaints = [c for c in complaints if c.category == category]

        if since or until:
            normalized_since = self._normalize_timestamp(since) if since else None
            normalized_until = self._normalize_timestamp(until) if until else None

            filtered_complaints = []
            for complaint in complaints:
                complaint_ts = self._normalize_timestamp(complaint.timestamp)
                if normalized_since and complaint_ts < normalized_since:
                    continue
                if normalized_until and complaint_ts > normalized_until:
                    continue
                filtered_complaints.append(complaint)

            complaints = filtered_complaints

        if offset > 0:
            complaints = complaints[offset:]

        if limit is not None:
            complaints = complaints[:limit]

        return complaints


# Singleton instance
_complaint_processor_instance = None

def get_complaint_processor() -> ComplaintProcessor:
    """
    Returns singleton instance of ComplaintProcessor.
    
    Returns:
        ComplaintProcessor instance
    """
    global _complaint_processor_instance
    if _complaint_processor_instance is None:
        _complaint_processor_instance = ComplaintProcessor()
    return _complaint_processor_instance
