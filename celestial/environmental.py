"""
CELESTIAL X - Environmental Context Intelligence Engine
=========================================================
Supplements remote sensing thermal anomalies with auxiliary environmental drivers:
  - Ambient 2m Air Temperature (°C)
  - Relative Humidity (%)
  - Surface Wind Speed (km/h)
  - Soil & Fine Fuel Dryness Index (0-100)

Scientific transparency
-----------------------
Observed satellite active fire hotspots (FIRMS thermal radiation) are strictly
distinguished from modeled fire weather conditions. Environmental context explains
why fires behave and spread differently across seasonal cycles.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Regional climatological environmental baselines (Monthly averages)
REGIONAL_CLIMATOLOGY = {
    "Tamil Nadu, India": {
        "temp": [27.5, 29.8, 32.4, 34.1, 35.2, 33.8, 32.5, 31.9, 31.2, 29.8, 27.9, 26.8],
        "humidity": [68, 62, 54, 52, 56, 58, 60, 62, 65, 74, 80, 75],
        "wind_speed": [12, 14, 16, 18, 22, 24, 23, 21, 17, 13, 15, 14],
        "dryness_index": [45, 68, 88, 92, 85, 65, 55, 50, 48, 35, 25, 30],
    },
    "Amazon, Brazil": {
        "temp": [26.2, 26.1, 26.3, 26.4, 26.5, 26.8, 27.2, 28.1, 28.9, 28.5, 27.8, 26.9],
        "humidity": [88, 90, 89, 87, 85, 80, 75, 68, 65, 72, 78, 85],
        "wind_speed": [8, 8, 9, 9, 10, 11, 12, 14, 15, 13, 10, 9],
        "dryness_index": [20, 18, 22, 25, 35, 55, 75, 92, 95, 82, 55, 30],
    },
    "California, USA": {
        "temp": [9.5, 11.2, 13.5, 16.2, 19.8, 24.1, 27.5, 27.0, 24.5, 19.2, 13.5, 9.8],
        "humidity": [75, 70, 65, 55, 48, 40, 35, 34, 38, 48, 62, 74],
        "wind_speed": [14, 15, 17, 19, 21, 22, 20, 19, 22, 25, 20, 15],
        "dryness_index": [25, 30, 40, 55, 72, 88, 96, 98, 94, 82, 50, 30],
    },
    "Australia": {
        "temp": [27.2, 26.8, 24.5, 20.8, 16.5, 13.8, 13.2, 14.8, 18.2, 21.5, 24.2, 26.1],
        "humidity": [55, 58, 62, 68, 74, 78, 76, 70, 62, 55, 52, 53],
        "wind_speed": [20, 19, 18, 16, 15, 16, 17, 18, 21, 23, 22, 21],
        "dryness_index": [92, 90, 78, 55, 35, 25, 22, 30, 48, 68, 82, 88],
    },
}

def get_environmental_context(region_name: str = "Tamil Nadu, India", month: int = 3) -> Dict[str, Any]:
    """
    Retrieve environmental context and wildfire weather risk factors for a region.
    """
    clim = REGIONAL_CLIMATOLOGY.get(region_name, REGIONAL_CLIMATOLOGY["Tamil Nadu, India"])
    m_idx = max(0, min(11, month - 1))

    temp = clim["temp"][m_idx]
    hum = clim["humidity"][m_idx]
    wind = clim["wind_speed"][m_idx]
    dry = clim["dryness_index"][m_idx]

    # Simplified Fire Weather Danger Score (0 - 100)
    # Higher temp, lower humidity, higher wind, higher fuel dryness -> Higher score
    fw_score = (
        (temp / 40.0 * 25.0) +
        ((100.0 - hum) / 100.0 * 30.0) +
        (min(wind, 50.0) / 50.0 * 20.0) +
        (dry / 100.0 * 25.0)
    )
    fw_score = round(max(0.0, min(100.0, fw_score)), 1)

    danger_rating = "EXTREME" if fw_score >= 80 else ("VERY HIGH" if fw_score >= 65 else ("HIGH" if fw_score >= 50 else ("MODERATE" if fw_score >= 30 else "LOW")))

    monthly_series = []
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for i in range(12):
        monthly_series.append({
            "month": month_names[i],
            "temperature_c": clim["temp"][i],
            "relative_humidity_pct": clim["humidity"][i],
            "wind_speed_kmh": clim["wind_speed"][i],
            "fuel_dryness_index": clim["dryness_index"][i],
        })

    return {
        "region": region_name,
        "selected_month": month_names[m_idx],
        "temperature_c": temp,
        "relative_humidity_pct": hum,
        "wind_speed_kmh": wind,
        "fuel_dryness_index": dry,
        "fire_weather_score": fw_score,
        "danger_rating": danger_rating,
        "monthly_series": monthly_series,
        "scientific_disclaimer": (
            "Environmental context is an auxiliary diagnostic indicator and should be interpreted "
            "in conjunction with remote sensing active fire observations."
        )
    }
