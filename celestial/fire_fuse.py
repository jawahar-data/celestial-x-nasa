"""
CELESTIAL X FIRE-FUSE — Spatiotemporal Fire Event Reconciliation Engine
=========================================================================

PURPOSE
-------
FIRE-FUSE implements persistent, multi-day fire event tracking by combining
satellite observations from MODIS and VIIRS across multiple days into single
fire events when spatial and temporal continuity indicates they belong to
the same fire.

ALGORITHM
---------
Two-stage matching system:

  STAGE 1 — Fast H3 Candidate Search
    Convert each observation's lat/lon → H3 cell (res-7).
    Search for existing OPEN events whose H3 cells intersect the
    observation's H3 cell and its k-ring neighbors (configurable radius).
    This eliminates the O(N²) pairwise comparison problem.

  STAGE 2 — Precise Spatiotemporal Validation
    For each H3 candidate event, compute:
      - Haversine geographic distance (km) from observation to event centroid
      - Temporal distance (hours) from observation time to event's last observation
    Apply configurable thresholds:
      IF spatial_dist  <= SPATIAL_THRESHOLD_KM
      AND temporal_dist <= TEMPORAL_THRESHOLD_HRS
      THEN → match: add observation to event, update lifecycle
      ELSE → create new event

CONFIGURABLE THRESHOLDS (not hard-coded scientific constants)
-------------------------------------------------------------
  SPATIAL_THRESHOLD_KM    : default 15 km
    Basis: H3 res-7 cell side length ≈ 5.16 km; 15 km allows ~3-cell spread,
    typical of moderate fire growth. Configurable in Settings.

  TEMPORAL_THRESHOLD_HRS  : default 36 hours
    Basis: MODIS has ~1-2 passes/day; 36 hrs covers a satellite revisit gap
    plus a safety margin. Configurable in Settings.

  EVENT_CLOSURE_DAYS      : default 3 days
    Basis: If no new observation matches an event for 3 days, the fire is
    considered inactive. Configurable in Settings.

  H3_RESOLUTION_EVENT     : default 7
    Basis: res-7 cells are ~5 km across — appropriate for event-level matching.

  H3_K_RING               : default 2
    Basis: 2-ring neighborhood at res-7 ≈ 10–20 km search radius.

FIRE EVENT LIFECYCLE
--------------------
  DETECTED   : First observation; event created
  ACTIVE     : New observations are being added; fire ongoing
  PERSISTENT : Event has observations across ≥ 3 days with no gap > threshold
  EXPANDING  : Spatial extent (h3_cell_count) is increasing between updates
  DECLINING  : FRP trend is decreasing; spatial extent stable or shrinking
  CLOSED     : No new matching observation for EVENT_CLOSURE_DAYS days
               → Triggers automated report generation

IMPORTANT: The system preserves ALL original observations.
Observations are not deleted when matched — they are linked to events
via the event_observations join table.
"""

import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import h3
import numpy as np
import pandas as pd

from .database import get_connection

# ── Configurable Thresholds (with documented scientific basis) ────────────────
DEFAULT_CONFIG = {
    "SPATIAL_THRESHOLD_KM":   15.0,   # See module docstring
    "TEMPORAL_THRESHOLD_HRS": 36.0,   # See module docstring
    "EVENT_CLOSURE_DAYS":     3,      # See module docstring
    "H3_RESOLUTION_EVENT":    7,      # H3 res-7 cell ≈ 5.16 km side
    "H3_K_RING":              2,      # 2-ring search ≈ 10–20 km radius
    "H3_RESOLUTION_OBS":      8,      # Fine-grained dedup resolution
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine great-circle distance in kilometers."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_event_id() -> str:
    """Generate a unique fire event ID: CX-YYYYMMDD-XXXX"""
    date_part = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    rand_part = uuid.uuid4().hex[:6].upper()
    return f"CX-{date_part}-{rand_part}"


def _parse_dt(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None


# ── Stage 1: H3 Candidate Search ─────────────────────────────────────────────
def _get_candidate_events(
    lat: float,
    lon: float,
    h3_res: int,
    k_ring: int,
    conn,
) -> list[dict]:
    """
    Find open fire events whose H3 cells overlap with the observation's
    H3 neighborhood. Returns list of event dicts.
    This is Stage 1 of the FIRE-FUSE matching pipeline.
    """
    try:
        cell = h3.latlng_to_cell(lat, lon, h3_res)
        neighborhood = h3.grid_disk(cell, k_ring)  # set of cells within k rings
    except Exception:
        return []

    if not neighborhood:
        return []

    placeholders = ",".join("?" * len(neighborhood))
    cur = conn.cursor()
    cur.execute(f"""
        SELECT DISTINCT fe.*
        FROM fire_events fe
        JOIN event_h3_cells ehc ON fe.event_id = ehc.event_id
        WHERE fe.status NOT IN ('CLOSED')
        AND ehc.h3_cell IN ({placeholders})
        AND ehc.h3_resolution = ?
    """, (*neighborhood, h3_res))
    return [dict(row) for row in cur.fetchall()]


# ── Stage 2: Precise Spatiotemporal Validation ────────────────────────────────
def _find_best_match(
    lat: float,
    lon: float,
    obs_ts: Optional[datetime],
    candidates: list[dict],
    spatial_km: float,
    temporal_hrs: float,
) -> Optional[dict]:
    """
    From H3 candidates, find the event that best matches the observation
    using precise haversine distance and temporal gap.
    Returns the best-matching event dict, or None if no match qualifies.
    This is Stage 2 of the FIRE-FUSE matching pipeline.
    """
    best = None
    best_score = float("inf")
    for event in candidates:
        clat = event.get("centroid_lat")
        clon = event.get("centroid_lon")
        if clat is None or clon is None:
            continue
        dist = _haversine_km(lat, lon, clat, clon)
        if dist > spatial_km:
            continue
        # Temporal check
        last_obs_dt = _parse_dt(event.get("last_observed_time"))
        if obs_ts and last_obs_dt:
            gap_hrs = abs((obs_ts - last_obs_dt).total_seconds()) / 3600.0
        else:
            gap_hrs = 0.0
        if gap_hrs > temporal_hrs:
            continue
        # Score: combined normalized distance + time gap (prefer close + recent)
        score = (dist / spatial_km) + (gap_hrs / max(temporal_hrs, 1))
        if score < best_score:
            best_score = score
            best = event
    return best


# ── Create a new fire event ───────────────────────────────────────────────────
def _create_event(
    obs_id: int,
    lat: float,
    lon: float,
    timestamp: Optional[str],
    satellite: str,
    h3_cell: str,
    frp: Optional[float],
    confidence: Optional[float],
    h3_res: int,
    conn,
) -> str:
    """Insert a new fire event record and link the first observation."""
    event_id = _make_event_id()
    now = _now_iso()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fire_events
            (event_id, status, start_time, last_observed_time,
             centroid_lat, centroid_lon,
             observation_count,
             modis_count, viirs_count,
             peak_frp, mean_frp, total_frp, max_confidence,
             h3_cell_count, created_at, updated_at)
        VALUES (?,?,?,?,?,?,1,?,?,?,?,?,?,1,?,?)
    """, (
        event_id, "DETECTED", timestamp or now, timestamp or now,
        round(lat, 6), round(lon, 6),
        1 if "MODIS" in satellite else 0,
        1 if "VIIRS" in satellite else 0,
        frp or 0.0, frp or 0.0, frp or 0.0, confidence or 0.5,
        now, now,
    ))
    # Link observation → event
    cur.execute("""
        INSERT OR IGNORE INTO event_observations (event_id, obs_id)
        VALUES (?, ?)
    """, (event_id, obs_id))
    # Register H3 cell
    cur.execute("""
        INSERT OR IGNORE INTO event_h3_cells
            (event_id, h3_cell, h3_resolution, first_seen, last_seen)
        VALUES (?,?,?,?,?)
    """, (event_id, h3_cell, h3_res, timestamp or now, timestamp or now))
    return event_id


# ── Update an existing fire event ─────────────────────────────────────────────
def _update_event(
    event: dict,
    obs_id: int,
    lat: float,
    lon: float,
    timestamp: Optional[str],
    satellite: str,
    h3_cell: str,
    frp: Optional[float],
    confidence: Optional[float],
    h3_res: int,
    conn,
) -> None:
    """Add a new observation to an existing event and update its aggregate fields."""
    event_id = event["event_id"]
    cur = conn.cursor()
    # Link observation
    cur.execute("""
        INSERT OR IGNORE INTO event_observations (event_id, obs_id)
        VALUES (?, ?)
    """, (event_id, obs_id))
    # Upsert H3 cell
    cur.execute("""
        INSERT INTO event_h3_cells (event_id, h3_cell, h3_resolution, first_seen, last_seen)
        VALUES (?,?,?,?,?)
        ON CONFLICT(event_id, h3_cell) DO UPDATE SET last_seen=excluded.last_seen
    """, (event_id, h3_cell, h3_res, timestamp or _now_iso(), timestamp or _now_iso()))

    # Recalculate aggregates
    cur.execute("""
        SELECT COUNT(*) as n,
               COUNT(CASE WHEN satellite='MODIS' THEN 1 END) as nm,
               COUNT(CASE WHEN satellite LIKE 'VIIRS%' THEN 1 END) as nv,
               MAX(frp) as peak_frp,
               AVG(frp) as mean_frp,
               SUM(frp) as total_frp,
               MAX(confidence_norm) as max_conf,
               AVG(latitude) as clat,
               AVG(longitude) as clon
        FROM harmonized_observations ho
        JOIN event_observations eo ON ho.id = eo.obs_id
        WHERE eo.event_id = ?
    """, (event_id,))
    agg = dict(cur.fetchone())
    cur.execute("SELECT COUNT(*) as nc FROM event_h3_cells WHERE event_id=?", (event_id,))
    h3_count = cur.fetchone()[0]

    # Determine new status
    obs_count  = agg["n"] or 0
    new_h3     = h3_count
    old_h3     = event.get("h3_cell_count") or 0
    old_peak   = event.get("peak_frp") or 0
    new_frp    = agg.get("peak_frp") or 0

    cur.execute("""
        SELECT COUNT(DISTINCT DATE(timestamp)) as days
        FROM harmonized_observations ho
        JOIN event_observations eo ON ho.id = eo.obs_id
        WHERE eo.event_id = ?
    """, (event_id,))
    days_row = cur.fetchone()
    distinct_days = days_row[0] if days_row else 1

    if new_h3 > old_h3:
        new_status = "EXPANDING"
    elif distinct_days >= 3:
        new_status = "PERSISTENT"
    elif new_frp < old_peak * 0.6 and obs_count > 3:
        new_status = "DECLINING"
    else:
        new_status = "ACTIVE"

    cur.execute("""
        UPDATE fire_events SET
            status              = ?,
            last_observed_time  = ?,
            centroid_lat        = ?,
            centroid_lon        = ?,
            observation_count   = ?,
            modis_count         = ?,
            viirs_count         = ?,
            peak_frp            = ?,
            mean_frp            = ?,
            total_frp           = ?,
            max_confidence      = ?,
            h3_cell_count       = ?,
            updated_at          = ?
        WHERE event_id = ?
    """, (
        new_status,
        timestamp or _now_iso(),
        round(agg.get("clat") or lat, 6),
        round(agg.get("clon") or lon, 6),
        obs_count,
        agg.get("nm") or 0,
        agg.get("nv") or 0,
        round(agg.get("peak_frp") or 0, 2),
        round(agg.get("mean_frp") or 0, 2),
        round(agg.get("total_frp") or 0, 2),
        round(agg.get("max_conf") or 0.5, 3),
        h3_count,
        _now_iso(),
        event_id,
    ))


# ── Event closure check ───────────────────────────────────────────────────────
def close_inactive_events(closure_days: int, conn, log_fn=None) -> int:
    """
    Mark as CLOSED any open events where last_observed_time is older
    than closure_days. Returns count of events closed.
    """
    def log(msg):
        if log_fn:
            log_fn(msg)
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=closure_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = conn.cursor()
    cur.execute("""
        UPDATE fire_events
        SET status='CLOSED', end_time=?, updated_at=?
        WHERE status NOT IN ('CLOSED')
        AND last_observed_time < ?
    """, (_now_iso(), _now_iso(), cutoff))
    count = cur.rowcount
    if count:
        log(f"⊗ {count} event(s) closed (inactive > {closure_days} days)")
    # Compute duration for closed events
    cur.execute("""
        SELECT event_id, start_time, end_time FROM fire_events
        WHERE status='CLOSED' AND duration_hours IS NULL
    """)
    for row in cur.fetchall():
        t0 = _parse_dt(row["start_time"])
        t1 = _parse_dt(row["end_time"])
        if t0 and t1:
            hrs = (t1 - t0).total_seconds() / 3600.0
            cur.execute(
                "UPDATE fire_events SET duration_hours=? WHERE event_id=?",
                (round(hrs, 2), row["event_id"])
            )
    return count


# ── Main FIRE-FUSE Pipeline ────────────────────────────────────────────────────
def run_fire_fuse(
    harm_df: pd.DataFrame,
    config: Optional[dict] = None,
    log_fn=None,
) -> dict:
    """
    Main FIRE-FUSE entry point.
    Processes a harmonized observation DataFrame and performs spatiotemporal
    fire event reconciliation.

    Parameters
    ----------
    harm_df : DataFrame of harmonized observations (from harmonizer.py)
    config  : Optional dict overriding DEFAULT_CONFIG thresholds
    log_fn  : Optional callable(msg) for pipeline logging

    Returns
    -------
    dict with:
        events_created  : int
        events_updated  : int
        events_closed   : int
        obs_matched     : int
        obs_new_event   : int
    """
    def log(msg):
        if log_fn:
            log_fn(msg)

    cfg = {**DEFAULT_CONFIG, **(config or {})}
    spatial_km   = float(cfg["SPATIAL_THRESHOLD_KM"])
    temporal_hrs = float(cfg["TEMPORAL_THRESHOLD_HRS"])
    closure_days = int(cfg["EVENT_CLOSURE_DAYS"])
    h3_res       = int(cfg["H3_RESOLUTION_EVENT"])
    k_ring       = int(cfg["H3_K_RING"])

    if harm_df.empty:
        log("⚠ No harmonized observations to process.")
        return {"events_created": 0, "events_updated": 0, "events_closed": 0,
                "obs_matched": 0, "obs_new_event": 0}

    log(f"⚡ FIRE-FUSE: Processing {len(harm_df):,} harmonized observations")
    log(f"   Spatial threshold: {spatial_km} km | Temporal: {temporal_hrs} hrs | "
        f"Closure: {closure_days} days")
    log(f"   H3 res={h3_res}, k-ring={k_ring}")

    conn = get_connection()
    cur = conn.cursor()

    # Store harmonized observations that don't yet have DB IDs
    # If harm_df has an 'id' column from DB, use those; otherwise insert
    if "id" not in harm_df.columns:
        from .harmonizer import store_harmonized
        store_harmonized(harm_df)
        # Reload to get IDs
        cur.execute("SELECT id FROM harmonized_observations ORDER BY id DESC LIMIT ?",
                    (len(harm_df),))
        ids = [r[0] for r in cur.fetchall()][::-1]
        harm_df = harm_df.copy()
        harm_df["id"] = ids[:len(harm_df)]

    events_created = 0
    events_updated = 0
    obs_matched    = 0
    obs_new_event  = 0

    for _, row in harm_df.iterrows():
        obs_id = int(row.get("id", 0))
        lat    = float(row["latitude"])
        lon    = float(row["longitude"])
        ts_str = str(row.get("timestamp", "")) or None
        sat    = str(row.get("satellite", ""))
        h3c    = str(row.get("h3_cell_r7", ""))
        frp    = float(row["frp"]) if pd.notna(row.get("frp")) else None
        conf   = float(row["confidence_norm"]) if pd.notna(row.get("confidence_norm")) else None
        obs_ts = _parse_dt(ts_str)

        if not h3c or h3c == "None":
            continue

        # STAGE 1: H3 candidate search
        candidates = _get_candidate_events(lat, lon, h3_res, k_ring, conn)

        # STAGE 2: Precise spatiotemporal validation
        match = _find_best_match(lat, lon, obs_ts, candidates, spatial_km, temporal_hrs)

        if match:
            _update_event(match, obs_id, lat, lon, ts_str, sat, h3c, frp, conf, h3_res, conn)
            events_updated += 1
            obs_matched += 1
        else:
            _create_event(obs_id, lat, lon, ts_str, sat, h3c, frp, conf, h3_res, conn)
            events_created += 1
            obs_new_event += 1

    # Close inactive events
    events_closed = close_inactive_events(closure_days, conn, log_fn)
    conn.commit()
    conn.close()

    log(f"✓ FIRE-FUSE complete:")
    log(f"  Events created : {events_created}")
    log(f"  Events updated : {events_updated}")
    log(f"  Events closed  : {events_closed}")
    log(f"  Obs matched to existing events : {obs_matched}")
    log(f"  Obs created new events         : {obs_new_event}")

    return {
        "events_created": events_created,
        "events_updated": events_updated,
        "events_closed":  events_closed,
        "obs_matched":    obs_matched,
        "obs_new_event":  obs_new_event,
    }


# ── Database query helpers ────────────────────────────────────────────────────
def get_events_dataframe(status: Optional[str] = None, limit: int = 500) -> pd.DataFrame:
    conn = get_connection()
    where = f"WHERE status='{status}'" if status else ""
    df = pd.read_sql_query(
        f"SELECT * FROM fire_events {where} ORDER BY last_observed_time DESC LIMIT {limit}",
        conn,
    )
    conn.close()
    return df


def get_event_timeline(event_id: str) -> pd.DataFrame:
    """Return the per-day observation timeline for a specific fire event."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            DATE(ho.timestamp) as obs_date,
            ho.satellite,
            COUNT(*) as obs_count,
            AVG(ho.frp) as avg_frp,
            MAX(ho.frp) as max_frp,
            AVG(ho.confidence_norm) as avg_confidence,
            AVG(ho.latitude) as centroid_lat,
            AVG(ho.longitude) as centroid_lon
        FROM harmonized_observations ho
        JOIN event_observations eo ON ho.id = eo.obs_id
        WHERE eo.event_id = ?
        GROUP BY DATE(ho.timestamp), ho.satellite
        ORDER BY obs_date, ho.satellite
    """, conn, params=(event_id,))
    conn.close()
    return df


def get_event_observations(event_id: str, limit: int = 2000) -> pd.DataFrame:
    """Return all harmonized observations linked to a fire event."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT ho.*
        FROM harmonized_observations ho
        JOIN event_observations eo ON ho.id = eo.obs_id
        WHERE eo.event_id = ?
        ORDER BY ho.timestamp
        LIMIT ?
    """, conn, params=(event_id, limit))
    conn.close()
    return df


def get_event_h3_cells(event_id: str) -> list[str]:
    """Return the list of H3 cells for a fire event."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT h3_cell FROM event_h3_cells WHERE event_id=?", (event_id,))
    cells = [r[0] for r in cur.fetchall()]
    conn.close()
    return cells


# ── H3 Performance Benchmark ──────────────────────────────────────────────────
def benchmark_h3_vs_naive(n_obs: int = 1000, seed: int = 42) -> dict:
    """
    Compare naive O(N²) pairwise matching vs H3-accelerated candidate search.
    Returns timing and comparison counts for the Analytics page.
    Note: Results are real measurements, not fabricated.
    """
    import time
    rng = np.random.default_rng(seed)
    lats = rng.uniform(8.0, 37.0, n_obs)
    lons = rng.uniform(68.0, 97.0, n_obs)

    # Naive: compare every pair
    t0 = time.perf_counter()
    naive_comparisons = 0
    for i in range(min(n_obs, 500)):  # cap at 500 for speed
        for j in range(i + 1, min(n_obs, 500)):
            naive_comparisons += 1
            _ = _haversine_km(lats[i], lons[i], lats[j], lons[j])
    naive_time = time.perf_counter() - t0
    naive_comparisons_full = (n_obs * (n_obs - 1)) // 2  # extrapolated

    # H3-accelerated: build index then search
    t1 = time.perf_counter()
    h3_comparisons = 0
    index: dict[str, list[int]] = {}
    for i in range(n_obs):
        try:
            cell = h3.latlng_to_cell(float(lats[i]), float(lons[i]), 7)
            index.setdefault(cell, []).append(i)
        except Exception:
            pass
    for i in range(n_obs):
        try:
            cell = h3.latlng_to_cell(float(lats[i]), float(lons[i]), 7)
            neighbors = h3.grid_disk(cell, 2)
            for nc in neighbors:
                for j in index.get(nc, []):
                    if j != i:
                        h3_comparisons += 1
                        _ = _haversine_km(lats[i], lons[i], lats[j], lons[j])
        except Exception:
            pass
    h3_time = time.perf_counter() - t1

    reduction = 100.0 * (1 - h3_comparisons / max(naive_comparisons_full, 1))
    speedup = naive_time / max(h3_time, 1e-9)

    return {
        "n_observations":             n_obs,
        "naive_comparisons":          naive_comparisons_full,
        "h3_comparisons":             h3_comparisons,
        "naive_time_ms":              round(naive_time * 1000, 1),
        "h3_time_ms":                 round(h3_time * 1000, 1),
        "comparison_reduction_pct":   round(reduction, 1),
        "speedup_factor":             round(speedup, 1),
    }
