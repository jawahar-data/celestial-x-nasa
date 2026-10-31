"""
CELESTIAL X - Protected Ecosystem & Biodiversity Monitoring Engine
===================================================================
Quantifies fire pressure on critical ecological preserves and biodiversity hotspots:
  - Classifies hotspots as: INSIDE PROTECTED AREA, BUFFER ZONE (<= 10 km), or REGIONAL
  - Identifies persistent fire events encroaching upon high-conservation ecosystems
  - Evaluates historical burning trends inside protected reserve perimeters
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .database import get_connection

# Key global and demonstration protected ecosystems (Bounding approximations)
PROTECTED_RESERVES = [
    # Tamil Nadu / Western Ghats Biodiversity Hotspot
    {
        "id": "PA-TN-01",
        "name": "Mudumalai Tiger Reserve & Biosphere",
        "region": "Tamil Nadu, India",
        "category": "Tiger Reserve / UNESCO Biosphere",
        "bounds": (76.45, 11.50, 76.75, 11.75),  # west, south, east, north
        "buffer_km": 10.0,
        "biodiversity_importance": "CRITICAL (Asian Elephant, Bengal Tiger, Nilgiri Tahr)",
    },
    {
        "id": "PA-TN-02",
        "name": "Anamalai Tiger Reserve",
        "region": "Tamil Nadu, India",
        "category": "Tiger Reserve & Rain Forest",
        "bounds": (76.80, 10.20, 77.30, 10.60),
        "buffer_km": 10.0,
        "biodiversity_importance": "CRITICAL (Lion-tailed Macaque, Nilgiri Langur)",
    },
    {
        "id": "PA-TN-03",
        "name": "Sathyamangalam Tiger Reserve",
        "region": "Tamil Nadu, India",
        "category": "Wildlife Sanctuary / Tiger Corridor",
        "bounds": (76.90, 11.45, 77.45, 11.85),
        "buffer_km": 10.0,
        "biodiversity_importance": "HIGH (Elephant migratory corridor connecting Western & Eastern Ghats)",
    },
    # Amazon Rainforest
    {
        "id": "PA-AMZ-01",
        "name": "Tumucumaque Mountains National Park",
        "region": "Amazon, Brazil",
        "category": "Tropical Rainforest National Park",
        "bounds": (-55.0, 0.5, -51.5, 3.5),
        "buffer_km": 15.0,
        "biodiversity_importance": "CRITICAL (Largest tropical forest national park on Earth)",
    },
    # California
    {
        "id": "PA-CAL-01",
        "name": "Yosemite National Park & Mariposa",
        "region": "California, USA",
        "category": "National Park & UNESCO World Heritage",
        "bounds": (-119.9, 37.5, -119.2, 38.2),
        "buffer_km": 10.0,
        "biodiversity_importance": "HIGH (Giant Sequoia groves, Sierra Nevada ecosystem)",
    },
    # Australia
    {
        "id": "PA-AUS-01",
        "name": "Greater Blue Mountains Heritage Area",
        "region": "Australia",
        "category": "World Heritage Protected Area",
        "bounds": (150.0, -34.2, 150.7, -33.1),
        "buffer_km": 12.0,
        "biodiversity_importance": "CRITICAL (Temperate eucalypt forest, endemic flora)",
    },
]

def analyze_protected_areas(selected_reserve_id=None) -> Dict[str, Any]:
    """
    Evaluate fire hotspots intersecting or in the buffer zone of protected ecosystems.
    """
    conn = get_connection()
    
    results = []
    total_inside = 0
    total_buffer = 0

    for pa in PROTECTED_RESERVES:
        if selected_reserve_id and selected_reserve_id != "All" and pa["id"] != selected_reserve_id:
            continue

        w, s, e, n = pa["bounds"]
        buf_deg = pa["buffer_km"] / 111.0  # Approx degree conversion

        # Query inside
        q_inside = """
        SELECT COUNT(*) as cnt, AVG(COALESCE(frp, frp_proxy, 0)) as avg_frp
        FROM harmonized_observations
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
        """
        row_in = conn.execute(q_inside, (s, n, w, e)).fetchone()
        in_cnt = row_in["cnt"] if row_in else 0
        in_frp = round(row_in["avg_frp"], 1) if (row_in and row_in["avg_frp"]) else 0.0

        # Query buffer
        q_buf = """
        SELECT COUNT(*) as cnt
        FROM harmonized_observations
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
          AND NOT (latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?)
        """
        row_buf = conn.execute(q_buf, (s - buf_deg, n + buf_deg, w - buf_deg, e + buf_deg, s, n, w, e)).fetchone()
        buf_cnt = row_buf["cnt"] if row_buf else 0

        # Persistent events affecting this area
        q_events = """
        SELECT COUNT(*) as cnt
        FROM fire_events
        WHERE centroid_lat BETWEEN ? AND ?
          AND centroid_lon BETWEEN ? AND ?
        """
        row_ev = conn.execute(q_events, (s - buf_deg, n + buf_deg, w - buf_deg, e + buf_deg)).fetchone()
        ev_cnt = row_ev["cnt"] if row_ev else 0

        threat_level = "CRITICAL" if in_cnt > 20 else ("HIGH" if in_cnt > 5 or buf_cnt > 30 else "MODERATE")

        results.append({
            "id": pa["id"],
            "name": pa["name"],
            "region": pa["region"],
            "category": pa["category"],
            "inside_hotspots": in_cnt,
            "buffer_hotspots": buf_cnt,
            "avg_frp": in_frp,
            "persistent_events_count": ev_cnt,
            "threat_level": threat_level,
            "biodiversity_importance": pa["biodiversity_importance"],
            "bounds": pa["bounds"],
        })
        total_inside += in_cnt
        total_buffer += buf_cnt

    conn.close()

    return {
        "reserves": results,
        "total_inside_all": total_inside,
        "total_buffer_all": total_buffer,
    }
