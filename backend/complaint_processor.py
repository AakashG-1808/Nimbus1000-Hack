"""
UrbanGuard AI System - Complaint Processor
Validates and stores citizen complaints
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
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
        Validates that location exists in Bengaluru locations.
        
        Args:
            location: Location name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not location:
            return False, "Missing required field: location"
        
        if location not in BENGALURU_LOCATIONS:
            return False, f"Invalid location: {location} not found in Bengaluru locations"
        
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
        """
        Retrieves coordinates for a valid Bengaluru location.
        
        Args:
            location: Valid Bengaluru location name
            
        Returns:
            Tuple of (latitude, longitude)
        """
        return BENGALURU_LOCATIONS[location]
    
    def submit_complaint(
        self,
        location: str,
        category: str,
        description: str,
        timestamp: datetime
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
        
        # Look up coordinates from location
        coordinates = self.get_coordinates(location)
        
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
