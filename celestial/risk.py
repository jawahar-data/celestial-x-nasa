"""
CELESTIAL X — Risk Assessment Module
======================================
Produces a FIRE RISK indicator for each active fire event based on
observable satellite-derived metrics.

IMPORTANT SCIENTIFIC DISCLAIMER
---------------------------------
This module produces project-defined ANALYTICAL INDICATORS, not
scientifically validated fire risk forecasts.

Clearly labeled as:
    CELESTIAL-X-RISK-v1 (project-defined analytical indicator)

The indicator is based on observable satellite data:
  - Fire Radiative Power (FRP)
  - Event duration
  - Spatial expansion (H3 cell count)
  - Observation count and satellite agreement
  - Confidence levels

It does NOT:
  - Claim to predict the exact date, location, or cause of future fires
  - Incorporate real-time temperature, humidity, or wind data
    (these are documented as future improvements requiring external APIs)
  - Produce scientifically calibrated probability estimates

For real fire risk forecasting, consult official national fire danger
rating systems and meteorological services.
"""

from typing import Optional
import pandas as pd
import numpy as np

from .database import get_connection


# ── Risk level definitions ────────────────────────────────────────────────────
RISK_THRESHOLDS = {
    "VERY HIGH": 0.75,
    "HIGH":      0.50,
    "MODERATE":  0.25,
    "LOW":       0.00,
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


def compute_risk_score(event: dict) -> tuple[float, str]:
    """
    Compute the CELESTIAL-X-RISK-v1 analytical indicator for a fire event.

    Weights (project-defined, not scientifically validated):
      FRP contribution  : 40%
      Duration          : 25%
      Spatial expansion : 20%
      Satellite agree   : 10%
      Confidence        : 5%

    Returns (score: float 0–1, level: str)
    """
    # Compute duration if available
    from datetime import datetime, timezone
    start = event.get("start_time")
    last  = event.get("last_observed_time")
    dur_hrs = None
    if start and last:
        try:
            t0 = datetime.fromisoformat(start.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(last.replace("Z", "+00:00"))
            dur_hrs = (t1 - t0).total_seconds() / 3600.0
        except Exception:
            pass

    # Satellite agreement: proportion of events observed by both satellites
    modis_c = event.get("modis_count") or 0
    viirs_c = event.get("viirs_count") or 0
    total_c = event.get("observation_count") or 1
    sat_agree = min(modis_c, viirs_c) / max(total_c, 1)

    frp_s   = _score_frp(event.get("peak_frp"), event.get("mean_frp"))
    dur_s   = _score_duration(dur_hrs or event.get("duration_hours"))
    exp_s   = _score_expansion(event.get("h3_cell_count"), event.get("observation_count"))
    agr_s   = _score_agreement(sat_agree)
    conf_s  = _score_confidence(event.get("max_confidence"))

    score = (
        frp_s   * 0.40 +
        dur_s   * 0.25 +
        exp_s   * 0.20 +
        agr_s   * 0.10 +
        conf_s  * 0.05
    )
    score = round(min(1.0, max(0.0, score)), 4)

    level = "LOW"
    for lv, threshold in RISK_THRESHOLDS.items():
        if score >= threshold:
            level = lv
            break

    return score, level


def assess_all_events(log_fn=None) -> int:
    """
    Run risk assessment on all non-closed fire events.
    Updates fire_events.risk_level and inserts risk_predictions rows.
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
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for event in events:
        score, level = compute_risk_score(event)
        cur.execute(
            "UPDATE fire_events SET risk_level=?, updated_at=? WHERE event_id=?",
            (level, now, event["event_id"])
        )
        cur.execute("""
            INSERT OR REPLACE INTO risk_predictions
                (event_id, latitude, longitude, risk_level, risk_score,
                 frp_indicator, duration_factor, expansion_factor, confidence_factor,
                 assessment_date, methodology)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            event["event_id"],
            event.get("centroid_lat"), event.get("centroid_lon"),
            level, score,
            _score_frp(event.get("peak_frp"), event.get("mean_frp")),
            _score_duration(event.get("duration_hours")),
            _score_expansion(event.get("h3_cell_count"), event.get("observation_count")),
            _score_confidence(event.get("max_confidence")),
            now,
            "CELESTIAL-X-RISK-v1 (project-defined analytical indicator, not a scientifically validated forecast)",
        ))

    conn.commit()
    conn.close()
    log(f"✓ Risk assessed for {len(events)} events")
    return len(events)


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
