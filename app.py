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
    <div style="max-width:760px;margin:50px auto 30px auto;text-align:center;animation:fadeUp 0.6s ease;">
      <div style="font-size:3.5rem;margin-bottom:16px;filter:drop-shadow(0 0 32px rgba(100,180,255,0.8));animation:logoFloat 8s ease-in-out infinite;">🔭</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:2.2rem;font-weight:900;color:#ffffff;letter-spacing:5px;margin-bottom:6px;text-shadow:0 0 40px rgba(100,160,255,0.4);">CELESTIAL X</div>
      <div style="font-family:'Inter',sans-serif;font-size:0.75rem;color:#60a5fa;letter-spacing:4px;text-transform:uppercase;margin-bottom:28px;">
        NASA SPACE APPS CHALLENGE 2026 • SYSTEM ONBOARDING & SETUP
      </div>

      <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:28px 36px;backdrop-filter:blur(40px);box-shadow:0 24px 80px rgba(0,0,0,0.7);text-align:left;margin-bottom:28px;">
        <h3 style="font-family:'Orbitron',sans-serif;color:#fff;font-size:1.1rem;margin-bottom:12px;display:flex;align-items:center;gap:10px;">
          <span>🚀</span> Quick-Start Instructions — How to Run & Work With CELESTIAL X
        </h3>
        <p style="color:rgba(255,255,255,0.85);font-size:0.86rem;line-height:1.8;margin-bottom:16px;">
          CELESTIAL X reconciles over 20 years of NASA MODIS (1 km) and VIIRS (375 m) active fire observations into a harmonized burning activity calendar and persistent event intelligence platform.
        </p>

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;margin:18px 0;">
          <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;">
            <b style="color:#60a5fa;font-size:0.8rem;">1. SELECT LAUNCH MODE</b>
            <p style="font-size:0.75rem;color:rgba(255,255,255,0.65);margin-top:4px;line-height:1.5;">
              Use <b>Demo Mode</b> for instant 1-click access with preloaded 2000–2026 data, or enter a free NASA FIRMS key for live stream.
            </p>
          </div>
          <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;">
            <b style="color:#f59e0b;font-size:0.8rem;">2. BURNING CALENDARS</b>
            <p style="font-size:0.75rem;color:rgba(255,255,255,0.65);margin-top:4px;line-height:1.5;">
              Navigate to <b>📅 Burning Calendar</b> & <b>🕰️ Time Machine</b> to analyze 20-year baselines, anomaly percentiles & FRP intensity.
            </p>
          </div>
          <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;">
            <b style="color:#10b981;font-size:0.8rem;">3. RUN FIRE-FUSE</b>
            <p style="font-size:0.75rem;color:rgba(255,255,255,0.65);margin-top:4px;line-height:1.5;">
              Open <b>📥 Data Pipeline</b> to ingest observations, harmonize confidences, and cluster multi-day persistent events via H3 grids.
            </p>
          </div>
          <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;">
            <b style="color:#ec4899;font-size:0.8rem;">4. COPILOT & AUDIT</b>
            <p style="font-size:0.75rem;color:rgba(255,255,255,0.65);margin-top:4px;line-height:1.5;">
              Ask natural language questions in <b>🤖 Copilot</b> and audit cross-sensor calibration (3.82x ratio) in <b>🔬 Calibration Lab</b>.
            </p>
          </div>
        </div>

        <div style="height:1px;background:rgba(255,255,255,0.08);margin:20px 0;"></div>

        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
          <span style="font-size:0.82rem;color:rgba(255,255,255,0.7);">
            👉 <b>Recommended for evaluation:</b> Click <b>Demo Mode</b> to explore immediately with all datasets preloaded.
          </span>
          <span style="font-size:0.75rem;color:rgba(255,255,255,0.5);">
            Free key at <a href='https://firms.modaps.eosdis.nasa.gov/api/area/' target='_blank' style='color:#60a5fa;'>firms.modaps.eosdis.nasa.gov</a>
          </span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2.4, 1])
    with col_c:
        entered_key = st.text_input(
            "NASA FIRMS API Key (Optional)",
            type="password",
            placeholder="Paste your NASA FIRMS API key here (or click Demo Mode below)…",
            label_visibility="collapsed",
        )
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
        demo_col, save_col = st.columns(2)
        with demo_col:
            if st.button("🎯  Launch in Demo Mode", use_container_width=True, help="Explore immediately with preloaded 2000-2026 multi-decade records"):
                from celestial.config import save_api_key
                save_api_key("DEMO_MODE")
                st.rerun()
        with save_col:
            if st.button("🔐  Save & Connect Live API", use_container_width=True, help="Validate and connect your live NASA FIRMS API key"):
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
                    st.warning("Please paste an API key, or click Demo Mode.")
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

# ── Auto-Refresh & Ingestion Trigger ──────────────────────────────────────────
_col_rf, _col_msg = st.columns([1.5, 5])
with _col_rf:
    if st.button("🔄 Refresh Live Data", help="Clear cache and fetch latest observations", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with _col_msg:
    st.markdown(
        '<div style="font-size:0.78rem;color:rgba(255,255,255,0.6);padding-top:8px;">'
        '⚡ Synchronize local memory cache with live database & recalculate baseline deviations'
        '</div>',
        unsafe_allow_html=True
    )

# ── Operational Guide & System Instructions ──────────────────────────────────
st.markdown(section_header("🧭", "HOW TO USE CELESTIAL X · STEP-BY-STEP OPERATIONAL GUIDE"), unsafe_allow_html=True)

st.markdown("""<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:22px 24px 18px 24px;margin-bottom:28px;backdrop-filter:blur(20px);box-shadow:0 12px 40px rgba(0,0,0,0.5);">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:18px;">
<div>
<div style="font-family:'Orbitron',sans-serif;font-size:1.05rem;font-weight:800;color:#ffffff;letter-spacing:1.5px;">
SCIENTIFIC &amp; OPERATIONAL WORKFLOW ROADMAP
</div>
<div style="font-family:'Inter',sans-serif;font-size:0.8rem;color:rgba(255,255,255,0.6);margin-top:3px;">
Follow these 5 core stages to evaluate real-time satellite fire intelligence, 25-year multi-sensor baselines, and AI copilot capabilities:
</div>
</div>
<div style="display:flex;align-items:center;gap:6px;background:rgba(96,165,250,0.08);border:1px solid rgba(96,165,250,0.25);border-radius:20px;padding:5px 14px;font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#60a5fa;">
<span>💡 Scroll Top Nav with ❮ ❯ or Mouse Wheel</span>
</div>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(210px, 1fr));gap:14px;">
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(239,68,68,0.25);border-radius:12px;padding:16px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;">
<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg, #ef4444, transparent);"></div>
<div>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
<span style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;color:#ef4444;">01</span>
<span style="font-size:1.1rem;">🗺️</span>
</div>
<div style="font-family:'Orbitron',sans-serif;font-size:0.82rem;font-weight:700;color:#ffffff;letter-spacing:1px;margin-bottom:6px;">
LIVE FIRE MONITORING
</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#60a5fa;margin-bottom:8px;">
Live Map · Fire Events
</div>
<p style="font-size:0.76rem;color:rgba(255,255,255,0.72);line-height:1.6;margin:0;">
Ingest active hotspots from NASA MODIS (1 km) &amp; VIIRS (375 m). Inspect 3D globe perimeters, H3 spatial clusters, and Rothermel downwind spread cones.
</p>
</div>
<div style="margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06);font-size:0.72rem;color:rgba(255,255,255,0.5);">
🎯 <b>What to look for:</b> Multi-sensor cluster reconciliation &amp; FRP intensity.
</div>
</div>
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(245,158,11,0.25);border-radius:12px;padding:16px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;">
<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg, #f59e0b, transparent);"></div>
<div>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
<span style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;color:#f59e0b;">02</span>
<span style="font-size:1.1rem;">📅</span>
</div>
<div style="font-family:'Orbitron',sans-serif;font-size:0.82rem;font-weight:700;color:#ffffff;letter-spacing:1px;margin-bottom:6px;">
BURNING CALENDARS
</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#f59e0b;margin-bottom:8px;">
Burning Calendar · Time Machine
</div>
<p style="font-size:0.76rem;color:rgba(255,255,255,0.72);line-height:1.6;margin:0;">
Examine 25+ years (2000–2026) of fire history. Drag the <b>Time Machine</b> slider to compare yearly seasonal peaks, FRP energy anomalies, and 20-year medians.
</p>
</div>
<div style="margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06);font-size:0.72rem;color:rgba(255,255,255,0.5);">
🎯 <b>What to look for:</b> Seasonal departure percentiles across multi-decades.
</div>
</div>
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(16,185,129,0.25);border-radius:12px;padding:16px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;">
<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg, #10b981, transparent);"></div>
<div>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
<span style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;color:#10b981;">03</span>
<span style="font-size:1.1rem;">🌴</span>
</div>
<div style="font-family:'Orbitron',sans-serif;font-size:0.82rem;font-weight:700;color:#ffffff;letter-spacing:1px;margin-bottom:6px;">
RESERVE CONSERVATION
</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#10b981;margin-bottom:8px;">
Tamil Nadu · Risk Forecast
</div>
<p style="font-size:0.76rem;color:rgba(255,255,255,0.72);line-height:1.6;margin:0;">
Track high-biodiversity tiger reserves (Mudumalai, Anamalai, Sathyamangalam). Integrates live Meteomatics wind/weather with Fosberg fire weather indices.
</p>
</div>
<div style="margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06);font-size:0.72rem;color:rgba(255,255,255,0.5);">
🎯 <b>What to look for:</b> Weather-coupled spread vectors near wildlife zones.
</div>
</div>
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(139,92,246,0.25);border-radius:12px;padding:16px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;">
<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg, #8b5cf6, transparent);"></div>
<div>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
<span style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;color:#8b5cf6;">04</span>
<span style="font-size:1.1rem;">🔬</span>
</div>
<div style="font-family:'Orbitron',sans-serif;font-size:0.82rem;font-weight:700;color:#ffffff;letter-spacing:1px;margin-bottom:6px;">
SENSOR CALIBRATION LAB
</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#8b5cf6;margin-bottom:8px;">
Calibration Lab · Methodology
</div>
<p style="font-size:0.76rem;color:rgba(255,255,255,0.72);line-height:1.6;margin:0;">
Audit the 3.82x VIIRS/MODIS detection jump. Learn how cross-sensor normalization prevents false climate trend inflation. Review open KaTeX equations.
</p>
</div>
<div style="margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06);font-size:0.72rem;color:rgba(255,255,255,0.5);">
🎯 <b>What to look for:</b> Transparent regression coefficients &amp; 5-pillar formulas.
</div>
</div>
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(236,72,153,0.25);border-radius:12px;padding:16px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;">
<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg, #ec4899, transparent);"></div>
<div>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
<span style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;color:#ec4899;">05</span>
<span style="font-size:1.1rem;">🤖</span>
</div>
<div style="font-family:'Orbitron',sans-serif;font-size:0.82rem;font-weight:700;color:#ffffff;letter-spacing:1px;margin-bottom:6px;">
AI COPILOT &amp; REPORTS
</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#ec4899;margin-bottom:8px;">
Copilot · Reports Dossiers
</div>
<p style="font-size:0.76rem;color:rgba(255,255,255,0.72);line-height:1.6;margin:0;">
Ask questions in natural language. Every response shows verifiable SQL provenance with zero hallucination. Review and download multi-page PDF incident dossiers.
</p>
</div>
<div style="margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06);font-size:0.72rem;color:rgba(255,255,255,0.5);">
🎯 <b>What to look for:</b> Verified SQL transparency &amp; 1-click executive export.
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

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
    st.markdown(
        '<p style="font-size:0.78rem;color:rgba(255,255,255,0.55);margin-top:8px;text-align:center;">'
        '<span style="color:#dc2626;">&#9679;</span> Very High &nbsp;|&nbsp; '
        '<span style="color:#ea580c;">&#9679;</span> High &nbsp;|&nbsp; '
        '<span style="color:#ca8a04;">&#9679;</span> Moderate &nbsp;|&nbsp; '
        '<span style="color:#16a34a;">&#9679;</span> Low &nbsp;&middot;&nbsp; '
        '3D column height = Peak FRP &nbsp;&middot;&nbsp; Satellite basemap</p>',
        unsafe_allow_html=True
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

