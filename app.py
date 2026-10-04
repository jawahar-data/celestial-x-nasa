"""
CELESTIAL X
============
Satellite Fire Intelligence & Spatiotemporal Event Harmonization
NASA Space Apps Challenge 2026

Main entry point (Overview page).
Multi-page navigation is handled by Streamlit's pages/ directory.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pydeck as pdk
import math

from celestial.styles    import (
    ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer,
    section_header, metric_card, terminal_log, DECK_TOOLTIP,
)
from celestial.database  import init_database, get_stats
from celestial.config    import get_key_status
from celestial.fire_fuse import get_events_dataframe
from celestial.risk      import get_risk_map_data, RISK_COLOR_MAP
from celestial.reports   import generate_pending_reports

init_database()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CELESTIAL X · Fire Intelligence",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Background orb + global CSS ───────────────────────────────────────────────
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── API key check → redirect to settings if unconfigured ─────────────────────
key_status = get_key_status()
api_key    = key_status["key"]

# ── Auto-generate pending reports ONCE per session (not on every rerun) ────────
if not st.session_state.get("_reports_generated"):
    generate_pending_reports()
    st.session_state["_reports_generated"] = True

# ── Navigation bar ────────────────────────────────────────────────────────────
render_nav("OVERVIEW")

# ── First-run API key setup screen ────────────────────────────────────────────
if not key_status["configured"]:
    st.markdown("""
    <div style="max-width:520px;margin:90px auto;text-align:center;animation:fadeUp 0.6s ease;">
      <div style="font-size:4rem;margin-bottom:24px;filter:drop-shadow(0 0 32px rgba(100,180,255,0.8));animation:logoFloat 8s ease-in-out infinite;">🔭</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:2rem;font-weight:900;color:#ffffff;letter-spacing:5px;margin-bottom:6px;text-shadow:0 0 40px rgba(100,160,255,0.4);">CELESTIAL X</div>
      <div style="font-family:'Inter',sans-serif;font-size:0.7rem;color: #ffffff;letter-spacing:4px;text-transform:uppercase;margin-bottom:40px;">NASA API CONFIGURATION</div>
      <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:36px 40px;backdrop-filter:blur(40px);box-shadow:0 24px 80px rgba(0,0,0,0.7),inset 0 1px 0 rgba(255,255,255,0.05);">
        <p style="color: #ffffff;font-size:0.85rem;line-height:1.9;margin-bottom:28px;font-weight:300;">
          Enter your <strong style='color: #ffffff;'>NASA FIRMS API key</strong> once. It will be securely stored
          in a local <code>.env</code> file — never committed to git or exposed to the browser.<br/><br/>
          Get a free key at <a href='https://firms.modaps.eosdis.nasa.gov/api/area/' target='_blank'>firms.modaps.eosdis.nasa.gov</a>
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2.2, 1])
    with col_c:
        entered_key = st.text_input(
            "NASA FIRMS API Key",
            type="password",
            placeholder="Paste your NASA FIRMS API key…",
            label_visibility="collapsed",
        )
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
        save_col, demo_col = st.columns(2)
        with save_col:
            if st.button("🔐  Save & Continue", use_container_width=True):
                if entered_key.strip():
                    from celestial.config import save_api_key, validate_api_key
                    with st.spinner("Validating against NASA FIRMS…"):
                        valid, msg = validate_api_key(entered_key.strip())
                    if valid:
                        save_api_key(entered_key.strip())
                        st.success(f"✓ {msg}")
                        st.rerun()
                    else:
                        st.error(f"✗ {msg}")
                else:
                    st.warning("Please enter an API key.")
        with demo_col:
            if st.button("🎯  Demo Mode", use_container_width=True):
                from celestial.config import save_api_key
                save_api_key("DEMO_MODE")
                st.rerun()
    st.markdown(footer(), unsafe_allow_html=True)
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# OVERVIEW DASHBOARD
# ════════════════════════════════════════════════════════════════════════════

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="cx-hero">
  <style>
    .cx-hero-desc, .cx-hero p, .cx-hero div {{
      text-align: center !important;
    }}
  </style>
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    NASA SPACE APPS CHALLENGE 2026&nbsp;&nbsp;·&nbsp;&nbsp;FIRE INTELLIGENCE PLATFORM
  </div>
  <div class="cx-hero-title">CELESTIAL X</div>
  <div class="cx-hero-sub-title">Satellite Fire Intelligence &amp; Spatiotemporal Event Harmonization</div>
  <div style="width: 100%; text-align: center; display: flex; justify-content: center;">
    <p class="cx-hero-desc" style="text-align: center; margin: 0 auto 40px auto;">Real-time ingestion of NASA FIRMS MODIS &amp; VIIRS observations. Multi-day persistent fire event reconciliation via the <strong>CELESTIAL X FIRE-FUSE</strong> algorithm — combining H3 spatial indexing with haversine distance matching to track fire events across days, sensors, and orbits.</p>
  </div>
  <div class="cx-tags">
    <span class="cx-tag"><span class="dot" style="background:#ef4444"></span>MODIS NRT · 1 km</span>
    <span class="cx-tag"><span class="dot" style="background:#eab308"></span>VIIRS SNPP/NOAA-20 · 375 m</span>
    <span class="cx-tag"><span class="dot" style="background:#8b5cf6"></span>H3 Spatial Indexing</span>
    <span class="cx-tag"><span class="dot" style="background:#22c55e"></span>Multi-Day Fire Events</span>
    <span class="cx-tag"><span class="dot" style="background:#3b82f6"></span>FIRE-FUSE Engine</span>
    <span class="cx-tag"><span class="dot" style="background:#f97316"></span>CELESTIAL-X-RISK-v1</span>
    <span class="cx-tag"><span class="dot" style="background:#ec4899"></span>Auto Reports</span>
    <span class="cx-tag"><span class="dot" style="background:#14b8a6"></span>SQLite Persistence</span>
  </div>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# ── Live statistics ───────────────────────────────────────────────────────────
stats = get_stats()
st.markdown(section_header("📊", "LIVE SYSTEM METRICS"), unsafe_allow_html=True)
st.markdown(
    '<div class="cx-metrics">'
    + metric_card("Active Fire Events",    str(stats["events_active"]),   "Currently tracked",       "red")
    + metric_card("Persistent Events",     str(stats["events_total"] - stats["events_active"] - stats["events_closed"]),
                                                                            "Multi-day events",       "orange")
    + metric_card("Closed Events",         str(stats["events_closed"]),   "Reports generated",       "green")
    + metric_card("MODIS Observations",    f"{stats['modis_total']:,}",   "Raw pixels ingested",     "blue")
    + metric_card("VIIRS Observations",    f"{stats['viirs_total']:,}",   "SNPP + NOAA-20",          "purple")
    + metric_card("High-Risk Regions",     str(stats["high_risk"]),       "HIGH + VERY HIGH events", "amber")
    + '</div>',
    unsafe_allow_html=True
)

# ── Active events table ───────────────────────────────────────────────────────
st.markdown(section_header("🔥", "ACTIVE FIRE EVENTS"), unsafe_allow_html=True)
events_df = get_events_dataframe()

if events_df.empty:
    st.markdown("""
    <div class="cx-panel" style="text-align:center;padding:64px 40px;">
      <div style="font-size:3.5rem;margin-bottom:20px;opacity:0.3;">🛰</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:0.9rem;color: #ffffff;
                  margin-bottom:12px;letter-spacing:2px;">NO FIRE EVENTS YET</div>
      <p style="color: #ffffff;font-size:0.82rem;max-width:400px;margin:0 auto;line-height:1.8;">
        Go to <strong style="color: #ffffff;">💾 Data</strong> and launch the
        CELESTIAL X FIRE-FUSE pipeline to ingest NASA FIRMS satellite observations.
      </p>
    </div>
    """, unsafe_allow_html=True)
else:
    display_cols = [c for c in [
        "event_id", "status", "risk_level", "start_time", "last_observed_time",
        "duration_hours", "observation_count", "modis_count", "viirs_count",
        "peak_frp", "h3_cell_count", "centroid_lat", "centroid_lon",
    ] if c in events_df.columns]
    st.dataframe(
        events_df[display_cols].rename(columns={
            "event_id": "Event ID", "status": "Status",
            "risk_level": "Risk Level", "start_time": "Start",
            "last_observed_time": "Last Observed", "duration_hours": "Duration (hrs)",
            "observation_count": "Total Obs", "modis_count": "MODIS",
            "viirs_count": "VIIRS", "peak_frp": "Peak FRP (MW)",
            "h3_cell_count": "H3 Cells",
            "centroid_lat": "Lat", "centroid_lon": "Lon",
        }).head(25),
        use_container_width=True,
        hide_index=True,
    )

# ── Overview map (premium — satellite + 3D columns) ───────────────────────────
risk_df = get_risk_map_data()
if not risk_df.empty:
    st.markdown(section_header("🗺", "FIRE EVENT OVERVIEW  ·  SATELLITE VIEW"), unsafe_allow_html=True)

    risk_df["color"]  = risk_df["risk_level"].apply(lambda x: RISK_COLOR_MAP.get(x, RISK_COLOR_MAP[None]))
    risk_df["radius"] = risk_df["observation_count"].fillna(1).apply(
        lambda n: max(22000, min(140000, n * 5000))
    )
    max_frp = float(risk_df["peak_frp"].max() or 1.0)
    risk_df["elevation"] = risk_df["peak_frp"].fillna(0).apply(
        lambda f: max(6000, (f / max_frp) * 180_000)
    )

    layers_ov = [
        pdk.Layer(
            "ScatterplotLayer", data=risk_df,
            get_position="[longitude, latitude]",
            get_radius="radius", get_fill_color="color",
            pickable=True, stroked=True,
            get_line_color=[255, 255, 255, 25],
            line_width_min_pixels=1, id="ov_halos",
        ),
        pdk.Layer(
            "ColumnLayer", data=risk_df,
            get_position="[longitude, latitude]",
            get_elevation="elevation", elevation_scale=1,
            radius=6000, get_fill_color="color",
            pickable=True, extruded=True, coverage=0.75,
            id="ov_columns",
        ),
    ]
    view = pdk.ViewState(
        latitude=float(risk_df["latitude"].mean()),
        longitude=float(risk_df["longitude"].mean()),
        zoom=4, pitch=50, bearing=-8,
    )
    deck = pdk.Deck(
        layers=layers_ov, initial_view_state=view,
        map_style="mapbox://styles/mapbox/satellite-v9",
        tooltip={
            "html": (
                "<div style='font-family:Orbitron,sans-serif;font-weight:700;font-size:11px;"
                "color:#fff;margin-bottom:5px;'>🔥 {event_id}</div>"
                "<div style='font-size:11px;color: #ffffff;line-height:1.8;'>"
                "Status: {status}<br/>Risk: <b>{risk_level}</b><br/>"
                "Peak FRP: {peak_frp} MW<br/>Observations: {observation_count}</div>"
            ),
            "style": DECK_TOOLTIP,
        },
    )
    st.markdown(
        '<div style="border-radius:20px;overflow:hidden;'
        'border:1px solid rgba(255,255,255,0.08);'
        'box-shadow:0 20px 80px rgba(0,0,0,0.8);">',
        unsafe_allow_html=True,
    )
    st.pydeck_chart(deck, use_container_width=True, height=500)
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption(
        "🔴 Very High  |  🟠 High  |  🟡 Moderate  |  🟢 Low  "
        "·  3D column height = Peak FRP  ·  Satellite basemap"
    )

# ── Quick-start guide ─────────────────────────────────────────────────────────
st.markdown(section_header("📖", "QUICK START"), unsafe_allow_html=True)
with st.expander("How to use CELESTIAL X — click to expand"):
    st.markdown("""
### Getting Started

**Step 1 — Ingest Data**
Navigate to **💾 Data** → select region, date range → click **LAUNCH CELESTIAL X FIRE-FUSE PIPELINE**.
This fetches MODIS and VIIRS data from NASA FIRMS and runs the full pipeline.

**Step 2 — Explore Fire Events**
Navigate to **🔥 Fire Events** → browse all detected persistent multi-day fire events.
Click any event to see its timeline, FRP trend, satellite map, and risk score.

**Step 3 — Live Map**
Navigate to **🗺 Live Map** → interactive satellite map with MODIS, VIIRS,
H3 hex grid, event halos, and 3D FRP columns.

**Step 4 — Risk Assessment**
Navigate to **⚠ Risk Forecast** → CELESTIAL-X-RISK-v1 analytical indicators per event.
*(Labeled as a project-defined indicator — not a scientifically validated forecast.)*

**Step 5 — Download Reports**
When a fire event closes, a final report is auto-generated.
View and download from **📋 Reports**.

---

    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div style="text-align: center; max-width: 600px; margin: 40px auto 0;">
  <h3 style="font-family:'Orbitron', sans-serif; font-size:1.1rem; color:#fff; letter-spacing:1px; text-transform:uppercase;">About CELESTIAL X FIRE-FUSE</h3>
  <p style="color: rgba(255,255,255,0.8); margin-bottom: 20px;">The FIRE-FUSE algorithm uses <strong>two-stage spatiotemporal matching</strong>:</p>
  
  <div style="text-align: left; background: rgba(255,255,255,0.05); padding: 20px 30px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <div style="margin-bottom:16px;">
      <strong style="color: #3b82f6;">1. Stage 1 — H3 Candidate Search</strong><br/>
      <span style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">Converts lat/lon → H3 cell (res-7), searches the k-ring neighborhood for open fire events. Eliminates O(N²) pairwise comparison.</span>
    </div>
    <div>
      <strong style="color: #22c55e;">2. Stage 2 — Haversine Validation</strong><br/>
      <span style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">For each H3 candidate, computes exact distance and temporal gap. Links the observation to an existing event, or creates a new one.</span>
    </div>
  </div>

  <p style="color: rgba(255,255,255,0.8); font-size: 0.95rem; line-height: 1.6;">
    The same fire observed across <strong>5 days by MODIS and VIIRS</strong> is tracked
    as a <strong>single persistent multi-day fire event</strong> — not 5 separate records.
  </p>
</div>
    """, unsafe_allow_html=True)

st.markdown(footer(), unsafe_allow_html=True)

