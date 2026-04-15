"""
UrbanGuard AI System - Constants
Bengaluru locations and complaint categories
"""
from typing import Dict, Tuple, List

# 40+ Bengaluru locations with coordinates (latitude, longitude)
BENGALURU_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "Koramangala": (12.9352, 77.6245),
    "Indiranagar": (12.9716, 77.6412),
    "Whitefield": (12.9698, 77.7499),
    "Electronic City": (12.8456, 77.6603),
    "Jayanagar": (12.9250, 77.5838),
    "Malleshwaram": (13.0039, 77.5727),
    "HSR Layout": (12.9116, 77.6473),
    "BTM Layout": (12.9166, 77.6101),
    "Marathahalli": (12.9591, 77.7011),
    "Bannerghatta Road": (12.8892, 77.5957),
    "Yelahanka": (13.1007, 77.5963),
    "Hebbal": (13.0358, 77.5970),
    "Rajajinagar": (12.9916, 77.5544),
    "Basavanagudi": (12.9423, 77.5742),
    "JP Nagar": (12.9077, 77.5854),
    "Sarjapur Road": (12.9121, 77.6871),
    "Bellandur": (12.9259, 77.6766),
    "Bommanahalli": (12.9141, 77.6257),
    "Mahadevapura": (12.9899, 77.6988),
    "Yeshwanthpur": (13.0280, 77.5385),
    "KR Puram": (13.0092, 77.6957),
    "Ramamurthy Nagar": (13.0103, 77.6774),
    "CV Raman Nagar": (12.9850, 77.6680),
    "Hoodi": (12.9899, 77.7119),
    "Varthur": (12.9350, 77.7513),
    "Kadugodi": (12.9899, 77.7588),
    "Brookefield": (12.9716, 77.7137),
    "Domlur": (12.9611, 77.6387),
    "Ulsoor": (12.9810, 77.6190),
    "Frazer Town": (12.9890, 77.6090),
    "Richmond Town": (12.9716, 77.6031),
    "Shivajinagar": (12.9897, 77.6012),
    "Sadashivanagar": (13.0050, 77.5750),
    "Vijayanagar": (12.9716, 77.5322),
    "Peenya": (13.0297, 77.5200),
    "Jalahalli": (13.0430, 77.5600),
    "Nagarbhavi": (12.9580, 77.5020),
    "Kengeri": (12.9077, 77.4854),
    "Banashankari": (12.9250, 77.5480),
    "Girinagar": (12.9350, 77.5580),
    "Uttarahalli": (12.8950, 77.5350),
    "Rajarajeshwari Nagar": (12.9077, 77.5200),
    "Vijayanagar": (12.9716, 77.5322),
    "Chickpet": (12.9634, 77.5855),
    "Shantinagar": (12.9716, 77.6031),
}

# 8 supported complaint categories
COMPLAINT_CATEGORIES: List[str] = [
    "pothole",
    "flooding",
    "traffic",
    "garbage",
    "streetlight",
    "water_supply",
    "noise",
    "construction",
]

# Category keywords for fallback classification
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "pothole": ["pothole", "road damage", "crater", "hole in road", "broken road"],
    "flooding": ["flood", "water logging", "waterlogged", "drainage", "overflow", "rain water"],
    "traffic": ["traffic", "congestion", "jam", "signal", "accident", "vehicle"],
    "garbage": ["garbage", "waste", "trash", "litter", "dump", "dirty", "smell"],
    "streetlight": ["streetlight", "street light", "lamp", "lighting", "dark", "bulb"],
    "water_supply": ["water supply", "no water", "water shortage", "tap", "pipeline", "leak"],
    "noise": ["noise", "loud", "sound", "disturbance", "pollution"],
    "construction": ["construction", "building", "debris", "dust", "excavation", "work"],
}
