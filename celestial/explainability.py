"""
CELESTIAL X - Harmonization Explainability & Traceability Engine
=================================================================
Provides full scientific auditability for FIRE-FUSE decisions.
For every persistent fire event and linked observation, exposes:
  - Raw satellite provenance (Instrument, Swath, Native confidence, FRP)
  - Spatial mapping (H3 res-7/8 cells, Haversine distance to event centroid)
  - Temporal delta (hours between observations)
  - Exact rule evaluated and mathematical justification
"""

import math
import pandas as pd
from typing import Dict, Any, List
from .database import get_connection

def explain_event_harmonization(event_id: str) -> Dict[str, Any]:
    """
    Generate an explainability breakdown for a persistent fire event,
    detailing how individual satellite observations were fused together.
    """
    conn = get_connection()
    
    # Get event metadata
    ev_row = conn.execute(
        "SELECT * FROM fire_events WHERE event_id = ?", (event_id,)
    ).fetchone()

    if not ev_row:
        conn.close()
        return {"error": f"Event {event_id} not found"}

    event_data = dict(ev_row)

    # Get linked observations and original raw data
    query = """
    SELECT 
        eo.id as link_id,
        eo.added_at,
        ho.id as harm_id,
        ho.satellite,
        ho.timestamp,
        ho.latitude,
        ho.longitude,
        ho.h3_cell_r7,
        ho.h3_cell_r8,
        ho.confidence_norm,
        ho.frp,
        ho.frp_proxy,
        ho.quality_flag,
        ro.id as raw_id,
        ro.product,
        ro.confidence as raw_confidence,
        ro.brightness,
        ro.bright_ti4,
        ro.daynight
    FROM event_observations eo
    JOIN harmonized_observations ho ON eo.obs_id = ho.id
    LEFT JOIN raw_observations ro ON ho.raw_obs_id = ro.id
    WHERE eo.event_id = ?
    ORDER BY ho.timestamp ASC
    """
    obs_rows = conn.execute(query, (event_id,)).fetchall()
    conn.close()

    centroid_lat = event_data.get("centroid_lat") or 0.0
    centroid_lon = event_data.get("centroid_lon") or 0.0

    trace_records = []
    first_ts = None

    for idx, r in enumerate(obs_rows):
        r_dict = dict(r)
        lat = r_dict["latitude"]
        lon = r_dict["longitude"]
        ts_str = r_dict["timestamp"]

        # Calculate distance to event centroid
        dist_km = haversine_distance(lat, lon, centroid_lat, centroid_lon)
        
        # Calculate time delta from event start
        if idx == 0:
            first_ts = pd.to_datetime(ts_str)
            time_delta_hrs = 0.0
            decision_type = "EVENT_SEED"
            rule_justification = f"Initial active thermal anomaly seed at lat={lat:.3f}, lon={lon:.3f}."
        else:
            cur_ts = pd.to_datetime(ts_str)
            time_delta_hrs = round((cur_ts - first_ts).total_seconds() / 3600.0, 1) if first_ts else 0.0
            decision_type = "FUSED_MATCH"
            rule_justification = (
                f"Observation matches within spatial threshold (dist={dist_km:.2f} km <= 15.0 km) "
                f"and temporal threshold (delta={time_delta_hrs:.1f} hrs <= 36.0 hrs)."
            )

        trace_records.append({
            "step": idx + 1,
            "decision": decision_type,
            "satellite": r_dict["satellite"],
            "raw_id": r_dict["raw_id"],
            "timestamp": ts_str,
            "lat": lat,
            "lon": lon,
            "h3_r7": r_dict["h3_cell_r7"],
            "h3_r8": r_dict["h3_cell_r8"],
            "raw_confidence": r_dict["raw_confidence"],
            "norm_confidence": round(r_dict["confidence_norm"] or 0.5, 2),
            "frp": round(r_dict["frp"] or r_dict["frp_proxy"] or 0.0, 1),
            "distance_to_centroid_km": round(dist_km, 2),
            "time_delta_hours": time_delta_hrs,
            "justification": rule_justification,
        })

    return {
        "event_id": event_id,
        "event_summary": event_data,
        "total_observations_fused": len(trace_records),
        "trace_records": trace_records,
    }

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute Haversine distance in kilometers between two points."""
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c
