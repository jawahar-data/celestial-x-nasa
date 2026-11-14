"""
CELESTIAL X — Potential Fire Spread & Exposure Intelligence Engine
===================================================================
A transparent, physics-grounded screening model evaluating downwind exposure,
rate-of-spread proxies, and environmental asset vulnerability.

Scientific Methodology & Principles:
------------------------------------
1. Wind Vector Propagation:
   Wind direction ($W_{dir}$) defines where the wind originates.
   Primary downwind exposure bearing ($B_{down}$) is:
     B_down = (W_dir + 180 deg) % 360 deg

2. Topographic Slope Acceleration (Rothermel, 1972 principle):
   Fires burn significantly faster uphill due to pre-heating of upslope vegetation:
     phi_s = 5.275 * (tan(theta))^2

3. Rate of Spread (ROS) Proxy:
   Combines wind velocity, fuel dryness, slope, and Fire Radiative Power (FRP):
     ROS_proxy = base_fuel_speed * (1 + 0.04 * wind_kmh) * (1 + phi_s) * (FRP_factor)

4. Downwind Exposure Cone:
   Calculates an exposure sector spanning [B_down - 30 deg, B_down + 30 deg]
   with multi-tier buffer zones (Immediate 12h, Extended 24h, Advisory 48h).

IMPORTANT SCIENTIFIC DISCLAIMER:
--------------------------------
This is an analytical screening model designed for decision support, ecological monitoring,
and emergency preparedness review. It is NOT an operational computational fluid dynamics (CFD)
fire perimeter prediction and should not be used as the sole basis for tactical evacuation.
"""

import math
import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from .database import get_connection
from .weather_intelligence import get_weather_for_location, get_wind_cardinal_direction
from .environmental_intelligence import get_environmental_context_for_location, find_nearest_protected_area, KNOWN_PROTECTED_RESERVES


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def _destination_point(lat: float, lon: float, bearing_deg: float, distance_km: float) -> Tuple[float, float]:
    """Calculate destination lat/lon given a start point, bearing, and distance."""
    r = 6371.0
    phi1 = math.radians(lat)
    lam1 = math.radians(lon)
    theta = math.radians(bearing_deg)
    d_r = distance_km / r

    phi2 = math.asin(math.sin(phi1) * math.cos(d_r) + math.cos(phi1) * math.sin(d_r) * math.cos(theta))
    lam2 = lam1 + math.atan2(math.sin(theta) * math.sin(d_r) * math.cos(phi1),
                             math.cos(d_r) - math.sin(phi1) * math.sin(phi2))
    return (round(math.degrees(phi2), 5), round(math.degrees(lam2), 5))


def assess_fire_spread_and_exposure(
    event_id: str,
    centroid_lat: float,
    centroid_lon: float,
    peak_frp: Optional[float] = None,
    mean_frp: Optional[float] = None,
    weather_dict: Optional[Dict[str, Any]] = None,
    env_dict: Optional[Dict[str, Any]] = None,
    conn=None
) -> Dict[str, Any]:
    """
    Perform a multi-factor fire spread and exposure assessment for an active fire event.
    """
    # 1. Weather parameters
    if not weather_dict:
        weather_dict = get_weather_for_location(centroid_lat, centroid_lon)

    wind_speed = float(weather_dict.get("wind_speed_kmh", 12.0) or 12.0)
    wind_dir = float(weather_dict.get("wind_direction_deg", 90.0) or 90.0)
    temp_c = float(weather_dict.get("temperature_c", 28.0) or 28.0)
    rh_pct = float(weather_dict.get("relative_humidity_pct", 50.0) or 50.0)

    # Downwind vector (direction the fire is pushed towards)
    downwind_bearing = (wind_dir + 180.0) % 360.0
    downwind_cardinal = get_wind_cardinal_direction(downwind_bearing)

    # 2. Environmental & Terrain parameters
    if not env_dict:
        env_dict = get_environmental_context_for_location(centroid_lat, centroid_lon)

    slope_deg = float(env_dict.get("slope_deg", 5.0) or 5.0)
    aspect_deg = float(env_dict.get("aspect_deg", 180.0) or 180.0)
    land_class = env_dict.get("land_cover_class", "Tree cover")

    # Slope alignment: if downwind direction aligns with uphill aspect
    # Aspect is direction face slopes towards; fire burns fastest directly uphill
    uphill_bearing = (aspect_deg + 180.0) % 360.0
    bearing_diff = abs(downwind_bearing - uphill_bearing)
    if bearing_diff > 180.0:
        bearing_diff = 360.0 - bearing_diff
    alignment_factor = math.cos(math.radians(bearing_diff)) # 1.0 = direct uphill spread

    # Topographic slope multiplier (Rothermel 1972)
    slope_rad = math.radians(min(45.0, slope_deg))
    phi_s = 5.275 * (math.tan(slope_rad) ** 2) * max(0.0, alignment_factor)

    # 3. Combustion Intensity Factor (FRP)
    frp_val = max(1.0, float(peak_frp or mean_frp or 25.0))
    frp_multiplier = min(2.5, 0.8 + (math.log10(frp_val) * 0.4))

    # 4. Fuel & Weather Rate of Spread (ROS) Proxy (km/h)
    base_fuel_ros = 0.25 # default ~250 meters/hour for moderate forest
    if "Grass" in land_class:
        base_fuel_ros = 0.65
    elif "Shrub" in land_class:
        base_fuel_ros = 0.50
    elif "Crop" in land_class:
        base_fuel_ros = 0.35

    # Moisture deficit multiplier
    moisture_deficit = max(0.5, (100.0 - rh_pct) / 50.0) * (temp_c / 25.0)
    wind_multiplier = 1.0 + (0.045 * wind_speed)

    ros_proxy_kmh = round(base_fuel_ros * wind_multiplier * (1.0 + phi_s) * moisture_deficit * frp_multiplier, 2)
    ros_proxy_kmh = max(0.05, min(3.5, ros_proxy_kmh)) # soft-cap realistic wildland speeds

    # 5. Potential Exposure Radii (12h, 24h, 48h active spread windows)
    r_12h = round(ros_proxy_kmh * 12.0 * 0.65, 2) # incorporating diurnal cooling dampener
    r_24h = round(ros_proxy_kmh * 24.0 * 0.55, 2)
    r_48h = round(ros_proxy_kmh * 48.0 * 0.45, 2)

    # 6. Generate Exposure Sector Polygon Coordinates (Arc: bearing ± 30°)
    exposure_cone_coords = []
    # Center vertex
    exposure_cone_coords.append([centroid_lon, centroid_lat])
    # Arc points along downwind bearing ± 30 deg at r_24h distance
    for angle_offset in range(-35, 36, 10):
        arc_bearing = (downwind_bearing + angle_offset) % 360.0
        pt_lat, pt_lon = _destination_point(centroid_lat, centroid_lon, arc_bearing, r_24h)
        exposure_cone_coords.append([pt_lon, pt_lat])
    # Close polygon
    exposure_cone_coords.append([centroid_lon, centroid_lat])

    # 7. Check for threatened conservation areas in downwind path
    threatened_reserves = []
    for res in KNOWN_PROTECTED_RESERVES:
        dist_to_res = _haversine_distance_km(centroid_lat, centroid_lon, res["center_lat"], res["center_lon"])
        if dist_to_res <= (r_48h + 10.0):
            # Calculate bearing to reserve center
            y = math.sin(math.radians(res["center_lon"] - centroid_lon)) * math.cos(math.radians(res["center_lat"]))
            x = (math.cos(math.radians(centroid_lat)) * math.sin(math.radians(res["center_lat"])) -
                 math.sin(math.radians(centroid_lat)) * math.cos(math.radians(res["center_lat"])) *
                 math.cos(math.radians(res["center_lon"] - centroid_lon)))
            bearing_to_res = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0

            angle_diff = abs(downwind_bearing - bearing_to_res)
            if angle_diff > 180.0:
                angle_diff = 360.0 - angle_diff

            if angle_diff <= 45.0: # Directly in downwind corridor
                urgency = "IMMINENT (<= 12h)" if dist_to_res <= r_12h else ("HIGH (<= 24h)" if dist_to_res <= r_24h else "MONITORING (24-48h)")
                threatened_reserves.append({
                    "name": res["name"],
                    "state": res["state"],
                    "distance_km": round(dist_to_res, 1),
                    "bearing_deg": round(bearing_to_res, 1),
                    "bearing_cardinal": get_wind_cardinal_direction(bearing_to_res),
                    "exposure_urgency": urgency,
                    "importance": res["biodiversity_importance"],
                })

    # Spread Potential Index (0 - 100)
    spi = (
        (min(wind_speed, 40.0) / 40.0 * 35.0) +
        (min(slope_deg, 30.0) / 30.0 * 20.0) +
        (min(frp_val, 300.0) / 300.0 * 25.0) +
        ((100.0 - rh_pct) / 100.0 * 20.0)
    )
    spread_potential_index = round(max(5.0, min(100.0, spi)), 1)

    assessment = {
        "event_id": event_id,
        "assessment_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spread_potential_index": spread_potential_index,
        "estimated_ros_proxy_kmh": ros_proxy_kmh,
        "wind_speed_kmh": wind_speed,
        "wind_origin_direction_deg": wind_dir,
        "wind_origin_cardinal": get_wind_cardinal_direction(wind_dir),
        "downwind_bearing_deg": round(downwind_bearing, 1),
        "downwind_cardinal": downwind_cardinal,
        "slope_deg": slope_deg,
        "alignment_with_slope": "Uphill Alignment (Accelerated)" if alignment_factor > 0.4 else "Cross/Downslope",
        "potential_exposure_radius_12h_km": r_12h,
        "potential_exposure_radius_24h_km": r_24h,
        "potential_exposure_radius_48h_km": r_48h,
        "exposure_cone_geojson": {
            "type": "Feature",
            "properties": {"event_id": event_id, "downwind_bearing": downwind_bearing},
            "geometry": {"type": "Polygon", "coordinates": [exposure_cone_coords]}
        },
        "threatened_assets": threatened_reserves,
        "methodology": "CELESTIAL-X-SPREAD-v1 (Physics-Grounded Screening Indicator)",
        "scientific_disclaimer": (
            "Screening model for environmental preparedness. Does not replace official "
            "fire agency perimeter mapping or evacuation orders."
        )
    }

    # Store assessment in database
    if event_id:
        store_spread_assessment(event_id, assessment, conn)

    return assessment


def store_spread_assessment(event_id: str, assessment: Dict[str, Any], conn=None) -> bool:
    """Store fire spread assessment record in SQLite."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fire_spread_assessments (
                event_id, assessment_time, spread_potential_index,
                estimated_ros_proxy_kmh, downwind_direction_deg,
                primary_exposure_bearing_deg, potential_exposure_radius_km,
                threatened_assets, methodology, confidence_rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            assessment["assessment_time"],
            assessment["spread_potential_index"],
            assessment["estimated_ros_proxy_kmh"],
            assessment["downwind_bearing_deg"],
            assessment["downwind_bearing_deg"],
            assessment["potential_exposure_radius_24h_km"],
            json.dumps(assessment.get("threatened_assets", [])),
            assessment["methodology"],
            "SCREENING_ESTIMATE",
        ))
        if own_conn:
            conn.commit()
        return True
    except Exception:
        return False
    finally:
        if own_conn:
            conn.close()


def get_latest_spread_assessment(event_id: str, conn=None) -> Optional[Dict[str, Any]]:
    """Retrieve the latest fire spread assessment for an event."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM fire_spread_assessments
            WHERE event_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (event_id,))
        row = cur.fetchone()
        if row:
            res = dict(row)
            if res.get("threatened_assets"):
                try:
                    res["threatened_assets"] = json.loads(res["threatened_assets"])
                except Exception:
                    res["threatened_assets"] = []
            return res
        return None
    finally:
        if own_conn:
            conn.close()
