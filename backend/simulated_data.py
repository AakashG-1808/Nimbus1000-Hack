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
        "Huge pothole appeared after last week's rain, damaging car tires",
        "Road has developed dangerous potholes, already caused 2 accidents",
        "Deep hole in road near bus stop, pedestrians at risk",
        "Pothole filled with water, impossible to see depth",
        "Several small potholes merged into one large crater",
        "Road completely broken near school, children's safety at risk",
        "Pothole on flyover ramp causing vehicles to swerve dangerously",
        "Auto rickshaw fell into pothole yesterday, driver injured",
        "Road patch work failed, pothole reappeared within a week",
        "Massive pothole blocking half the road width",
    ],
    "flooding": [
        "Severe waterlogging after rain, road completely submerged",
        "Drainage overflow causing flooding in residential area",
        "Water accumulation on road due to blocked drains",
        "Heavy flooding making the street impassable",
        "Rainwater not draining, creating large puddles",
        "Knee-deep water on main road after 2 hours of rain",
        "Manhole overflowing, sewage water flooding the street",
        "Entire street flooded, water entering ground floor homes",
        "Storm drain blocked with plastic waste, causing severe flooding",
        "Water stagnation for 3 days, mosquito breeding concern",
        "Flash flooding during evening rush hour, vehicles stranded",
        "Underground parking flooded, multiple cars damaged",
        "Drainage system completely overwhelmed, water up to waist level",
        "Road turned into river after heavy rain, traffic diverted",
        "Basement apartments flooded, residents evacuated",
    ],
    "traffic": [
        "Heavy traffic congestion during peak hours",
        "Traffic signal not working causing chaos at junction",
        "Accident blocking main road, severe traffic jam",
        "Road construction causing major traffic delays",
        "Illegal parking blocking traffic flow",
        "Traffic backed up for 2km, taking 45 minutes to cross junction",
        "Signal timing completely wrong, causing massive jams",
        "Bus breakdown blocking entire lane during morning rush",
        "Traffic police absent, complete chaos at busy intersection",
        "Road narrowed due to construction, severe bottleneck",
        "Truck overturned, blocking both lanes for hours",
        "Traffic jam due to VIP movement, no alternate route",
        "School zone congestion, parents parking on main road",
        "Metro construction blocking 2 lanes, traffic nightmare",
        "Delivery trucks double-parked, blocking traffic completely",
    ],
    "garbage": [
        "Garbage pile not collected for several days, bad smell",
        "Overflowing waste bins attracting stray animals",
        "Illegal dumping of construction debris on roadside",
        "Garbage scattered across the street, unhygienic conditions",
        "Waste collection not happening regularly in this area",
        "Garbage truck hasn't come for 5 days, pile growing huge",
        "Stray dogs tearing open garbage bags, waste everywhere",
        "Foul smell from rotting garbage, residents complaining",
        "Commercial waste dumped in residential area illegally",
        "Garbage bin overflowing for weeks, rats and cockroaches everywhere",
        "Medical waste found mixed with regular garbage, health hazard",
        "Plastic waste blocking storm drain, needs immediate clearing",
        "Restaurant dumping food waste on street at night",
        "E-waste dumped near park, toxic materials exposed",
        "Garbage collection schedule not followed, area becoming dump yard",
    ],
    "streetlight": [
        "Street lights not working, area completely dark at night",
        "Multiple lamp posts damaged, need replacement",
        "Streetlight flickering and causing disturbance",
        "No lighting on main road, safety concern for pedestrians",
        "Broken streetlight pole leaning dangerously",
        "All streetlights on this road out for 2 weeks, very unsafe",
        "Streetlight pole knocked down by vehicle, wires exposed",
        "Only 2 out of 15 streetlights working, area pitch dark",
        "Streetlight stays on during day, wastes electricity",
        "Broken glass from streetlight on footpath, dangerous",
        "Streetlight near ATM not working, security concern",
        "Entire street dark, women afraid to walk at night",
        "Streetlight bulbs stolen, need immediate replacement",
        "Faulty wiring causing streetlights to short circuit",
        "No streetlights near bus stop, commuters struggling",
    ],
    "water_supply": [
        "No water supply for the past 3 days",
        "Water pipeline leaking, wasting large amounts of water",
        "Very low water pressure, unable to fill tanks",
        "Contaminated water supply, brownish color",
        "Water supply timing irregular, causing inconvenience",
        "Water comes only for 30 minutes daily, insufficient",
        "Major pipeline burst, water gushing out for hours",
        "Muddy water coming from taps, unfit for drinking",
        "Water supply stopped without notice, no tanker arranged",
        "Leaking pipe under road creating huge puddle",
        "Water pressure so low, upper floors getting no water",
        "Foul smell in water supply, possible sewage contamination",
        "Water meter broken, unable to track consumption",
        "Pipeline repair work ongoing, no water for 2 days",
        "Illegal water connection causing low pressure for others",
    ],
    "noise": [
        "Construction noise starting very early in the morning",
        "Loud music from commercial establishment late at night",
        "Heavy vehicle traffic causing excessive noise pollution",
        "Generator running continuously, disturbing residents",
        "Loudspeaker noise from nearby event venue",
        "Construction work starting at 6 AM, disturbing sleep",
        "Pub playing loud music till 2 AM, violating rules",
        "Heavy trucks passing at night, house vibrating",
        "Wedding hall using loudspeakers beyond permitted hours",
        "Industrial generator noise 24/7, unbearable for residents",
        "Religious place using loudspeakers at 5 AM daily",
        "Bar with outdoor seating, loud music till midnight",
        "Construction drilling noise throughout the day",
        "Motorcycle racing on street at night, very loud",
        "Factory siren going off randomly, disturbing neighborhood",
    ],
    "construction": [
        "Unauthorized construction blocking public pathway",
        "Construction debris dumped on road, causing obstruction",
        "Building work without proper safety measures",
        "Excavation work damaging adjacent property",
        "Construction dust causing air pollution and health issues",
        "Illegal construction on footpath, pedestrians forced on road",
        "Construction material stored on public road for weeks",
        "Building demolition without safety net, debris falling",
        "Excavation pit left open without barricades, very dangerous",
        "Construction workers living on site, hygiene issues",
        "Cement mixing on road, making it slippery",
        "High-rise construction without proper permits",
        "Construction crane blocking entire street",
        "Digging work damaged water pipeline, causing leakage",
        "Construction site has no safety signage, accidents waiting to happen",
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
    
    # Track used descriptions to avoid immediate repetition
    used_descriptions = set()
    
    for i in range(count):
        # Random location
        location = random.choice(locations)
        coordinates = BENGALURU_LOCATIONS[location]
        
        # Random category with weighted distribution (some categories more common)
        category_weights = {
            'pothole': 0.20,
            'traffic': 0.18,
            'garbage': 0.15,
            'flooding': 0.12,
            'water_supply': 0.12,
            'streetlight': 0.10,
            'construction': 0.08,
            'noise': 0.05,
        }
        category = random.choices(
            list(category_weights.keys()),
            weights=list(category_weights.values())
        )[0]
        
        # Get available descriptions for this category
        available_descriptions = [
            desc for desc in COMPLAINT_TEMPLATES[category]
            if desc not in used_descriptions
        ]
        
        # If all descriptions used, reset the tracking
        if not available_descriptions:
            used_descriptions.clear()
            available_descriptions = COMPLAINT_TEMPLATES[category]
        
        # Random description from templates
        description = random.choice(available_descriptions)
        used_descriptions.add(description)
        
        # More realistic timestamp distribution:
        # 40% in last 24 hours, 30% in last 3 days, 30% in last 7 days
        rand = random.random()
        if rand < 0.4:
            # Recent complaints (last 24 hours)
            hours_ago = random.uniform(0, 24)
            timestamp = now - timedelta(hours=hours_ago)
        elif rand < 0.7:
            # Medium age (1-3 days ago)
            days_ago = random.uniform(1, 3)
            timestamp = now - timedelta(days=days_ago)
        else:
            # Older complaints (3-7 days ago)
            days_ago = random.uniform(3, 7)
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
    # Generate 60 random complaints for more variety
    complaints = generate_simulated_complaints(60)
    
    # Add all complaints to storage
    for complaint in complaints:
        storage.add_complaint(complaint)
    
    return len(complaints)
