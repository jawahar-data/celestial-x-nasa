"""
CELESTIAL X — Database Module
==============================
SQLite schema for persistent fire event storage.
All tables are created here; the database file is celestial_x.db.

Tables
------
raw_observations        : Original satellite records, never modified
harmonized_observations : Normalized common schema
fire_events             : One row per fire event (lifecycle + metrics)
event_observations      : Many-to-many link: observation ↔ event
event_h3_cells          : H3 cells covered by each event
risk_predictions        : Environmental risk assessment output
reports                 : Generated fire event reports (text/HTML)
api_configuration       : Stored API configuration (key masked)
"""

import sqlite3
import os
import streamlit as st
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "celestial_x.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the CELESTIAL X SQLite database."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database() -> None:
    """Create all tables and indexes if they do not already exist."""
    conn = get_connection()
    cur = conn.cursor()

    # ── Raw Observations ──────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_observations (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        satellite       TEXT    NOT NULL,            -- MODIS | VIIRS_SNPP | VIIRS_NOAA20
        product         TEXT    NOT NULL,            -- e.g. MODIS_NRT
        latitude        REAL    NOT NULL,
        longitude       REAL    NOT NULL,
        acq_date        TEXT,                        -- YYYY-MM-DD
        acq_time        TEXT,                        -- HHMM
        acq_datetime    TEXT,                        -- ISO8601 UTC
        confidence      TEXT,                        -- l / n / h  or  numeric %
        frp             REAL,                        -- Fire Radiative Power MW
        brightness      REAL,                        -- Brightness temp K (MODIS)
        bright_ti4      REAL,                        -- VIIRS band I-4 bright temp
        bright_ti5      REAL,                        -- VIIRS band I-5 bright temp
        scan            REAL,
        track           REAL,
        daynight        TEXT,
        version         TEXT,
        quality_flag    TEXT,
        raw_source      TEXT,                        -- region / bbox requested
        ingested_at     TEXT DEFAULT (datetime('now'))
    )
    """)

    # ── Harmonized Observations ───────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS harmonized_observations (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_obs_id      INTEGER REFERENCES raw_observations(id),
        satellite       TEXT    NOT NULL,
        timestamp       TEXT    NOT NULL,            -- ISO8601 UTC
        latitude        REAL    NOT NULL,
        longitude       REAL    NOT NULL,
        h3_cell_r7      TEXT,                        -- H3 res-7 (event matching)
        h3_cell_r8      TEXT,                        -- H3 res-8 (dedup)
        confidence_norm REAL,                        -- 0.0–1.0 normalized
        frp             REAL,
        frp_proxy       REAL,                        -- brightness-derived proxy
        quality_flag    TEXT,
        source          TEXT,                        -- MODIS | VIIRS_SNPP | VIIRS_NOAA20
        harmonized_at   TEXT DEFAULT (datetime('now'))
    )
    """)

    # ── Fire Events ───────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fire_events (
        event_id            TEXT    PRIMARY KEY,     -- CX-YYYYMMDD-XXXX
        status              TEXT    NOT NULL DEFAULT 'DETECTED',
                                                     -- DETECTED|ACTIVE|PERSISTENT|EXPANDING|DECLINING|CLOSED
        start_time          TEXT    NOT NULL,        -- ISO8601 UTC
        last_observed_time  TEXT,
        end_time            TEXT,                    -- set on CLOSED
        duration_hours      REAL,
        centroid_lat        REAL,
        centroid_lon        REAL,
        bbox_west           REAL,
        bbox_south          REAL,
        bbox_east           REAL,
        bbox_north          REAL,
        observation_count   INTEGER DEFAULT 0,
        modis_count         INTEGER DEFAULT 0,
        viirs_count         INTEGER DEFAULT 0,
        h3_cell_count       INTEGER DEFAULT 0,
        peak_frp            REAL,
        mean_frp            REAL,
        total_frp           REAL,
        max_confidence      REAL,
        satellite_agreement REAL,                    -- 0–1: fraction of cells with both sensors
        spatial_expansion   REAL,                    -- km² estimated
        risk_level          TEXT,                    -- LOW|MODERATE|HIGH|VERY HIGH
        report_status       TEXT DEFAULT 'PENDING',  -- PENDING|GENERATED
        region              TEXT,
        notes               TEXT,
        created_at          TEXT DEFAULT (datetime('now')),
        updated_at          TEXT DEFAULT (datetime('now'))
    )
    """)

    # ── Event ↔ Observation link ──────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_observations (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id        TEXT    NOT NULL REFERENCES fire_events(event_id),
        obs_id          INTEGER NOT NULL REFERENCES harmonized_observations(id),
        added_at        TEXT DEFAULT (datetime('now')),
        UNIQUE(event_id, obs_id)
    )
    """)

    # ── H3 cells per event ────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_h3_cells (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id        TEXT    NOT NULL REFERENCES fire_events(event_id),
        h3_cell         TEXT    NOT NULL,
        h3_resolution   INTEGER NOT NULL DEFAULT 7,
        first_seen      TEXT,
        last_seen       TEXT,
        UNIQUE(event_id, h3_cell)
    )
    """)

    # ── Risk Predictions ──────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS risk_predictions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id        TEXT    REFERENCES fire_events(event_id),
        latitude        REAL,
        longitude       REAL,
        h3_cell         TEXT,
        risk_level      TEXT,                        -- LOW|MODERATE|HIGH|VERY HIGH
        risk_score      REAL,                        -- 0–1 analytical indicator
        frp_indicator   REAL,
        duration_factor REAL,
        expansion_factor REAL,
        confidence_factor REAL,
        assessment_date TEXT,
        methodology     TEXT DEFAULT 'CELESTIAL-X-RISK-v1 (project-defined analytical indicator)',
        created_at      TEXT DEFAULT (datetime('now'))
    )
    """)

    # ── Reports ───────────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id        TEXT    NOT NULL REFERENCES fire_events(event_id),
        report_type     TEXT    DEFAULT 'FINAL',     -- FINAL | INTERIM
        title           TEXT,
        content_md      TEXT,                        -- Markdown content
        generated_at    TEXT DEFAULT (datetime('now')),
        UNIQUE(event_id, report_type)
    )
    """)

    # ── API Configuration ─────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_configuration (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        key_name        TEXT    NOT NULL UNIQUE,     -- NASA_API_KEY
        key_masked      TEXT,                        -- ****XXXX (last 4 chars only)
        is_valid        INTEGER DEFAULT 0,           -- 0/1
        last_validated  TEXT,
        updated_at      TEXT DEFAULT (datetime('now'))
    )
    """)

    # ── Indexes ───────────────────────────────────────────────────────────────
    idx = [
        "CREATE INDEX IF NOT EXISTS idx_raw_obs_datetime  ON raw_observations(acq_datetime)",
        "CREATE INDEX IF NOT EXISTS idx_raw_obs_latlon    ON raw_observations(latitude, longitude)",
        "CREATE INDEX IF NOT EXISTS idx_harm_obs_ts       ON harmonized_observations(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_harm_obs_h3r7     ON harmonized_observations(h3_cell_r7)",
        "CREATE INDEX IF NOT EXISTS idx_harm_obs_h3r8     ON harmonized_observations(h3_cell_r8)",
        "CREATE INDEX IF NOT EXISTS idx_harm_obs_sat      ON harmonized_observations(satellite)",
        "CREATE INDEX IF NOT EXISTS idx_events_status     ON fire_events(status)",
        "CREATE INDEX IF NOT EXISTS idx_events_start      ON fire_events(start_time)",
        "CREATE INDEX IF NOT EXISTS idx_event_obs_event   ON event_observations(event_id)",
        "CREATE INDEX IF NOT EXISTS idx_event_obs_obs     ON event_observations(obs_id)",
        "CREATE INDEX IF NOT EXISTS idx_event_h3_event    ON event_h3_cells(event_id)",
        "CREATE INDEX IF NOT EXISTS idx_event_h3_cell     ON event_h3_cells(h3_cell)",
        "CREATE INDEX IF NOT EXISTS idx_risk_event        ON risk_predictions(event_id)",
        "CREATE INDEX IF NOT EXISTS idx_reports_event     ON reports(event_id)",
    ]
    for stmt in idx:
        cur.execute(stmt)

    conn.commit()
    conn.close()


@st.cache_data(ttl=30)
def get_stats() -> dict:
    """Return high-level database statistics for the Overview page."""
    conn = get_connection()
    cur = conn.cursor()
    stats = {}
    try:
        cur.execute("SELECT COUNT(*) FROM raw_observations")
        stats["raw_total"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM raw_observations WHERE satellite='MODIS'")
        stats["modis_total"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM raw_observations WHERE satellite LIKE 'VIIRS%'")
        stats["viirs_total"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fire_events")
        stats["events_total"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fire_events WHERE status IN ('ACTIVE','EXPANDING','PERSISTENT')")
        stats["events_active"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fire_events WHERE status='CLOSED'")
        stats["events_closed"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fire_events WHERE status='EXPANDING'")
        stats["events_expanding"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fire_events WHERE risk_level IN ('HIGH','VERY HIGH')")
        stats["high_risk"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM reports")
        stats["reports_total"] = cur.fetchone()[0]
    except Exception:
        stats = {k: 0 for k in [
            "raw_total","modis_total","viirs_total","events_total",
            "events_active","events_closed","events_expanding","high_risk","reports_total"
        ]}
    finally:
        conn.close()
    return stats


if __name__ == "__main__":
    init_database()
    print(f"Database initialized at: {DB_PATH}")
    print("Stats:", get_stats())
