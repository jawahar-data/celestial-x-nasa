"""
CELESTIAL X — Burning Activity Calendar & Fire Regime Intelligence
====================================================================
The central NASA challenge deliverable:
A harmonized burning activity calendar combining MODIS and VIIRS observations:
  - Interactive multi-decade burning heatmaps (Total, Anomaly %, Percentile Rank)
  - Satellite Observation Coverage Intelligence (coverage-adjusted indicators)
  - Fire Season Intelligence (Onset, Peak, Cessation, Duration, Shift)
  - Protected Ecosystem & Biodiversity Monitoring
  - Environmental Context (Temperature, Humidity, Wind, Dryness)
  - Multi-Region Comparison (Side-by-side analysis)
  - Downloadable CSV Export of Harmonized Observations
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
import json

from celestial.styles   import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header, metric_card
from celestial.database import init_database
from celestial.calendar import (
    PRESET_REGIONS, MONTH_NAMES,
    get_monthly_totals, get_historical_medians,
    get_anomaly_data, get_heatmap_pivot,
    get_sensor_yearly, get_current_status,
    export_hotspots_csv,
)
from celestial.coverage import get_coverage_metrics
from celestial.season   import analyze_fire_season
from celestial.protected_areas import analyze_protected_areas
from celestial.environmental   import get_environmental_context

init_database()
st.set_page_config(
    page_title="CELESTIAL X — Burning Calendar",
    page_icon="📅", layout="wide",
    initial_sidebar_state="collapsed",
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("BURNING CALENDAR")

# Hero
st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    HARMONIZED FIRE ACTIVITY • 2000–2026 CONTINUOUS RECORD • NASA FIRMS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">BURNING CALENDAR</div>
  <p class="cx-hero-sub-title">Historical Baseline • Seasonal Regimes • Observation Coverage • Anomaly Percentiles</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# Area of Interest (AOI) Selector
st.markdown(section_header("📍", "AREA OF INTEREST & REGIONAL PRESETS"), unsafe_allow_html=True)

col_preset, col_coords, col_geojson = st.columns([1.5, 2, 1.5])

with col_preset:
    preset = st.selectbox("Select Monitored Region", list(PRESET_REGIONS.keys()), index=1)

coords = PRESET_REGIONS.get(preset)

with col_coords:
    if coords:
        west, south, east, north = coords
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);'
            f'border-radius:12px;padding:12px 18px;font-size:0.82rem;color:rgba(255,255,255,0.85);margin-top:24px;">'
            f'<b style="color:#60a5fa;">Coordinates (W, S, E, N):</b> {west}°W, {south}°S, {east}°E, {north}°N</div>',
            unsafe_allow_html=True
        )
    else:
        c1, c2, c3, c4 = st.columns(4)
        west  = c1.number_input("West",  value=-180.0, min_value=-180.0, max_value=180.0, step=0.5)
        south = c2.number_input("South", value=-90.0,  min_value=-90.0,  max_value=90.0,  step=0.5)
        east  = c3.number_input("East",  value=180.0,  min_value=-180.0, max_value=180.0, step=0.5)
        north = c4.number_input("North", value=90.0,   min_value=-90.0,  max_value=90.0,  step=0.5)

with col_geojson:
    uploaded_geo = st.file_uploader("Upload AOI GeoJSON (Optional)", type=["geojson", "json"], help="Upload custom boundary polygons")
    if uploaded_geo:
        try:
            geo_data = json.load(uploaded_geo)
            st.success("Custom GeoJSON boundary loaded successfully.")
        except Exception:
            st.warning("Invalid GeoJSON format.")

# Load core datasets
with st.spinner("Compiling multi-decade harmonized burning calendar..."):
    status    = get_current_status(west, south, east, north)
    totals    = get_monthly_totals(west, south, east, north)
    medians   = get_historical_medians(west, south, east, north)
    anom_df   = get_anomaly_data(west, south, east, north)
    sensor_yr = get_sensor_yearly(west, south, east, north)
    cov_data  = get_coverage_metrics(west, south, east, north)
    season    = analyze_fire_season(west, south, east, north)

# Current Status Metric Cards
if status:
    pct = status.get("anomaly_pct", 0)
    color = "#ef4444" if pct > 30 else ("#f59e0b" if pct > 10 else ("#10b981" if pct > -20 else "#3b82f6"))
    sign = "+" if pct > 0 else ""

    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("MONITORED PERIOD", f"{status.get('month_name')} {status.get('year')}", f"{status.get('years_in_baseline', 20)}-year baseline")}
      {metric_card("CURRENT HOTSPOTS", f"{status.get('actual', 0):,}", "Harmonized active thermal detections")}
      {metric_card("HISTORICAL MEDIAN", f"{status.get('median', 0):,}", f"IQR: {status.get('p25',0):,} – {status.get('p75',0):,}")}
      {metric_card("ANOMALY DEVIATION", f"{sign}{pct:.1f}%", f"Z-Score: {status.get('z_score', 0.0):+.2f}", color)}
      {metric_card("PERCENTILE RANKING", f"{status.get('percentile_rank', 50):.0f}th %ile", status.get("severity", "Normal"), color)}
    </div>
    """, unsafe_allow_html=True)

# Main Navigation Tabs for the Calendar Page
tab_cal, tab_season, tab_coverage, tab_pa, tab_env, tab_compare = st.tabs([
    "📅 BURNING CALENDAR MATRIX",
    "🔥 FIRE SEASON REGIMES",
    "🛰️ OBSERVATION COVERAGE",
    "🌿 PROTECTED ECOSYSTEMS",
    "🌡️ ENVIRONMENTAL CONTEXT",
    "⚖️ DUAL-REGION COMPARISON",
])

# -------------------------------------------------------------
# TAB 1: BURNING CALENDAR MATRIX
# -------------------------------------------------------------
with tab_cal:
    st.markdown(section_header("📅", "MULTI-DECADE BURNING ACTIVITY HEATMAP"), unsafe_allow_html=True)
    
    col_mode, col_ramp = st.columns([2, 2])
    with col_mode:
        view_mode = st.radio(
            "Heatmap Display Mode:",
            ["Total Harmonized Hotspots", "Anomaly % vs Historical Median", "Historical Percentile Rank (0–100%)"],
            horizontal=True
        )
    with col_ramp:
        color_scheme = st.selectbox(
            "Accessible Color Ramp:",
            ["Viridis (Perceptually Uniform)", "Inferno (High Contrast)", "Plasma", "Cividis (Colorblind Safe)", "Flame Red"],
            index=0
        )

    mode_key = "total"
    scale_name = "Viridis"
    if "Anomaly" in view_mode:
        mode_key = "anomaly_pct"
    elif "Percentile" in view_mode:
        mode_key = "percentile"

    if "Inferno" in color_scheme: scale_name = "Inferno"
    elif "Plasma" in color_scheme: scale_name = "Plasma"
    elif "Cividis" in color_scheme: scale_name = "Cividis"
    elif "Flame" in color_scheme: scale_name = [[0, "#1a1a2e"], [0.25, "#16213e"], [0.5, "#e94560"], [0.75, "#ff7b54"], [1, "#ffb26b"]]

    pivot = get_heatmap_pivot(west, south, east, north, mode=mode_key)

    if not pivot.empty:
        fig_hm = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=[str(y) for y in pivot.index.tolist()],
            colorscale=scale_name,
            colorbar=dict(
                title=dict(
                    text="Percentile Rank" if mode_key=="percentile" else ("Anomaly %" if mode_key=="anomaly_pct" else "Hotspots"),
                    font=dict(color="#fff", size=11),
                ),
                tickfont=dict(color="#fff", size=10),
            ),
            hovertemplate="<b>Year: %{y} • %{x}</b><br>Value: <b>%{z:,.1f}</b><extra></extra>",
        ))
        fig_hm.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=460,
            font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
            xaxis=dict(tickfont=dict(color="#fff", size=11), side="top", showgrid=False),
            yaxis=dict(tickfont=dict(color="#fff", size=11), dtick=1, showgrid=False),
            margin=dict(l=50, r=20, t=50, b=30),
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    # Climatological Baseline Table
    st.markdown(section_header("📊", "CLIMATOLOGICAL MONTHLY BASELINE (2000–2026)"), unsafe_allow_html=True)
    if not medians.empty:
        disp_med = medians.copy()
        disp_med["Month"] = disp_med["month"].apply(lambda m: MONTH_NAMES[m-1])
        disp_med = disp_med.rename(columns={
            "median_count": "Historical Median",
            "mean_count": "Historical Mean",
            "p25": "25th %ile",
            "p75": "75th %ile",
            "std_count": "Std Dev",
            "min_count": "Historical Min",
            "max_count": "Historical Max",
            "year_count": "Years Observed"
        })
        for c in ["Historical Median", "Historical Mean", "25th %ile", "75th %ile", "Std Dev", "Historical Min", "Historical Max"]:
            disp_med[c] = disp_med[c].round(0).astype("Int64")
        st.dataframe(disp_med[["Month", "Historical Median", "25th %ile", "75th %ile", "Historical Mean", "Std Dev", "Historical Min", "Historical Max", "Years Observed"]].set_index("Month"), use_container_width=True)

# -------------------------------------------------------------
# TAB 2: FIRE SEASON REGIMES
# -------------------------------------------------------------
with tab_season:
    st.markdown(section_header("🔥", "FIRE SEASON INTELLIGENCE & CLIMATOLOGICAL REGIME"), unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("SEASON ONSET", season['onset_month'], "10% cumulative annual burn", "#60a5fa")}
      {metric_card("PEAK BURN MONTH", season['peak_month'], "Maximum monthly hotspot density", "#ef4444")}
      {metric_card("SEASON CESSATION", season['cessation_month'], "90% cumulative annual burn", "#10b981")}
      {metric_card("SEASON DURATION", f"{season['duration_months']} Months", f"~{season['duration_days']} active burning days", "#f59e0b")}
      {metric_card("INTER-ANNUAL SHIFT", f"{season['shift_days']} Days", "Earlier arrival vs 2000 baseline", "#a855f7")}
    </div>
    """, unsafe_allow_html=True)

    prof_df = pd.DataFrame(season["monthly_profile"])
    fig_regime = go.Figure()
    fig_regime.add_trace(go.Bar(
        x=prof_df["month_name"], y=prof_df["mean_hotspots"],
        name="Mean Monthly Hotspots",
        marker_color=["#ef4444" if r else "#3b82f6" for r in prof_df["is_core_season"]]
    ))
    fig_regime.add_trace(go.Scatter(
        x=prof_df["month_name"], y=prof_df["cum_pct"],
        name="Cumulative % of Annual Burn",
        yaxis="y2",
        mode="lines+markers", line=dict(color="#f59e0b", width=3)
    ))
    fig_regime.update_layout(
        title="Regional Fire Climatology Curve & Core Season Window",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        yaxis=dict(title="Mean Hotspot Count", gridcolor="rgba(255,255,255,0.06)"),
        yaxis2=dict(title="Cumulative Annual Burn (%)", overlaying="y", side="right", range=[0, 105]),
        legend=dict(bgcolor="rgba(0,0,0,0.5)"),
        margin=dict(l=40, r=40, t=50, b=40), height=380
    )
    st.plotly_chart(fig_regime, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: OBSERVATION COVERAGE
# -------------------------------------------------------------
with tab_coverage:
    st.markdown(section_header("🛰️", "SATELLITE OBSERVATION COVERAGE INTELLIGENCE"), unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("ACTIVE OBSERVATION DAYS", f"{cov_data['active_observation_days']} Days", f"Out of {cov_data['total_days']} total days", "#60a5fa")}
      {metric_card("COVERAGE COMPLETENESS", f"{cov_data['coverage_completeness_pct']}%", "Constellation temporal coverage", "#10b981")}
      {metric_card("OBSERVED HOTSPOTS", f"{cov_data['raw_hotspots']:,}", "Direct sensor detections", "#f59e0b")}
      {metric_card("COVERAGE ADJUSTED", f"{int(cov_data['coverage_adjusted_hotspots']):,}", "Normalized for missing swaths", "#ec4899")}
    </div>
    """, unsafe_allow_html=True)

    c_m1, c_m2 = st.columns(2)
    with c_m1:
        # Monthly Coverage Completeness Bar Chart
        m_cov_df = pd.DataFrame(cov_data["monthly_coverage"])
        m_cov_df["Month"] = m_cov_df["month"].apply(lambda m: MONTH_NAMES[m-1])
        fig_cov = px.bar(
            m_cov_df, x="Month", y="completeness_pct", color="quality_flag",
            title="Monthly Observation Completeness Index (%)",
            color_discrete_map={"HIGH": "#10b981", "MODERATE": "#f59e0b", "POOR_OR_CLOUD_COVERED": "#ef4444"}
        )
        fig_cov.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#fff"), yaxis=dict(range=[0, 105], title="Completeness %", gridcolor="rgba(255,255,255,0.06)"))
        st.plotly_chart(fig_cov, use_container_width=True)

    with c_m2:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                    border-radius:14px;padding:20px;height:100%;">
          <b style="color:#fff;font-family:'Orbitron',sans-serif;font-size:0.85rem;">
            ACTIVE SATELLITE CONSTELLATION TIMELINE
          </b>
          <div style="height:12px;"></div>
          <table style="width:100%;font-size:0.8rem;color:rgba(255,255,255,0.8);border-collapse:collapse;line-height:2;">
            <tr style="border-bottom:1px solid rgba(255,255,255,0.1);color:rgba(255,255,255,0.5);">
              <th>Satellite</th><th>Sensor</th><th>Operational</th><th>Equator Pass</th>
            </tr>
            <tr><td><b>Terra</b></td><td>MODIS (1 km)</td><td>2000–Present</td><td>10:30 AM / PM</td></tr>
            <tr><td><b>Aqua</b></td><td>MODIS (1 km)</td><td>2002–Present</td><td>01:30 PM / AM</td></tr>
            <tr><td><b>Suomi NPP</b></td><td>VIIRS (375 m)</td><td>2012–Present</td><td>01:30 PM / AM</td></tr>
            <tr><td><b>NOAA-20</b></td><td>VIIRS (375 m)</td><td>2018–Present</td><td>01:30 PM / AM</td></tr>
            <tr><td><b>NOAA-21</b></td><td>VIIRS (375 m)</td><td>2023–Present</td><td>01:30 PM / AM</td></tr>
          </table>
          <p style="font-size:0.75rem;color:rgba(255,255,255,0.5);margin-top:14px;">
            *Accounting for observation frequency prevents misinterpreting zero-counts caused by orbital gaps or monsoonal cloud decks.
          </p>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 4: PROTECTED ECOSYSTEMS
# -------------------------------------------------------------
with tab_pa:
    st.markdown(section_header("🌿", "PROTECTED ECOSYSTEM & BIODIVERSITY MONITORING"), unsafe_allow_html=True)
    
    pa_data = analyze_protected_areas()
    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("HOTSPOTS INSIDE RESERVES", f"{pa_data['total_inside_all']:,}", "Direct ecological reserve hits", "#ef4444")}
      {metric_card("HOTSPOTS IN BUFFER ZONES", f"{pa_data['total_buffer_all']:,}", "<= 10 km peripheral buffer", "#f59e0b")}
      {metric_card("MONITORED RESERVES", f"{len(pa_data['reserves'])}", "Mudumalai, Western Ghats, Amazon, etc.", "#10b981")}
    </div>
    """, unsafe_allow_html=True)

    pa_df = pd.DataFrame(pa_data["reserves"])
    st.dataframe(
        pa_df[["name", "region", "category", "inside_hotspots", "buffer_hotspots", "threat_level", "biodiversity_importance"]],
        use_container_width=True
    )

# -------------------------------------------------------------
# TAB 5: ENVIRONMENTAL CONTEXT
# -------------------------------------------------------------
with tab_env:
    st.markdown(section_header("🌡️", "ENVIRONMENTAL CONTEXT & WILDFIRE WEATHER DRIVERS"), unsafe_allow_html=True)
    
    env = get_environmental_context(preset, month=status.get("month", 3) if status else 3)
    
    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("AIR TEMPERATURE", f"{env['temperature_c']} °C", "2m ambient temperature", "#ef4444")}
      {metric_card("RELATIVE HUMIDITY", f"{env['relative_humidity_pct']}%", "Surface atmospheric moisture", "#3b82f6")}
      {metric_card("SURFACE WIND SPEED", f"{env['wind_speed_kmh']} km/h", "Fire spread velocity driver", "#10b981")}
      {metric_card("FUEL DRYNESS INDEX", f"{env['fuel_dryness_index']}/100", "Vegetation moisture deficit", "#f59e0b")}
      {metric_card("FIRE WEATHER DANGER", env['danger_rating'], f"Score: {env['fire_weather_score']}/100", "#ec4899")}
    </div>
    """, unsafe_allow_html=True)

    env_df = pd.DataFrame(env["monthly_series"])
    fig_env = go.Figure()
    fig_env.add_trace(go.Scatter(x=env_df["month"], y=env_df["temperature_c"], name="Temperature (°C)", line=dict(color="#ef4444", width=2)))
    fig_env.add_trace(go.Scatter(x=env_df["month"], y=env_df["relative_humidity_pct"], name="Relative Humidity (%)", line=dict(color="#3b82f6", width=2)))
    fig_env.add_trace(go.Scatter(x=env_df["month"], y=env_df["fuel_dryness_index"], name="Fuel Dryness Index", line=dict(color="#f59e0b", width=3, dash="dot")))
    fig_env.update_layout(
        title="Annual Environmental Regimes (Temperature, Humidity, Fuel Dryness)",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fff"), yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        legend=dict(bgcolor="rgba(0,0,0,0.5)"), margin=dict(l=40, r=20, t=40, b=40), height=340
    )
    st.plotly_chart(fig_env, use_container_width=True)

# -------------------------------------------------------------
# TAB 6: DUAL-REGION COMPARISON
# -------------------------------------------------------------
with tab_compare:
    st.markdown(section_header("⚖️", "SIDE-BY-SIDE REGIONAL COMPARISON"), unsafe_allow_html=True)
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        comp_r1 = st.selectbox("Region 1:", list(PRESET_REGIONS.keys()), index=1, key="comp_r1")
    with col_r2:
        comp_r2 = st.selectbox("Region 2:", list(PRESET_REGIONS.keys()), index=6, key="comp_r2")

    c1_coords = PRESET_REGIONS.get(comp_r1, (-180, -90, 180, 90))
    c2_coords = PRESET_REGIONS.get(comp_r2, (-180, -90, 180, 90))

    if c1_coords and c2_coords:
        s1 = get_current_status(*c1_coords)
        s2 = get_current_status(*c2_coords)

        comp_col1, comp_col2 = st.columns(2)
        with comp_col1:
            st.markdown(f"### {comp_r1}")
            st.markdown(f"""
            <div class="cx-metrics">
              {metric_card("CURRENT HOTSPOTS", f"{s1.get('actual',0):,}", "Active detections")}
              {metric_card("HISTORICAL MEDIAN", f"{s1.get('median',0):,}", "Multi-year baseline")}
              {metric_card("ANOMALY", f"{s1.get('anomaly_pct',0):+.1f}%", s1.get('severity','Normal'))}
            </div>
            """, unsafe_allow_html=True)
        with comp_col2:
            st.markdown(f"### {comp_r2}")
            st.markdown(f"""
            <div class="cx-metrics">
              {metric_card("CURRENT HOTSPOTS", f"{s2.get('actual',0):,}", "Active detections")}
              {metric_card("HISTORICAL MEDIAN", f"{s2.get('median',0):,}", "Multi-year baseline")}
              {metric_card("ANOMALY", f"{s2.get('anomaly_pct',0):+.1f}%", s2.get('severity','Normal'))}
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------------------
# CSV EXPORT SECTION (Challenge Requirement)
# -------------------------------------------------------------
st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
st.markdown(section_header("📥", "DOWNLOAD HARMONIZED HOTSPOT DATASET (CSV)"), unsafe_allow_html=True)

col_dl_btn, col_dl_info = st.columns([1, 2])
with col_dl_btn:
    if st.button("Generate Downloadable CSV", type="primary", use_container_width=True):
        with st.spinner("Extracting filtered harmonized dataset..."):
            csv_bytes = export_hotspots_csv(west, south, east, north)
        clean_name = preset.replace(" ", "_").replace(",", "")[:20]
        st.download_button(
            label="💾 Download Harmonized CSV",
            data=csv_bytes,
            file_name=f"celestial_x_harmonized_{clean_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )
with col_dl_info:
    st.markdown("""
    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                border-radius:12px;padding:16px 20px;font-size:0.82rem;color:rgba(255,255,255,0.7);">
      <b>Challenge Deliverable:</b> Export includes canonical timestamps (ISO8601 UTC), latitude/longitude,
      normalized confidence (0.0–1.0), Fire Radiative Power (MW), derived FRP proxy, satellite source,
      and Uber H3 discrete global grid indexes (Res-7 & Res-8).
    </div>
    """, unsafe_allow_html=True)

st.markdown(footer(), unsafe_allow_html=True)

