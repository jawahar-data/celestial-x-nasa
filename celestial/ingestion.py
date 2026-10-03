"""
CELESTIAL X — Data Ingestion Module
=====================================
Fetches raw MODIS and VIIRS observations from the NASA FIRMS Area CSV API
and stores them in the raw_observations table.

The raw data is NEVER modified — it is the ground truth.
All processing happens downstream in harmonizer.py and fire_fuse.py.

NASA FIRMS API reference: https://firms.modaps.eosdis.nasa.gov/api/
"""

import io
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import requests

from .database import get_connection

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Available products
PRODUCTS = {
    "MODIS NRT":       "MODIS_NRT",
    "VIIRS SNPP NRT":  "VIIRS_SNPP_NRT",
    "VIIRS NOAA-20 NRT": "VIIRS_NOAA20_NRT",
}

# Satellite label from product code
PRODUCT_TO_SAT = {
    "MODIS_NRT":       "MODIS",
    "VIIRS_SNPP_NRT":  "VIIRS_SNPP",
    "VIIRS_NOAA20_NRT":"VIIRS_NOAA20",
}

REGION_BBOXES = {
    "India (Subcontinent)":  "65.0,6.5,100.0,37.0",
    "California (USA)":      "-124.5,32.5,-114.1,42.0",
    "Australia (Eastern)":   "138.0,-40.0,155.0,-10.0",
    "Amazon Basin (Brazil)": "-74.0,-20.0,-44.0,5.0",
    "Southeast Asia":        "95.0,-10.0,141.0,28.0",
    "Sub-Saharan Africa":    "10.0,-35.0,45.0,15.0",
    "Siberia (Russia)":      "60.0,50.0,140.0,75.0",
    "Western USA":           "-125.0,30.0,-102.0,49.0",
    "Canada (Boreal)":       "-140.0,49.0,-52.0,70.0",
    "Mediterranean Basin":   "-10.0,30.0,40.0,48.0",
}


def fetch_raw(
    api_key: str,
    product: str,
    bbox: str,
    day_range: int = 1,
    log_fn=None,
) -> pd.DataFrame:
    """
    Fetch raw satellite fire data from NASA FIRMS API.

    Parameters
    ----------
    api_key   : NASA FIRMS API key
    product   : Product code e.g. 'MODIS_NRT'
    bbox      : 'west,south,east,north' bounding box string
    day_range : Number of past days to fetch (1–10)
    log_fn    : Optional callable(msg: str) for pipeline logging

    Returns
    -------
    pd.DataFrame with raw satellite columns (unchanged from API response)
    """
    def log(msg):
        if log_fn:
            log_fn(msg)

    url = f"{FIRMS_BASE}/{api_key}/{product}/{bbox}/{day_range}"
    log(f"→ GET {product} | bbox={bbox} | days={day_range}")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        text = r.text.strip()
        if not text:
            log(f"⚠ Empty response for {product}")
            return pd.DataFrame()
        if any(kw in text.lower() for kw in ("invalid", "unauthorized", "error")):
            log(f"✗ API error for {product}: {text[:120]}")
            return pd.DataFrame()
        df = pd.read_csv(io.StringIO(text), low_memory=False)
        log(f"✓ {product}: {len(df):,} raw pixels received")
        return df
    except requests.exceptions.Timeout:
        log(f"✗ Timeout fetching {product}")
        return pd.DataFrame()
    except Exception as exc:
        log(f"✗ {exc}")
        return pd.DataFrame()


def store_raw(df: pd.DataFrame, product: str, bbox: str) -> int:
    """
    Insert raw satellite observations into raw_observations table.
    Skips rows with invalid lat/lon.
    Returns count of rows inserted.
    """
    if df.empty:
        return 0
    satellite = PRODUCT_TO_SAT.get(product, product)
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        try:
            lat = float(row.get("latitude", float("nan")))
            lon = float(row.get("longitude", float("nan")))
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            acq_date = str(row.get("acq_date", "")).strip()
            acq_time = str(row.get("acq_time", "0000")).strip().zfill(4)
            acq_dt = None
            try:
                acq_dt = datetime.strptime(
                    f"{acq_date} {acq_time}", "%Y-%m-%d %H%M"
                ).replace(tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
            cur.execute("""
                INSERT INTO raw_observations
                    (satellite, product, latitude, longitude, acq_date, acq_time,
                     acq_datetime, confidence, frp, brightness, bright_ti4,
                     bright_ti5, scan, track, daynight, version, raw_source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                satellite, product, lat, lon, acq_date, acq_time, acq_dt,
                str(row.get("confidence", "")),
                _safe_float(row.get("frp")),
                _safe_float(row.get("brightness") or row.get("bright_t31")),
                _safe_float(row.get("bright_ti4")),
                _safe_float(row.get("bright_ti5")),
                _safe_float(row.get("scan")),
                _safe_float(row.get("track")),
                str(row.get("daynight", "")),
                str(row.get("version", "")),
                bbox,
            ))
            inserted += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return inserted


def get_raw_as_dataframe(
    satellite: Optional[str] = None,
    limit: int = 5000,
) -> pd.DataFrame:
    """Load raw observations from DB into a DataFrame."""
    conn = get_connection()
    where = f"WHERE satellite='{satellite}'" if satellite else ""
    df = pd.read_sql_query(
        f"SELECT * FROM raw_observations {where} ORDER BY acq_datetime DESC LIMIT {limit}",
        conn,
    )
    conn.close()
    return df


# ── Demo / synthetic data for offline testing ──────────────────────────────
def generate_demo_observations(
    region_bbox: str,
    n_days: int = 5,
    n_fires: int = 8,
    rng_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate realistic synthetic MODIS + VIIRS observations that simulate
    multi-day persistent fire events for offline/demo mode.

    Creates `n_fires` fire clusters, each observed across multiple days
    with slightly varying positions (simulating real fire movement).
    Returns (modis_df, viirs_df) — not stored in DB automatically.
    """
    rng = np.random.default_rng(rng_seed)
    west, south, east, north = map(float, region_bbox.split(","))
    clat = rng.uniform(south + 1, north - 1, n_fires)
    clon = rng.uniform(west + 1, east - 1, n_fires)
    from datetime import timedelta
    base_date = datetime.now(tz=timezone.utc).date()

    modis_rows, viirs_rows = [], []
    for day_offset in range(n_days):
        obs_date = (base_date - timedelta(days=n_days - 1 - day_offset)).strftime("%Y-%m-%d")
        # Each fire: decide which satellites observe it today
        for fi in range(n_fires):
            # Random chance each satellite observes each fire each day
            if rng.random() < 0.75:  # MODIS observes ~75% of days
                n_m = rng.integers(1, 5)
                for _ in range(n_m):
                    lat = float(np.clip(rng.normal(clat[fi], 0.08), south, north))
                    lon = float(np.clip(rng.normal(clon[fi], 0.08), west, east))
                    t = f"{rng.integers(0,24):02d}{rng.integers(0,60):02d}"
                    modis_rows.append({
                        "latitude": round(lat, 5),
                        "longitude": round(lon, 5),
                        "acq_date": obs_date,
                        "acq_time": t,
                        "confidence": rng.choice(["l", "n", "h"]),
                        "frp": round(float(rng.exponential(22)), 1),
                        "brightness": round(float(rng.uniform(310, 430)), 1),
                        "bright_t31": round(float(rng.uniform(290, 320)), 1),
                        "scan": round(float(rng.uniform(1, 3)), 2),
                        "track": round(float(rng.uniform(1, 3)), 2),
                        "daynight": rng.choice(["D", "N"]),
                        "source": "MODIS",
                        "fire_cluster": fi,  # metadata for test validation
                    })
            if rng.random() < 0.80:  # VIIRS observes ~80% of days
                n_v = rng.integers(2, 8)
                for _ in range(n_v):
                    lat = float(np.clip(rng.normal(clat[fi], 0.06), south, north))
                    lon = float(np.clip(rng.normal(clon[fi], 0.06), west, east))
                    t = f"{rng.integers(0,24):02d}{rng.integers(0,60):02d}"
                    viirs_rows.append({
                        "latitude": round(lat, 5),
                        "longitude": round(lon, 5),
                        "acq_date": obs_date,
                        "acq_time": t,
                        "confidence": rng.choice(["l", "n", "h"]),
                        "frp": round(float(rng.exponential(14)), 1),
                        "bright_ti4": round(float(rng.uniform(295, 390)), 1),
                        "bright_ti5": round(float(rng.uniform(270, 320)), 1),
                        "scan": round(float(rng.uniform(0.3, 1.5)), 2),
                        "track": round(float(rng.uniform(0.3, 1.5)), 2),
                        "daynight": rng.choice(["D", "N"]),
                        "source": "VIIRS",
                        "fire_cluster": fi,
                    })

    modis_df = pd.DataFrame(modis_rows) if modis_rows else pd.DataFrame()
    viirs_df  = pd.DataFrame(viirs_rows) if viirs_rows else pd.DataFrame()
    return modis_df, viirs_df


def _safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None
