"""
UrbanGuard AI System - BBMP Grievances Data Loader
Loads real BBMP civic complaint data from CSV files and uses AWS Bedrock
to extract historical patterns that improve risk scoring and classification.

Download CSVs from: https://data.opencity.in/dataset/bbmp-grievances-data
Place them in backend/data/ folder.
"""
import os
import csv
import glob
import json
import logging
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models import Complaint

logger = logging.getLogger(__name__)


# ============================================================================
# BBMP Ward → Coordinates mapping (198 BBMP wards, key wards listed)
# Coordinates are approximate centroids for each ward.
# ============================================================================
BBMP_WARD_COORDS = {
    # Zone: South
    "Begur": (12.8600, 77.6200),
    "Arakere": (12.8900, 77.6100),
    "Gottigere": (12.8700, 77.5900),
    "Hulimavu": (12.8800, 77.6000),
    "Hongasandra": (12.8950, 77.6050),
    "Begur Road": (12.8750, 77.6150),
    "Bommanahalli": (12.9141, 77.6257),
    "Singasandra": (12.8950, 77.6300),
    "Harlur": (12.9050, 77.6600),
    "Haralur": (12.9050, 77.6600),
    "Sarjapur Road": (12.9121, 77.6871),
    "Bellandur": (12.9259, 77.6766),
    "Varthur": (12.9350, 77.7513),
    "Marathahalli": (12.9591, 77.7011),
    "Doddanekundi": (12.9750, 77.7050),
    "Mahadevapura": (12.9899, 77.6988),
    "Hoodi": (12.9899, 77.7119),
    "Whitefield": (12.9698, 77.7499),
    "Kadugodi": (12.9899, 77.7588),
    "Brookefield": (12.9716, 77.7137),
    "KR Puram": (13.0092, 77.6957),
    "Ramamurthy Nagar": (13.0103, 77.6774),
    "CV Raman Nagar": (12.9850, 77.6680),
    "Banaswadi": (13.0100, 77.6600),
    "Horamavu": (13.0200, 77.6600),
    "Kalyan Nagar": (13.0200, 77.6400),
    "Kammanahalli": (13.0100, 77.6400),
    "HBR Layout": (13.0200, 77.6300),
    "Hennur": (13.0300, 77.6200),
    "Lingarajapuram": (13.0000, 77.6300),
    "Kaval Byrasandra": (13.0100, 77.6200),
    "Frazer Town": (12.9890, 77.6090),
    "Ulsoor": (12.9810, 77.6190),
    "Shivajinagar": (12.9897, 77.6012),
    "Richmond Town": (12.9716, 77.6031),
    "Shantinagar": (12.9716, 77.6031),
    "Domlur": (12.9611, 77.6387),
    "Indiranagar": (12.9716, 77.6412),
    "Jeevanbhimanagar": (12.9800, 77.6500),
    "Koramangala": (12.9352, 77.6245),
    "HSR Layout": (12.9116, 77.6473),
    "BTM Layout": (12.9166, 77.6101),
    "Jayanagar": (12.9250, 77.5838),
    "JP Nagar": (12.9077, 77.5854),
    "Banashankari": (12.9250, 77.5480),
    "Basavanagudi": (12.9423, 77.5742),
    "Girinagar": (12.9350, 77.5580),
    "Uttarahalli": (12.8950, 77.5350),
    "Kengeri": (12.9077, 77.4854),
    "Rajarajeshwari Nagar": (12.9077, 77.5200),
    "Nagarbhavi": (12.9580, 77.5020),
    "Vijayanagar": (12.9716, 77.5322),
    "Rajajinagar": (12.9916, 77.5544),
    "Malleshwaram": (13.0039, 77.5727),
    "Sadashivanagar": (13.0050, 77.5750),
    "Yeshwanthpur": (13.0280, 77.5385),
    "Peenya": (13.0297, 77.5200),
    "Jalahalli": (13.0430, 77.5600),
    "Hebbal": (13.0358, 77.5970),
    "Yelahanka": (13.1007, 77.5963),
    "Dasarahalli": (13.0500, 77.5100),
    "Byatarayanapura": (13.0700, 77.5600),
    "Jakkur": (13.0700, 77.5900),
    "Thanisandra": (13.0600, 77.6200),
    "Kothanur": (13.0500, 77.6300),
    "Vidyaranyapura": (13.0600, 77.5500),
    "Chickpet": (12.9634, 77.5855),
    "Gandhinagar": (12.9800, 77.5700),
    "Seshadripuram": (12.9900, 77.5700),
    "Srirampuram": (13.0000, 77.5600),
    "Chamrajpet": (12.9600, 77.5700),
    "Majestic": (12.9766, 77.5713),
    "Electronic City": (12.8456, 77.6603),
    "Bannerghatta Road": (12.8892, 77.5957),
    "Bannerghatta": (12.8635, 77.5975),
    "Hulimangala": (12.8400, 77.6400),
    "Jigani": (12.8000, 77.6300),
    "Anekal": (12.7100, 77.6900),
    "Electronic City Phase 2": (12.8300, 77.6700),
}

# Fallback: city center if ward not found
_DEFAULT_COORDS = (12.9716, 77.5946)


# ============================================================================
# BBMP grievance category → app category mapping
# ============================================================================
BBMP_CATEGORY_MAP = {
    # Roads / Potholes
    "roads": "pothole",
    "road": "pothole",
    "pothole": "pothole",
    "road maintenance": "pothole",
    "road repair": "pothole",
    "road damage": "pothole",
    "footpath": "pothole",
    "footpaths": "pothole",
    "pavement": "pothole",
    "speed breaker": "pothole",
    "road works": "construction",

    # Drainage / Flooding
    "drainage": "flooding",
    "storm water drain": "flooding",
    "storm water drains": "flooding",
    "stormwater": "flooding",
    "waterlogging": "flooding",
    "water logging": "flooding",
    "flood": "flooding",
    "flooding": "flooding",
    "sewage": "flooding",
    "sewer": "flooding",
    "manhole": "flooding",
    "drain": "flooding",

    # Solid Waste / Garbage
    "solid waste": "garbage",
    "garbage": "garbage",
    "waste": "garbage",
    "waste management": "garbage",
    "sanitation": "garbage",
    "cleanliness": "garbage",
    "litter": "garbage",
    "dumping": "garbage",
    "sweeping": "garbage",
    "pourakarmikas": "garbage",

    # Street Lights
    "street light": "streetlight",
    "street lights": "streetlight",
    "streetlight": "streetlight",
    "streetlights": "streetlight",
    "lighting": "streetlight",
    "lamp post": "streetlight",
    "lamp posts": "streetlight",
    "electrical": "streetlight",

    # Water Supply
    "water supply": "water_supply",
    "water": "water_supply",
    "drinking water": "water_supply",
    "bwssb": "water_supply",
    "pipeline": "water_supply",
    "water pipeline": "water_supply",
    "water leakage": "water_supply",
    "water connection": "water_supply",
    "water pressure": "water_supply",
    "water quality": "water_supply",
    "water contamination": "water_supply",

    # Noise
    "noise": "noise",
    "noise pollution": "noise",
    "sound": "noise",
    "loudspeaker": "noise",
    "music": "noise",

    # Construction / Building
    "construction": "construction",
    "building": "construction",
    "unauthorized construction": "construction",
    "illegal construction": "construction",
    "building plan": "construction",
    "encroachment": "construction",
    "demolition": "construction",

    # Traffic
    "traffic": "traffic",
    "traffic signal": "traffic",
    "traffic signals": "traffic",
    "parking": "traffic",
    "illegal parking": "traffic",
    "traffic management": "traffic",
    "signal": "traffic",
}


def _map_category(raw: str) -> str:
    """Map a raw BBMP grievance type to an app category."""
    key = raw.strip().lower()
    if key in BBMP_CATEGORY_MAP:
        return BBMP_CATEGORY_MAP[key]
    # Partial match
    for bbmp_key, app_cat in BBMP_CATEGORY_MAP.items():
        if bbmp_key in key or key in bbmp_key:
            return app_cat
    return "garbage"  # safe default


def _ward_to_coords(ward: str) -> tuple:
    """Return (lat, lng) for a BBMP ward name, with fuzzy fallback."""
    ward = ward.strip()
    if ward in BBMP_WARD_COORDS:
        return BBMP_WARD_COORDS[ward]
    # Case-insensitive match
    ward_lower = ward.lower()
    for k, v in BBMP_WARD_COORDS.items():
        if k.lower() == ward_lower:
            return v
    # Partial match
    for k, v in BBMP_WARD_COORDS.items():
        if ward_lower in k.lower() or k.lower() in ward_lower:
            return v
    # Add small jitter around city center so complaints don't all stack
    jitter_lat = random.uniform(-0.05, 0.05)
    jitter_lng = random.uniform(-0.05, 0.05)
    return (_DEFAULT_COORDS[0] + jitter_lat, _DEFAULT_COORDS[1] + jitter_lng)


def _parse_date(raw: str) -> datetime:
    """Try several date formats used in BBMP CSVs."""
    raw = raw.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    # Fallback: random time in last 30 days
    return datetime.now() - timedelta(days=random.uniform(0, 30))


def _detect_columns(header: list) -> dict:
    """
    Auto-detect column indices from CSV header row.
    Returns dict with keys: ward, category, description, date
    """
    header_lower = [h.strip().lower() for h in header]

    def find(candidates):
        for c in candidates:
            if c in header_lower:
                return header_lower.index(c)
        return None

    return {
        "ward": find(["ward_name", "ward name", "ward", "area", "location"]),
        "category": find(["grievance_type", "grievance type", "category", "type",
                          "complaint_type", "complaint type", "subject"]),
        "description": find(["description", "complaint_details", "complaint details",
                              "details", "remarks", "grievance_description",
                              "grievance description", "complaint"]),
        "date": find(["created_date", "created date", "date", "complaint_date",
                      "complaint date", "registered_date", "registered date",
                      "submission_date", "submission date"]),
        "status": find(["status", "complaint_status", "grievance_status"]),
    }


def load_bbmp_csv(filepath: str, max_rows: int = 5000) -> List[Complaint]:
    """
    Load complaints from a single BBMP grievances CSV file.

    Args:
        filepath: Path to the CSV file
        max_rows: Maximum number of rows to load (default 5000)

    Returns:
        List of Complaint objects
    """
    complaints = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return complaints

        cols = _detect_columns(header)

        # Need at least ward + category to be useful
        if cols["ward"] is None and cols["category"] is None:
            print(f"[BBMP Loader] Could not detect required columns in {filepath}")
            print(f"[BBMP Loader] Header: {header}")
            return complaints

        row_count = 0
        for row in reader:
            if row_count >= max_rows:
                break
            if not row or all(cell.strip() == "" for cell in row):
                continue

            def get(col_key, default=""):
                idx = cols.get(col_key)
                if idx is None or idx >= len(row):
                    return default
                return row[idx].strip()

            ward = get("ward", "Bengaluru")
            raw_category = get("category", "garbage")
            description = get("description", f"Civic complaint in {ward}")
            raw_date = get("date", "")

            # Skip rows with no meaningful data
            if not ward and not raw_category:
                continue

            category = _map_category(raw_category)
            coords = _ward_to_coords(ward)
            timestamp = _parse_date(raw_date) if raw_date else (
                datetime.now() - timedelta(days=random.uniform(0, 30))
            )

            # Use ward name as location, map to nearest known location if possible
            location = _nearest_known_location(coords)

            complaint = Complaint(
                location=location,
                category=category,
                description=description or f"{raw_category} complaint in {ward}",
                timestamp=timestamp,
                coordinates=coords,
                classification_confidence=0.85,
            )
            complaints.append(complaint)
            row_count += 1

    print(f"[BBMP Loader] Loaded {len(complaints)} complaints from {os.path.basename(filepath)}")
    return complaints


def _nearest_known_location(coords: tuple) -> str:
    """Map arbitrary coordinates to the nearest known BENGALURU_LOCATIONS key."""
    from constants import BENGALURU_LOCATIONS
    lat, lng = coords
    best = min(
        BENGALURU_LOCATIONS.items(),
        key=lambda item: (item[1][0] - lat) ** 2 + (item[1][1] - lng) ** 2
    )
    return best[0]


def load_all_bbmp_data(data_dir: str = None, max_total: int = 8000) -> Optional[List[Complaint]]:
    """
    Scan data_dir for BBMP CSV files and load them all.

    Args:
        data_dir: Directory containing CSV files (defaults to backend/data/)
        max_total: Maximum total complaints to load across all files

    Returns:
        List of Complaint objects, or None if no CSV files found
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    patterns = [
        os.path.join(data_dir, "*.csv"),
        os.path.join(data_dir, "*.CSV"),
    ]

    csv_files = []
    for pattern in patterns:
        csv_files.extend(glob.glob(pattern))

    # If no local CSVs, try downloading from S3
    if not csv_files:
        try:
            from s3_storage import download_bbmp_csvs
            downloaded = download_bbmp_csvs(data_dir)
            if downloaded > 0:
                for pattern in patterns:
                    csv_files.extend(glob.glob(pattern))
                logger.info(f"[BBMP Loader] Downloaded {downloaded} CSV(s) from S3")
        except Exception as e:
            logger.debug(f"[BBMP Loader] S3 download skipped: {e}")

    if not csv_files:
        return None

    all_complaints = []
    per_file_limit = max(1000, max_total // len(csv_files))

    for filepath in sorted(csv_files):
        if len(all_complaints) >= max_total:
            break
        remaining = max_total - len(all_complaints)
        batch = load_bbmp_csv(filepath, max_rows=min(per_file_limit, remaining))
        all_complaints.extend(batch)

    print(f"[BBMP Loader] Total: {len(all_complaints)} complaints from {len(csv_files)} file(s)")
    return all_complaints if all_complaints else None


# ============================================================================
# BBMP Pattern Analysis via AWS Bedrock
# ============================================================================

# Module-level cache so analysis runs once per server startup
_bbmp_insights: Optional[Dict[str, Any]] = None


def _build_dataset_summary(complaints: List[Complaint]) -> dict:
    """
    Summarise a list of BBMP complaints into statistics Bedrock can reason about.
    Keeps the prompt small — no raw complaint text is sent.
    """
    category_counts = Counter(c.category for c in complaints)
    location_counts = Counter(c.location for c in complaints)

    # Top 10 hotspot locations per category
    location_category: Dict[str, Counter] = defaultdict(Counter)
    for c in complaints:
        location_category[c.location][c.category] += 1

    hotspots = {}
    for loc, cat_counter in location_category.items():
        total = sum(cat_counter.values())
        if total >= 5:  # only meaningful clusters
            hotspots[loc] = {"total": total, "top_category": cat_counter.most_common(1)[0][0]}

    # Sort hotspots by total descending, keep top 20
    top_hotspots = dict(
        sorted(hotspots.items(), key=lambda x: x[1]["total"], reverse=True)[:20]
    )

    # Monthly distribution (last 12 months)
    monthly: Counter = Counter()
    for c in complaints:
        key = c.timestamp.strftime("%Y-%m")
        monthly[key] += 1

    return {
        "total_complaints": len(complaints),
        "category_distribution": dict(category_counts.most_common()),
        "top_locations_by_volume": dict(location_counts.most_common(15)),
        "hotspot_zones": top_hotspots,
        "monthly_trend": dict(sorted(monthly.items())[-12:]),
    }


def analyze_bbmp_patterns_with_bedrock(complaints: List[Complaint]) -> Dict[str, Any]:
    """
    Send a statistical summary of the BBMP dataset to AWS Bedrock (Nova Micro)
    and get back structured insights. Results are cached in S3 so Lambda cold
    starts don't re-run the analysis every time.
    """
    global _bbmp_insights
    if _bbmp_insights is not None:
        return _bbmp_insights

    # Try loading from S3 cache first (avoids Bedrock call on Lambda restarts)
    try:
        from s3_storage import load_bbmp_insights
        cached = load_bbmp_insights()
        if cached:
            logger.info("[BBMP Bedrock] Loaded insights from S3 cache")
            _bbmp_insights = cached
            return _bbmp_insights
    except Exception:
        pass

    fallback = {
        "hotspot_risk_boosts": {},
        "category_weights": {},
        "seasonal_warnings": [],
        "summary": "BBMP historical analysis not available.",
    }

    if not complaints:
        _bbmp_insights = fallback
        return _bbmp_insights

    summary = _build_dataset_summary(complaints)

    prompt = f"""You are an urban data analyst for Bengaluru, India.
Below is a statistical summary of {summary['total_complaints']} real BBMP civic grievances.

Category distribution: {json.dumps(summary['category_distribution'])}
Top complaint locations: {json.dumps(summary['top_locations_by_volume'])}
Hotspot zones (5+ complaints): {json.dumps(summary['hotspot_zones'])}
Monthly trend (recent 12 months): {json.dumps(summary['monthly_trend'])}

Based on this historical data, respond with a JSON object (no markdown, no explanation, just JSON) with exactly these keys:

1. "hotspot_risk_boosts": object mapping location names to integer bonus points (5-25) to add to their risk score because they are chronic problem areas. Include only the top 8 most problematic locations.

2. "category_weights": object mapping each of these category names to a float multiplier (0.8-1.5) reflecting how serious that category is historically: pothole, flooding, traffic, garbage, streetlight, water_supply, noise, construction.

3. "seasonal_warnings": array of up to 3 short strings describing seasonal risk patterns visible in the monthly trend (e.g. "Flooding complaints spike June-August during monsoon").

4. "summary": a single paragraph (3-4 sentences) summarising the key risk patterns in this dataset for a city official.

JSON response:"""

    try:
        import boto3, os as _os
        from botocore.config import Config

        aws_region = _os.getenv("AWS_BEDROCK_REGION", "us-east-1")
        model_id = _os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
        api_key = _os.getenv("BEDROCK_API_KEY")

        body = json.dumps({
            "messages": [{"role": "user", "content": [{"text": prompt}]}]
        })

        if api_key:
            import requests as _req
            url = f"https://bedrock-runtime.{aws_region}.amazonaws.com/model/{model_id}/invoke"
            resp = _req.post(
                url,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {api_key}"},
                data=body,
                timeout=20,
            )
            resp.raise_for_status()
            rb = resp.json()
        else:
            client = boto3.client(
                "bedrock-runtime",
                region_name=aws_region,
                config=Config(connect_timeout=5, read_timeout=20, retries={"max_attempts": 1}),
            )
            response = client.invoke_model(modelId=model_id, body=body)
            rb = json.loads(response["body"].read())

        # Extract text from Nova response
        text = (rb.get("output", {})
                  .get("message", {})
                  .get("content", [{}])[0]
                  .get("text", ""))

        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        insights = json.loads(text)

        # Validate and sanitise
        result = {
            "hotspot_risk_boosts": {
                k: max(0, min(30, int(v)))
                for k, v in insights.get("hotspot_risk_boosts", {}).items()
            },
            "category_weights": {
                k: max(0.5, min(2.0, float(v)))
                for k, v in insights.get("category_weights", {}).items()
            },
            "seasonal_warnings": [
                str(w) for w in insights.get("seasonal_warnings", [])[:3]
            ],
            "summary": str(insights.get("summary", "")),
        }

        logger.info(
            f"[BBMP Bedrock] Analysis complete. "
            f"Hotspot boosts for {len(result['hotspot_risk_boosts'])} areas. "
            f"Summary: {result['summary'][:80]}..."
        )
        _bbmp_insights = result

        # Persist to S3 so Lambda cold starts skip re-analysis
        try:
            from s3_storage import save_bbmp_insights
            save_bbmp_insights(result)
        except Exception:
            pass

        return result

    except Exception as e:
        logger.warning(f"[BBMP Bedrock] Analysis failed ({e}), using defaults.")
        _bbmp_insights = fallback
        return _bbmp_insights


def get_bbmp_insights() -> Optional[Dict[str, Any]]:
    """Return cached BBMP insights (None if analysis hasn't run yet)."""
    return _bbmp_insights


def reset_bbmp_insights():
    """Clear cached insights (useful for testing)."""
    global _bbmp_insights
    _bbmp_insights = None
