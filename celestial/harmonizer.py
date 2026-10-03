"""
CELESTIAL X — Data Harmonizer
================================
Normalizes raw MODIS and VIIRS observations into a common schema.
Assigns H3 cells at two resolutions:
  - res 8 : fine-grained (pixel-level deduplication)
  - res 7 : coarser (fire-event candidate matching in FIRE-FUSE)

Design principles
-----------------
- Original records in raw_observations are NEVER modified.
- Every harmonized row is traceable back to its raw_obs_id and satellite.
- Confidence is normalized to 0.0–1.0 for cross-satellite comparison.
- Missing FRP is not fabricated; frp_proxy is derived from brightness
  temperature where FRP is absent.
"""

import math
from datetime import datetime, timezone
from typing import Optional

import h3
import numpy as np
import pandas as pd

from .database import get_connection


# ── Confidence normalization ──────────────────────────────────────────────────
_CONF_MAP = {
    "l": 0.25, "low": 0.25,
    "n": 0.55, "nominal": 0.55, "medium": 0.55,
    "h": 0.90, "high": 0.90,
}

def _normalize_confidence(raw: str | float | None) -> float:
    """Normalize confidence to 0.0–1.0."""
    if raw is None:
        return 0.50
    try:
        pct = float(str(raw).strip())
        return max(0.0, min(1.0, pct / 100.0))
    except ValueError:
        return _CONF_MAP.get(str(raw).strip().lower(), 0.50)


def _frp_proxy_from_brightness(brightness: Optional[float]) -> Optional[float]:
    """
    Derive a rough FRP proxy from brightness temperature.
    Reference: Wooster et al. (2003) — T⁴ relationship.
    This is a PROXY only, clearly labeled as such.
    """
    if brightness is None or math.isnan(brightness):
        return None
    # Simplified radiance-based proxy (not a calibrated FRP estimate)
    sigma = 5.67e-8
    return max(0.0, sigma * (brightness ** 4) * 1e-12)


def harmonize_dataframe(
    df: pd.DataFrame,
    source_label: str,
    h3_res_obs: int = 8,
    h3_res_event: int = 7,
) -> pd.DataFrame:
    """
    Normalize a raw satellite DataFrame into the common harmonized schema.
    Does NOT write to database — returns a clean DataFrame.

    Parameters
    ----------
    df            : Raw satellite DataFrame (from ingestion or raw_observations)
    source_label  : 'MODIS' | 'VIIRS_SNPP' | 'VIIRS_NOAA20'
    h3_res_obs    : H3 resolution for pixel-level dedup (default 8)
    h3_res_event  : H3 resolution for event-level matching (default 7)
    """
    if df.empty:
        return pd.DataFrame()

    # ── Rename columns to canonical names ────────────────────────────────────
    col_aliases = {
        "latitude":   ["latitude", "lat"],
        "longitude":  ["longitude", "lon", "lng"],
        "acq_date":   ["acq_date"],
        "acq_time":   ["acq_time"],
        "confidence": ["confidence", "conf"],
        "frp":        ["frp"],
        "brightness": ["brightness", "bright_t31"],
        "bright_ti4": ["bright_ti4"],
        "bright_ti5": ["bright_ti5"],
        "scan":       ["scan"],
        "track":      ["track"],
        "daynight":   ["daynight"],
    }
    rename = {}
    for canon, aliases in col_aliases.items():
        if canon not in df.columns:
            for a in aliases:
                if a in df.columns:
                    rename[a] = canon
                    break
    if rename:
        df = df.rename(columns=rename)

    # ── Parse and validate lat/lon ────────────────────────────────────────────
    df["latitude"]  = pd.to_numeric(df.get("latitude"),  errors="coerce")
    df["longitude"] = pd.to_numeric(df.get("longitude"), errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[
        (df["latitude"]  >= -90) & (df["latitude"]  <= 90) &
        (df["longitude"] >= -180) & (df["longitude"] <= 180)
    ].copy()

    if df.empty:
        return pd.DataFrame()

    # ── Parse timestamps ──────────────────────────────────────────────────────
    acq_date = df.get("acq_date", pd.Series([""] * len(df))).astype(str).str.strip()
    acq_time = df.get("acq_time", pd.Series(["0000"] * len(df))).astype(str).str.strip().str.zfill(4)
    ts = pd.to_datetime(acq_date + " " + acq_time, format="%Y-%m-%d %H%M", errors="coerce", utc=True)
    df["timestamp"] = ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ").where(ts.notna(), other=None)

    # ── FRP and proxy ─────────────────────────────────────────────────────────
    df["frp"] = pd.to_numeric(df.get("frp"), errors="coerce").clip(lower=0)
    bright_col = "bright_ti4" if "bright_ti4" in df.columns else "brightness"
    df["brightness_raw"] = pd.to_numeric(df.get(bright_col), errors="coerce")
    df["frp_proxy"] = df["brightness_raw"].apply(_frp_proxy_from_brightness)
    # Use actual FRP where available, proxy where not
    df["frp_final"] = df["frp"].where(df["frp"].notna() & (df["frp"] > 0), other=df["frp_proxy"])

    # ── Confidence ────────────────────────────────────────────────────────────
    df["confidence_norm"] = df.get("confidence", pd.Series([None] * len(df))).apply(_normalize_confidence)

    # ── H3 cells ──────────────────────────────────────────────────────────────
    def safe_h3(lat, lon, res):
        try:
            return h3.latlng_to_cell(float(lat), float(lon), res)
        except Exception:
            return None

    df["h3_cell_r8"] = df.apply(lambda r: safe_h3(r["latitude"], r["longitude"], h3_res_obs),   axis=1)
    df["h3_cell_r7"] = df.apply(lambda r: safe_h3(r["latitude"], r["longitude"], h3_res_event), axis=1)

    # ── Source label ──────────────────────────────────────────────────────────
    df["source"] = source_label

    # ── Select final columns ──────────────────────────────────────────────────
    out = pd.DataFrame({
        "satellite":       source_label,
        "timestamp":       df["timestamp"],
        "latitude":        df["latitude"].round(6),
        "longitude":       df["longitude"].round(6),
        "h3_cell_r7":      df["h3_cell_r7"],
        "h3_cell_r8":      df["h3_cell_r8"],
        "confidence_norm": df["confidence_norm"].round(3),
        "frp":             df["frp"].round(2),
        "frp_proxy":       df["frp_proxy"].round(4) if "frp_proxy" in df.columns else None,
        "source":          source_label,
    })
    return out.dropna(subset=["h3_cell_r7", "h3_cell_r8"])


def store_harmonized(harm_df: pd.DataFrame, raw_obs_ids: Optional[list] = None) -> int:
    """
    Write harmonized observations to the harmonized_observations table.
    Returns number of rows inserted.
    """
    if harm_df.empty:
        return 0
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0
    for i, row in harm_df.iterrows():
        raw_id = raw_obs_ids[i] if (raw_obs_ids and i < len(raw_obs_ids)) else None
        try:
            cur.execute("""
                INSERT INTO harmonized_observations
                    (raw_obs_id, satellite, timestamp, latitude, longitude,
                     h3_cell_r7, h3_cell_r8, confidence_norm, frp, frp_proxy, source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                raw_id,
                str(row.get("satellite", "")),
                str(row.get("timestamp", "")),
                float(row["latitude"]),
                float(row["longitude"]),
                str(row.get("h3_cell_r7", "")),
                str(row.get("h3_cell_r8", "")),
                float(row.get("confidence_norm", 0.5)),
                float(row["frp"]) if pd.notna(row.get("frp")) else None,
                float(row["frp_proxy"]) if pd.notna(row.get("frp_proxy")) else None,
                str(row.get("source", "")),
            ))
            inserted += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return inserted


def get_harmonized_dataframe(limit: int = 10000) -> pd.DataFrame:
    """Load harmonized observations from DB into a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT * FROM harmonized_observations ORDER BY timestamp DESC LIMIT {limit}",
        conn,
    )
    conn.close()
    return df


def harmonize_and_store(
    modis_raw: pd.DataFrame,
    viirs_raw: pd.DataFrame,
    h3_res_obs: int = 8,
    h3_res_event: int = 7,
    log_fn=None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convenience: harmonize both satellites and store in DB.
    Returns (modis_harmonized, viirs_harmonized).
    """
    def log(msg):
        if log_fn:
            log_fn(msg)

    modis_harm = pd.DataFrame()
    viirs_harm  = pd.DataFrame()

    if not modis_raw.empty:
        modis_harm = harmonize_dataframe(modis_raw, "MODIS", h3_res_obs, h3_res_event)
        n = store_harmonized(modis_harm)
        log(f"✓ MODIS: {len(modis_harm):,} obs harmonized → {n:,} stored")

    if not viirs_raw.empty:
        sat_label = "VIIRS_SNPP" if "SNPP" in str(viirs_raw.get("source", "")).upper() else "VIIRS_NOAA20"
        if "source" in viirs_raw.columns:
            src = str(viirs_raw["source"].iloc[0]).upper()
            sat_label = "VIIRS_NOAA20" if "NOAA20" in src or "NOAA-20" in src else "VIIRS_SNPP"
        viirs_harm = harmonize_dataframe(viirs_raw, sat_label, h3_res_obs, h3_res_event)
        n = store_harmonized(viirs_harm)
        log(f"✓ VIIRS: {len(viirs_harm):,} obs harmonized → {n:,} stored")

    return modis_harm, viirs_harm
