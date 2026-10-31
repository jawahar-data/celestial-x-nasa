"""
CELESTIAL X — Burning Activity Calendar Engine
===============================================
Provides historical fire hotspot data aggregated by year and month,
enabling the core NASA challenge deliverable: a harmonized burning
activity calendar combining MODIS and VIIRS observations.

Scientific note
---------------
MODIS (Terra + Aqua): ~2000 onward, 1 km resolution, ~2 passes/day
VIIRS (SNPP + NOAA-20): ~2012 onward, 375 m resolution, higher sensitivity
Direct comparison without harmonization is invalid due to differences in
spatial resolution, scan geometry, and detection thresholds.
FIRE-FUSE harmonizes both sensors into a consistent observation schema.
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import date
from typing import Optional

from .database import get_connection

# Preset regions for emergency managers
PRESET_REGIONS = {
    "Global":                  (-180, -90, 180, 90),
    "Tamil Nadu, India":       (76.0, 8.0, 80.5, 13.6),
    "India (Full)":            (68.0, 8.0, 97.5, 37.5),
    "Amazon, Brazil":          (-74.0, -15.0, -44.0, 5.0),
    "California, USA":         (-124.5, 32.5, -114.0, 42.0),
    "Australia":               (113.0, -44.0, 154.0, -10.0),
    "Mediterranean":           (-6.0, 30.0, 37.0, 47.0),
    "Indonesia / SE Asia":     (95.0, -11.0, 141.0, 8.0),
    "Sub-Saharan Africa":      (-20.0, -35.0, 55.0, 20.0),
    "Custom":                  None,
}

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


@st.cache_data(ttl=60)
def get_calendar_data(west=-180.0, south=-90.0, east=180.0, north=90.0):
    """Monthly hotspot counts grouped by year, month, satellite_group (MODIS/VIIRS)."""
    conn = get_connection()
    query = """
        SELECT
            CAST(strftime('%Y', acq_date) AS INTEGER) AS year,
            CAST(strftime('%m', acq_date) AS INTEGER) AS month,
            CASE WHEN satellite = 'MODIS' THEN 'MODIS' ELSE 'VIIRS' END AS satellite_group,
            COUNT(*) AS hotspot_count
        FROM raw_observations
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
          AND acq_date IS NOT NULL AND acq_date != ''
        GROUP BY year, month, satellite_group
        ORDER BY year, month
    """
    try:
        df = pd.read_sql_query(query, conn, params=(south, north, west, east))
        df = df.dropna(subset=["year","month"])
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
    except Exception:
        df = pd.DataFrame(columns=["year","month","satellite_group","hotspot_count"])
    finally:
        conn.close()
    return df


@st.cache_data(ttl=60)
def get_monthly_totals(west=-180.0, south=-90.0, east=180.0, north=90.0):
    """Total monthly hotspots (all sensors) per year x month."""
    df = get_calendar_data(west, south, east, north)
    if df.empty:
        return pd.DataFrame()
    return (df.groupby(["year","month"])["hotspot_count"].sum()
              .reset_index().rename(columns={"hotspot_count":"total"}))


@st.cache_data(ttl=60)
def get_historical_medians(west=-180.0, south=-90.0, east=180.0, north=90.0):
    """Historical median/mean/std per calendar month across all years."""
    totals = get_monthly_totals(west, south, east, north)
    if totals.empty:
        return pd.DataFrame()
    return (totals.groupby("month")["total"]
              .agg(median_count="median", mean_count="mean",
                   std_count="std", min_count="min",
                   max_count="max", year_count="count")
              .reset_index())


@st.cache_data(ttl=60)
def get_anomaly_data(west=-180.0, south=-90.0, east=180.0, north=90.0):
    """Anomaly % vs historical median for each year x month."""
    totals  = get_monthly_totals(west, south, east, north)
    medians = get_historical_medians(west, south, east, north)
    if totals.empty or medians.empty:
        return pd.DataFrame()
    merged = totals.merge(medians[["month","median_count"]], on="month", how="left")
    merged["anomaly_pct"] = ((merged["total"] - merged["median_count"])
                              / merged["median_count"].replace(0, np.nan) * 100).round(1)
    def label(p):
        if pd.isna(p): return "No baseline"
        if p > 50:     return "Extreme (+)"
        if p > 20:     return "Above normal"
        if p >= -20:   return "Near normal"
        if p >= -50:   return "Below normal"
        return "Extreme (-)"
    merged["anomaly_label"] = merged["anomaly_pct"].apply(label)
    return merged


@st.cache_data(ttl=60)
def get_sensor_yearly(west=-180.0, south=-90.0, east=180.0, north=90.0):
    """Yearly totals by sensor for cross-sensor comparison."""
    df = get_calendar_data(west, south, east, north)
    if df.empty:
        return pd.DataFrame()
    return (df.groupby(["year","satellite_group"])["hotspot_count"]
              .sum().reset_index())


def get_heatmap_pivot(west=-180.0, south=-90.0, east=180.0, north=90.0, normalize=False):
    """Year x Month pivot for heatmap. normalize=True returns anomaly %."""
    if normalize:
        df = get_anomaly_data(west, south, east, north)
        val_col = "anomaly_pct"
    else:
        df = get_monthly_totals(west, south, east, north)
        val_col = "total"
    if df.empty:
        return pd.DataFrame()
    pivot = df.pivot_table(index="year", columns="month", values=val_col, aggfunc="sum")
    pivot.columns = [MONTH_NAMES[m-1] for m in pivot.columns]
    return pivot.sort_index(ascending=False)


def get_current_status(west=-180.0, south=-90.0, east=180.0, north=90.0):
    """Most recent month vs its historical median."""
    totals  = get_monthly_totals(west, south, east, north)
    medians = get_historical_medians(west, south, east, north)
    if totals.empty:
        return {}
    latest = totals.sort_values(["year","month"]).iloc[-1]
    yr, mo, actual = int(latest["year"]), int(latest["month"]), int(latest["total"])
    mname = date(2000, mo, 1).strftime("%B")
    row = medians[medians["month"] == mo]
    med = int(row["median_count"].values[0]) if not row.empty else None
    anom = round((actual - med) / med * 100, 1) if med else None
    return {"year":yr,"month":mo,"month_name":mname,"actual":actual,
            "median":med,"anomaly_pct":anom,
            "years_in_baseline": int(medians["year_count"].mean()) if not medians.empty else 0}


def export_hotspots_csv(west=-180.0, south=-90.0, east=180.0, north=90.0,
                        start_date=None, end_date=None):
    """Export filtered hotspots as downloadable CSV (challenge requirement)."""
    conn = get_connection()
    params = [south, north, west, east]
    extra = []
    if start_date:
        extra.append("AND acq_date >= ?"); params.append(start_date)
    if end_date:
        extra.append("AND acq_date <= ?"); params.append(end_date)
    q = f"""SELECT satellite,product,latitude,longitude,acq_date,acq_time,
                   confidence,frp,brightness,bright_ti4,daynight,ingested_at
            FROM raw_observations
            WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?
            {" ".join(extra)}
            ORDER BY acq_date DESC LIMIT 100000"""
    try:
        df = pd.read_sql_query(q, conn, params=params)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df.to_csv(index=False).encode("utf-8")
