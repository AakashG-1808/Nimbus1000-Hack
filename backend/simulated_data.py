"""
UrbanGuard AI System - Simulated Data Generator
Generates 40+ simulated complaints for local development
"""
import random
from datetime import datetime, timedelta
from typing import List
from models import Complaint
from constants import BENGALURU_LOCATIONS, COMPLAINT_CATEGORIES


# Realistic complaint descriptions for each category
COMPLAINT_TEMPLATES = {
    "pothole": [
        "Large pothole on main road causing vehicle damage",
        "Deep crater in the middle of the street needs urgent repair",
        "Multiple potholes making the road dangerous for two-wheelers",
        "Road surface completely damaged with several holes",
        "Pothole near junction causing traffic slowdown",
    ],
    "flooding": [
        "Severe waterlogging after rain, road completely submerged",
        "Drainage overflow causing flooding in residential area",
        "Water accumulation on road due to blocked drains",
        "Heavy flooding making the street impassable",
        "Rainwater not draining, creating large puddles",
    ],
    "traffic": [
        "Heavy traffic congestion during peak hours",
        "Traffic signal not working causing chaos at junction",
        "Accident blocking main road, severe traffic jam",
        "Road construction causing major traffic delays",
        "Illegal parking blocking traffic flow",
    ],
    "garbage": [
        "Garbage pile not collected for several days, bad smell",
        "Overflowing waste bins attracting stray animals",
        "Illegal dumping of construction debris on roadside",
        "Garbage scattered across the street, unhygienic conditions",
        "Waste collection not happening regularly in this area",
    ],
    "streetlight": [
        "Street lights not working, area completely dark at night",
        "Multiple lamp posts damaged, need replacement",
        "Streetlight flickering and causing disturbance",
        "No lighting on main road, safety concern for pedestrians",
        "Broken streetlight pole leaning dangerously",
    ],
    "water_supply": [
        "No water supply for the past 3 days",
        "Water pipeline leaking, wasting large amounts of water",
        "Very low water pressure, unable to fill tanks",
        "Contaminated water supply, brownish color",
        "Water supply timing irregular, causing inconvenience",
    ],
    "noise": [
        "Construction noise starting very early in the morning",
        "Loud music from commercial establishment late at night",
        "Heavy vehicle traffic causing excessive noise pollution",
        "Generator running continuously, disturbing residents",
        "Loudspeaker noise from nearby event venue",
    ],
    "construction": [
        "Unauthorized construction blocking public pathway",
        "Construction debris dumped on road, causing obstruction",
        "Building work without proper safety measures",
        "Excavation work damaging adjacent property",
        "Construction dust causing air pollution and health issues",
    ],
}


def generate_simulated_complaints(count: int = 45) -> List[Complaint]:
    """
    Generate simulated complaints across Bengaluru locations.
    
    Args:
        count: Number of complaints to generate (default 45)
        
    Returns:
        List of simulated Complaint objects with realistic data
    """
    complaints = []
    locations = list(BENGALURU_LOCATIONS.keys())
    
    # Generate complaints with timestamps spread over the last 7 days
    now = datetime.now()
    
    for i in range(count):
        # Random location
        location = random.choice(locations)
        coordinates = BENGALURU_LOCATIONS[location]
        
        # Random category
        category = random.choice(COMPLAINT_CATEGORIES)
        
        # Random description from templates
        description = random.choice(COMPLAINT_TEMPLATES[category])
        
        # Random timestamp within last 7 days
        days_ago = random.uniform(0, 7)
        timestamp = now - timedelta(days=days_ago)
        
        # Random classification confidence (0.7 to 1.0 for simulated data)
        confidence = random.uniform(0.7, 1.0)
        
        complaint = Complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp,
            coordinates=coordinates,
            classification_confidence=confidence,
        )
        
        complaints.append(complaint)
    
    return complaints


def generate_clustered_complaints(
    location: str, 
    category: str, 
    count: int = 5
) -> List[Complaint]:
    """
    Generate a cluster of complaints at a specific location.
    Useful for testing high-density cluster detection.
    
    Args:
        location: Bengaluru location name
        category: Complaint category
        count: Number of complaints in cluster (default 5)
        
    Returns:
        List of complaints at the same location within 24 hours
    """
    if location not in BENGALURU_LOCATIONS:
        raise ValueError(f"Invalid location: {location}")
    
    if category not in COMPLAINT_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")
    
    complaints = []
    coordinates = BENGALURU_LOCATIONS[location]
    now = datetime.now()
    
    for i in range(count):
        # Random description from templates
        description = random.choice(COMPLAINT_TEMPLATES[category])
        
        # Random timestamp within last 24 hours
        hours_ago = random.uniform(0, 24)
        timestamp = now - timedelta(hours=hours_ago)
        
        complaint = Complaint(
            location=location,
            category=category,
            description=description,
            timestamp=timestamp,
            coordinates=coordinates,
            classification_confidence=0.9,
        )
        
        complaints.append(complaint)
    
    return complaints


def initialize_storage_with_simulated_data(storage) -> int:
    """
    Initialize storage with 40+ simulated complaints.
    
    Args:
        storage: InMemoryStorage instance to populate
        
    Returns:
        Number of complaints added
    """
    # Generate 45 random complaints
    complaints = generate_simulated_complaints(45)
    
    # Add all complaints to storage
    for complaint in complaints:
        storage.add_complaint(complaint)
    
    return len(complaints)
