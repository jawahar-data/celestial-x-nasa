"""CELESTIAL X — Risk Forecast Page (Premium)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
import streamlit.components.v1 as components
import pydeck as pdk
from celestial.styles    import (ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer,
                                  section_header, metric_card, DECK_TOOLTIP)
from celestial.database  import init_database
from celestial.risk      import get_risk_map_data, assess_all_events, RISK_COLOR_MAP

init_database()
st.set_page_config(page_title="CELESTIAL X · Risk Forecast", page_icon="⚠", layout="wide", initial_sidebar_state="collapsed")
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("RISK FORECAST")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    CELESTIAL-X-RISK-v1 &nbsp;·&nbsp; PROJECT-DEFINED ANALYTICAL INDICATOR
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">RISK FORECAST</div>
  <p class="cx-hero-sub-title">Satellite-Derived Analytical Indicator · Not a Scientific Fire Danger Forecast</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# Disclaimer
st.markdown("""
<div class="cx-panel" style="background:rgba(239,68,68,0.05);border-color:rgba(239,68,68,0.18);padding:20px 28px;margin-top:20px;">
  <div style="display:flex;align-items:flex-start;gap:14px;">
    <span style="font-size:1.4rem;margin-top:2px;">⚠️</span>
    <div>
      <div style="font-family:'Orbitron',sans-serif;font-size:0.62rem;font-weight:700;
                  letter-spacing:2px;color: #ffffff;margin-bottom:8px;">
        SCIENTIFIC DISCLAIMER — READ BEFORE INTERPRETING
      </div>
      <p style="color: #ffffff;font-size:0.80rem;line-height:1.8;margin:0;">
        The <strong style="color: #ffffff;">CELESTIAL-X-RISK-v1</strong> indicator is a
        <strong style="color: #ffffff;">project-defined analytical tool</strong> based solely on observable
        satellite data (FRP, duration, spatial expansion, satellite agreement, confidence).
        It does <em>not</em> predict future fires, incorporate meteorological data, determine fire causes, or
        replace national fire danger rating systems. For operational decisions, consult official fire management authorities.
      </p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

rc1, rc2 = st.columns([5,1])
with rc2:
    if st.button("🔄 Refresh", use_container_width=True):
        with st.spinner("Running CELESTIAL-X-RISK-v1…"):
            n = assess_all_events()
        st.success(f"✓ Assessed {n} events")
        st.rerun()

risk_df = get_risk_map_data()
if risk_df.empty:
    st.markdown("""
    <div class="cx-panel" style="text-align:center;padding:80px 40px;">
      <div style="font-size:4rem;opacity:0.35;margin-bottom:20px;">⚠</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:1rem;color: #ffffff;letter-spacing:2px;">
        NO RISK DATA AVAILABLE
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown(footer(), unsafe_allow_html=True)
    st.stop()

# ── Summary metrics ────────────────────────────────────────────────────────────
level_counts = risk_df["risk_level"].value_counts().to_dict()
st.markdown(section_header("📊", "RISK LEVEL DISTRIBUTION"), unsafe_allow_html=True)
st.markdown(
    '<div class="cx-metrics" style="grid-template-columns:repeat(4,1fr);">'
    + metric_card("VERY HIGH", str(level_counts.get("VERY HIGH",0)), "Highest indicator events", "red")
    + metric_card("HIGH",      str(level_counts.get("HIGH",0)),      "High indicator events",    "orange")
    + metric_card("MODERATE",  str(level_counts.get("MODERATE",0)),  "Moderate indicator events","amber")
    + metric_card("LOW",       str(level_counts.get("LOW",0)),       "Low indicator events",     "green")
    + "</div>", unsafe_allow_html=True
)

# ── Risk map ───────────────────────────────────────────────────────────────────
st.markdown(section_header("🗺", "RISK INDICATOR MAP  ·  SATELLITE VIEW"), unsafe_allow_html=True)

risk_df["color"]  = risk_df["risk_level"].apply(lambda x: RISK_COLOR_MAP.get(x, RISK_COLOR_MAP[None]))
risk_df["radius"] = risk_df["observation_count"].fillna(1).apply(
    lambda n: max(25000, min(220000, n * 9000))
)
max_frp = risk_df["peak_frp"].max() or 1.0
risk_df["elevation"] = risk_df["peak_frp"].fillna(0).apply(
    lambda f: max(8000, (f / max_frp) * 200_000)
)

# Dual layer: halo scatterplot + 3D column
layers = [
    pdk.Layer(
        "ScatterplotLayer", data=risk_df,
        get_position="[longitude, latitude]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True, stroked=True,
        get_line_color=[255,255,255,30],
        line_width_min_pixels=2,
        id="risk_halos",
    ),
    pdk.Layer(
        "ColumnLayer", data=risk_df,
        get_position="[longitude, latitude]",
        get_elevation="elevation",
        elevation_scale=1,
        radius=7000,
        get_fill_color="color",
        pickable=True,
        extruded=True,
        coverage=0.75,
        id="risk_columns",
    ),
]
view = pdk.ViewState(
    latitude=float(risk_df["latitude"].mean()),
    longitude=float(risk_df["longitude"].mean()),
    zoom=4, pitch=50, bearing=-10,
)
deck = pdk.Deck(
    layers=layers, initial_view_state=view,
    map_style="mapbox://styles/mapbox/satellite-v9",
    tooltip={
        "html": (
            "<div style='font-family:Orbitron,sans-serif;font-weight:700;font-size:11px;color:#fff;margin-bottom:5px;'>"
            "{event_id}</div>"
            "<div style='font-size:11px;color: #ffffff;line-height:1.8;'>"
            "Risk: <b>{risk_level}</b>  ·  Score: {risk_score}<br/>"
            "Peak FRP: {peak_frp} MW<br/>"
            "Status: {status}</div>"
        ),
        "style": DECK_TOOLTIP,
    },
)
st.markdown('<div style="border-radius:20px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);box-shadow:0 20px 80px rgba(0,0,0,0.8);">', unsafe_allow_html=True)
st.pydeck_chart(deck, use_container_width=True, height=520)
# Removed split close div
st.caption("🔴 Very High  |  🟠 High  |  🟡 Moderate  |  🟢 Low  ·  3D column height = Peak FRP  ·  Satellite basemap")

# ── Risk table ─────────────────────────────────────────────────────────────────
st.markdown(section_header("📋", "RISK INDICATOR TABLE"), unsafe_allow_html=True)
show_cols = [c for c in [
    "event_id","risk_level","risk_score","status",
    "peak_frp","observation_count","start_time","last_observed_time",
] if c in risk_df.columns]
st.dataframe(
    risk_df[show_cols].sort_values("risk_score", ascending=False).rename(columns={
        "event_id":"Event ID","risk_level":"Risk Level","risk_score":"Score",
        "status":"Status","peak_frp":"Peak FRP (MW)",
        "observation_count":"Observations","start_time":"Start","last_observed_time":"Last Observed",
    }),
    use_container_width=True, hide_index=True,
)

# ── Methodology ─────────────────────────────────────────────────────────────────
st.markdown(section_header("📖", "CELESTIAL-X-RISK-v1 METHODOLOGY"), unsafe_allow_html=True)
with st.expander("Full methodology and limitation documentation"):
    st.markdown("""
### CELESTIAL-X-RISK-v1

**Classification:** Project-defined analytical indicator.
**NOT** a scientifically validated fire danger rating or forecast.

#### Component Weights

| Component | Weight | Satellite Observable |
|---|---|---|
| Fire Radiative Power (FRP) | **40%** | Satellite-measured intensity (MW) |
| Event Duration | **25%** | Time from first to last observation |
| Spatial Expansion | **20%** | Number of distinct H3 cells (res-7) |
| Satellite Agreement | **10%** | Multi-sensor confirmation |
| Detection Confidence | **5%** | Observation confidence level |

#### Risk Thresholds

| Level | Composite Score |
|---|---|
| VERY HIGH | ≥ 0.75 |
| HIGH | ≥ 0.50 |
| MODERATE | ≥ 0.25 |
| LOW | < 0.25 |

#### What Is NOT Included
- Real-time temperature, humidity, or wind data
- Vegetation type, moisture content, or fuel load
- Terrain elevation or slope
- Fire suppression status
- Historical fire frequency

These are documented as **future improvements** requiring integration of external
meteorological APIs (e.g., OpenWeatherMap, ERA5) and land cover datasets.
    """)
st.markdown(footer(), unsafe_allow_html=True)
