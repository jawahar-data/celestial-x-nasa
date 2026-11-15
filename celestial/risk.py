"""
CELESTIAL X — Advanced Multi-Factor Fire Risk Engine (CELESTIAL-X-RISK-v2)
==========================================================================
Produces transparent, explainable wildfire risk scores combining:
  1. Satellite Combustion Radiative Intensity (FRP)
  2. Spatiotemporal Persistence & Expansion (FIRE-FUSE Duration & H3 Cells)
  3. Real-Time / Climatological Fire Weather Deficit (Temperature, Humidity, Wind)
  4. Topographic Terrain & Land Cover Fuel Models (Copernicus DEM & ESA WorldCover)
  5. Biodiversity Vulnerability & Protected Area Proximity (Tiger Reserves / Sanctuaries)

IMPORTANT SCIENTIFIC DISCLAIMER:
---------------------------------
CELESTIAL-X-RISK-v2 is an analytical multi-criteria decision indicator developed for
wildfire situational awareness. It is transparent, fully auditable, and grounded in
satellite observations and meteorological drivers. It is NOT an empirical flame-length
simulation or an official national fire danger rating forecast.
"""

from typing import Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
import streamlit as st

from .database import get_connection
from .weather_intelligence import get_weather_for_location
from .environmental_intelligence import get_environmental_context_for_location


# ── Risk level thresholds ─────────────────────────────────────────────────────
RISK_THRESHOLDS = {
    "VERY HIGH": 0.75,
    "HIGH":      0.50,
    "MODERATE":  0.25,
    "LOW":       0.00,
}

# CELESTIAL-X-RISK-v2 Weights Specification
RISK_V2_WEIGHTS = {
    "thermal_intensity":       0.30, # FRP Peak & Average normalized
    "persistence_expansion":   0.20, # Duration (hrs) and H3 spatial dispersion
    "weather_deficit":         0.20, # High Temp, Low Humidity, High Wind Speed
    "fuel_topography":         0.15, # Land cover flammability + Slope amplification
    "conservation_proximity":  0.15, # Proximity to UNESCO / Tiger Reserves
}


def _score_frp(peak_frp: Optional[float], mean_frp: Optional[float]) -> float:
    """
    FRP-based component (0–1).
    Reference scale: FRP > 500 MW = major fire (Giglio et al.).
    Soft-clipped at 1000 MW.
    """
    if not peak_frp:
        return 0.0
    return min(1.0, (peak_frp / 1000.0) ** 0.6)


def _score_duration(duration_hours: Optional[float]) -> float:
    """
    Duration-based component (0–1).
    Longer active fires indicate higher persistence risk.
    Soft-cap at 7 days (168 hours).
    """
    if not duration_hours:
        return 0.0
    return min(1.0, duration_hours / 168.0)


def _score_expansion(h3_count: Optional[int], obs_count: Optional[int]) -> float:
    """
    Spatial expansion component (0–1).
    Based on number of distinct H3 cells relative to observation count.
    High ratio = fire spreading widely.
    """
    if not h3_count or not obs_count or obs_count == 0:
        return 0.0
    ratio = h3_count / max(obs_count, 1)
    return min(1.0, ratio * 2)


def _score_agreement(satellite_agreement: Optional[float]) -> float:
    """
    Cross-satellite agreement component (0–1).
    If both MODIS and VIIRS detect the same area → higher confidence in fire.
    """
    return float(satellite_agreement or 0.0)


def _score_confidence(max_confidence: Optional[float]) -> float:
    """Confidence component — direct pass-through of normalized confidence."""
    return float(max_confidence or 0.5)


def _score_weather(weather_dict: Optional[Dict[str, Any]]) -> float:
    """
    Atmospheric fire weather deficit score (0–1).
    Higher score when temperature is high, humidity is low, and wind is high.
    """
    if not weather_dict:
        return 0.40 # Neutral default

    t = float(weather_dict.get("temperature_c", 28.0) or 28.0)
    rh = float(weather_dict.get("relative_humidity_pct", 50.0) or 50.0)
    ws = float(weather_dict.get("wind_speed_kmh", 12.0) or 12.0)

    t_factor = min(1.0, max(0.0, (t - 15.0) / 25.0)) # 15°C to 40°C
    rh_factor = min(1.0, max(0.0, (100.0 - rh) / 80.0)) # 100% down to 20%
    ws_factor = min(1.0, max(0.0, ws / 40.0)) # 0 to 40 km/h

    score = (t_factor * 0.35) + (rh_factor * 0.40) + (ws_factor * 0.25)
    return round(min(1.0, max(0.0, score)), 4)


def _score_environment(env_dict: Optional[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Return (fuel_and_terrain_score: 0-1, conservation_vulnerability_score: 0-1).
    """
    if not env_dict:
        return 0.45, 0.30

    slope = float(env_dict.get("slope_deg", 5.0) or 5.0)
    esi = float(env_dict.get("environmental_sensitivity_score", 50.0) or 50.0)
    dist_pa = float(env_dict.get("dist_to_protected_area_km", 20.0) or 20.0)

    # Slope + fuel flammability
    fuel_terrain_score = (esi / 100.0 * 0.65) + (min(1.0, slope / 25.0) * 0.35)

    # Protected area proximity: < 2km = 1.0, > 20km = 0.0
    if dist_pa <= 0.0:
        pa_score = 1.0 # Directly inside protected reserve
    else:
        pa_score = max(0.0, 1.0 - (dist_pa / 20.0))

    return round(min(1.0, max(0.0, fuel_terrain_score)), 4), round(min(1.0, max(0.0, pa_score)), 4)


class RiskScoreResult(tuple):
    """
    Dual-compatibility return object:
    1. Unpackable as a 3-tuple: (score, level, breakdown)
    2. Indexable like a dict: rv2["composite_risk_score"], rv2["risk_level"], rv2["factor_scores"]
    """
    def __new__(cls, score: float, level: str, breakdown: dict):
        return super().__new__(cls, (score, level, breakdown))

    def __init__(self, score: float, level: str, breakdown: dict):
        self.score = score
        self.level = level
        self.breakdown = breakdown
        self._dict = {
            "composite_risk_score": score,
            "risk_score": score,
            "risk_level": level,
            "level": level,
            "factor_scores": {
                "thermal_intensity": breakdown.get("thermal_intensity_score", 0.0),
                "duration_persistence": breakdown.get("persistence_expansion_score", 0.0),
                "weather_deficit": breakdown.get("weather_deficit_score", 0.0),
                "fuel_topography": breakdown.get("fuel_topography_score", 0.0),
                "conservation_proximity": breakdown.get("conservation_proximity_score", 0.0),
            },
            "breakdown": breakdown,
            **breakdown
        }

    def __getitem__(self, item):
        if isinstance(item, str):
            if item in self._dict:
                return self._dict[item]
            return self.breakdown.get(item)
        return super().__getitem__(item)

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def __contains__(self, item):
        return item in self._dict


def compute_risk_score_v2(
    event: dict,
    weather_dict: Optional[Dict[str, Any]] = None,
    env_dict: Optional[Dict[str, Any]] = None,
) -> Tuple[float, str, Dict[str, Any]]:
    """
    Compute CELESTIAL-X-RISK-v2 multi-factor risk assessment.
    Returns (score: 0.0-1.0, level: str, breakdown: dict)
    """
    lat = event.get("centroid_lat")
    lon = event.get("centroid_lon")

    # Fetch weather if not provided
    if not weather_dict and lat is not None and lon is not None:
        weather_dict = get_weather_for_location(lat, lon)

    # Fetch environmental context if not provided
    if not env_dict and lat is not None and lon is not None:
        env_dict = get_environmental_context_for_location(lat, lon)

    # Factor 1: Thermal Intensity (30%)
    frp_s = _score_frp(event.get("peak_frp"), event.get("mean_frp"))

    # Factor 2: Persistence & Expansion (20%)
    dur_s = _score_duration(event.get("duration_hours"))
    exp_s = _score_expansion(event.get("h3_cell_count"), event.get("observation_count"))
    persist_s = (dur_s * 0.60) + (exp_s * 0.40)

    # Factor 3: Weather Deficit (20%)
    wx_s = _score_weather(weather_dict)

    # Factor 4 & 5: Fuel/Terrain (15%) and Conservation Proximity (15%)
    fuel_s, pa_s = _score_environment(env_dict)

    # Weighted composite score
    w = RISK_V2_WEIGHTS
    score = (
        (frp_s * w["thermal_intensity"]) +
        (persist_s * w["persistence_expansion"]) +
        (wx_s * w["weather_deficit"]) +
        (fuel_s * w["fuel_topography"]) +
        (pa_s * w["conservation_proximity"])
    )
    score = round(min(1.0, max(0.0, score)), 4)

    level = "LOW"
    for lv, threshold in RISK_THRESHOLDS.items():
        if score >= threshold:
            level = lv
            break

    breakdown = {
        "model_version": "CELESTIAL-X-RISK-v2",
        "thermal_intensity_score": round(frp_s, 3),
        "persistence_expansion_score": round(persist_s, 3),
        "weather_deficit_score": round(wx_s, 3),
        "fuel_topography_score": round(fuel_s, 3),
        "conservation_proximity_score": round(pa_s, 3),
        "weather_provenance": weather_dict.get("source", "N/A") if weather_dict else "N/A",
        "environmental_provenance": env_dict.get("source", "N/A") if env_dict else "N/A",
        "nearest_protected_area": env_dict.get("protected_area_name", "N/A") if env_dict else "N/A",
        "dist_to_protected_km": env_dict.get("dist_to_protected_area_km", None) if env_dict else None,
    }

    return RiskScoreResult(score, level, breakdown)


def compute_risk_score(event: dict) -> Tuple[float, str]:
    """
    Backward-compatible wrapper for CELESTIAL-X-RISK.
    Returns (score: float 0–1, level: str)
    """
    score, level, _ = compute_risk_score_v2(event)
    return score, level


def assess_all_events(log_fn=None) -> int:
    """
    Run CELESTIAL-X-RISK-v2 assessment on all non-closed fire events.
    Updates fire_events.risk_level, inserts risk_predictions rows,
    associates weather & environmental drivers, and computes spread screening.
    Returns count of events assessed.
    """
    def log(msg):
        if log_fn:
            log_fn(msg)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fire_events WHERE status != 'CLOSED'")
    events = [dict(r) for r in cur.fetchall()]
    from datetime import datetime, timezone
    import json
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Record model metadata
    try:
        cur.execute("""
            INSERT INTO risk_model_metadata (model_version, weights_json, description)
            VALUES (?, ?, ?)
        """, (
            "CELESTIAL-X-RISK-v2",
            json.dumps(RISK_V2_WEIGHTS),
            "Multi-factor model combining thermal FRP (30%), persistence (20%), fire weather deficit (20%), topography & fuel (15%), and conservation proximity (15%)."
        ))
    except Exception:
        pass

    from .weather_intelligence import store_event_weather, get_event_weather
    from .environmental_intelligence import store_event_environmental_context, get_event_environmental_context
    from .fire_spread import assess_fire_spread_and_exposure
    from concurrent.futures import ThreadPoolExecutor

    # 1. Check existing weather and environmental context already in DB
    cur.execute("""
        SELECT event_id, latitude, longitude, observation_time,
               temperature_c, relative_humidity_pct, wind_speed_kmh,
               wind_direction_deg, precipitation_mm, surface_pressure_hpa,
               fire_weather_index, is_forecast, source
        FROM weather_observations
    """)
    existing_weather_by_eid = {dict(r)["event_id"]: dict(r) for r in cur.fetchall()}

    cur.execute("""
        SELECT * FROM environmental_context
    """)
    existing_env_by_eid = {dict(r)["event_id"]: dict(r) for r in cur.fetchall()}

    # 2. Identify unique quantized coordinates that need network retrieval
    needed_coords = set()
    for ev in events:
        eid = ev["event_id"]
        lat = ev.get("centroid_lat")
        lon = ev.get("centroid_lon")
        if lat and lon and (eid not in existing_weather_by_eid or eid not in existing_env_by_eid):
            macro_coord = (round(lat * 2.0) / 2.0, round(lon * 2.0) / 2.0)
            needed_coords.add(macro_coord)

    weather_lookup = {}
    env_lookup = {}

    if needed_coords:
        def fetch_weather_and_env(coord):
            c_lat, c_lon = coord
            try:
                wx = get_weather_for_location(c_lat, c_lon)
            except Exception:
                wx = None
            try:
                env = get_environmental_context_for_location(c_lat, c_lon)
            except Exception:
                env = None
            return coord, wx, env

        with ThreadPoolExecutor(max_workers=min(12, len(needed_coords))) as executor:
            for coord, wx, env in executor.map(fetch_weather_and_env, needed_coords):
                weather_lookup[coord] = wx
                env_lookup[coord] = env

    # 3. Assess each event using cached or pre-fetched context
    for event in events:
        lat = event.get("centroid_lat")
        lon = event.get("centroid_lon")
        ev_id = event["event_id"]
        qcoord = (round(lat * 2.0) / 2.0, round(lon * 2.0) / 2.0) if (lat and lon) else None

        # Resolve weather (prefer DB cache, then concurrent lookup)
        weather_dict = existing_weather_by_eid.get(ev_id)
        if not weather_dict and qcoord:
            weather_dict = weather_lookup.get(qcoord)
            if weather_dict:
                store_event_weather(ev_id, weather_dict, conn)
                existing_weather_by_eid[ev_id] = weather_dict

        # Resolve environmental context (prefer DB cache, then concurrent lookup)
        env_dict = existing_env_by_eid.get(ev_id)
        if not env_dict and qcoord:
            env_dict = env_lookup.get(qcoord)
            if env_dict:
                store_event_environmental_context(ev_id, env_dict, conn)
                existing_env_by_eid[ev_id] = env_dict

        # Potential fire spread assessment (passes pre-computed weather & env!)
        if lat and lon:
            try:
                assess_fire_spread_and_exposure(
                    ev_id, lat, lon,
                    peak_frp=event.get("peak_frp"),
                    mean_frp=event.get("mean_frp"),
                    weather_dict=weather_dict,
                    env_dict=env_dict,
                    conn=conn
                )
            except Exception:
                pass

        score, level, breakdown = compute_risk_score_v2(event, weather_dict, env_dict)
        cur.execute(
            "UPDATE fire_events SET risk_level=?, updated_at=? WHERE event_id=?",
            (level, now, ev_id)
        )
        cur.execute("""
            INSERT OR REPLACE INTO risk_predictions
                (event_id, latitude, longitude, risk_level, risk_score,
                 frp_indicator, duration_factor, expansion_factor, confidence_factor,
                 assessment_date, methodology)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ev_id,
            lat, lon,
            level, score,
            breakdown.get("thermal_intensity_score", 0.0),
            breakdown.get("persistence_expansion_score", 0.0),
            breakdown.get("fuel_topography_score", 0.0),
            breakdown.get("weather_deficit_score", 0.0),
            now,
            "CELESTIAL-X-RISK-v2 (Multi-Factor Weather, Topographic & Conservation Indicator)",
        ))

    conn.commit()
    conn.close()
    log(f"✓ CELESTIAL-X-RISK-v2 assessed for {len(events)} events (weather, topography, and spread integrated)")
    return len(events)


@st.cache_data(ttl=30)
def get_risk_map_data() -> pd.DataFrame:
    """Return event centroids with risk level for map visualization."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            fe.event_id, fe.centroid_lat as latitude, fe.centroid_lon as longitude,
            fe.risk_level, rp.risk_score,
            fe.status, fe.peak_frp, fe.observation_count,
            fe.start_time, fe.last_observed_time
        FROM fire_events fe
        LEFT JOIN risk_predictions rp ON fe.event_id = rp.event_id
        WHERE fe.centroid_lat IS NOT NULL
        ORDER BY rp.risk_score DESC NULLS LAST
    """, conn)
    conn.close()
    return df


RISK_COLOR_MAP = {
    "VERY HIGH": [220, 38, 38,  210],    # deep red
    "HIGH":      [234, 88, 12,  200],    # orange
    "MODERATE":  [202, 138, 4,  180],    # amber
    "LOW":       [21, 128, 61,  160],    # green
    None:        [100, 100, 100, 120],
}
