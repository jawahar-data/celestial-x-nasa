"""
CELESTIAL X — Tamil Nadu Deep Dive
====================================
Regional fire intelligence for Tamil Nadu, India:
  - Multi-sub-region analysis (State, Mudumalai, Western Ghats, Anamalai)
  - Protected reserve monitoring (tiger reserves, wildlife sanctuaries)
  - Fire season profile for the Southern Deccan / Western Ghats regime
  - Inter-state fire corridor: Mudumalai connecting TN–Karnataka–Kerala
  - Environmental context (temperature, humidity, dryness)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from celestial.styles import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header, metric_card
from celestial.database import init_database
from celestial.calendar import MONTH_NAMES, get_current_status, get_monthly_totals, get_historical_medians
from celestial.season import analyze_fire_season
from celestial.protected_areas import analyze_protected_areas
from celestial.environmental import get_environmental_context

init_database()
st.set_page_config(
    page_title="CELESTIAL X — Tamil Nadu",
    page_icon="🌴", layout="wide",
    initial_sidebar_state="collapsed"
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("TAMIL NADU")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge"><span class="cx-hero-badge-dot"></span>
    TAMIL NADU DEEP DIVE — WESTERN GHATS · MUDUMALAI · ANAMALAI · NILGIRIS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">TAMIL NADU</div>
  <p class="cx-hero-sub-title">Sub-regional fire intelligence for India's biodiversity-rich southern frontier</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# Sub-region definitions
TN_REGIONS = {
    "Tamil Nadu (Full State)":          (76.0, 8.0, 80.5, 13.6),
    "Mudumalai Tiger Reserve":          (76.4, 11.4, 76.9, 11.9),
    "Western Ghats — Tamil Nadu":       (76.2, 8.5, 77.8, 11.8),
    "Anamalai Tiger Reserve":           (76.8, 10.1, 77.4, 10.7),
    "Nilgiri Biosphere Reserve (TN)":   (76.5, 11.0, 77.2, 11.9),
}

# ── Sub-Region Selector ───────────────────────────────────────────────────────
st.markdown(section_header("📍", "SELECT SUB-REGION"), unsafe_allow_html=True)
selected_region = st.selectbox("Sub-Region:", list(TN_REGIONS.keys()), index=0)
w, s, e, n = TN_REGIONS[selected_region]

# ── Status Metrics for All 4 Core Sub-Regions ──────────────────────────────────
st.markdown(section_header("🌡️", "MULTI-SUB-REGION STATUS DASHBOARD"), unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:0.82rem;color:rgba(255,255,255,0.55);margin-bottom:12px;">'
    'Live status for the four primary Tamil Nadu fire monitoring zones. '
    'Comparison uses harmonized MODIS + VIIRS benchmark baseline.</p>',
    unsafe_allow_html=True
)

sub_cols = st.columns(4)
core_subs = [
    ("Tamil Nadu (Full)", (76.0, 8.0, 80.5, 13.6)),
    ("Mudumalai Reserve", (76.4, 11.4, 76.9, 11.9)),
    ("Western Ghats TN",  (76.2, 8.5, 77.8, 11.8)),
    ("Anamalai Reserve",  (76.8, 10.1, 77.4, 10.7)),
]
for col, (name, bounds) in zip(sub_cols, core_subs):
    with col:
        st_data = get_current_status(*bounds)
        if st_data:
            pct = st_data.get("anomaly_pct") or 0.0
            color = "#ef4444" if pct > 30 else ("#f59e0b" if pct > 10 else "#10b981")
            actual_count = st_data.get('actual', 0) or 0
            severity_str = st_data.get('severity', 'Normal')
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);
                        border-radius:14px;padding:18px 14px;text-align:center;">
              <div style="font-size:0.65rem;color:rgba(255,255,255,0.5);letter-spacing:1.5px;
                          text-transform:uppercase;font-family:'Orbitron',sans-serif;margin-bottom:8px;">
                {name}
              </div>
              <div style="font-size:1.6rem;font-weight:800;color:#fff;font-family:'Orbitron',sans-serif;">
                {actual_count:,}
              </div>
              <div style="font-size:0.72rem;color:rgba(255,255,255,0.55);margin:4px 0;">hotspots</div>
              <div style="font-size:1.1rem;font-weight:700;color:{color};">{float(pct):+.1f}% anomaly</div>
              <div style="font-size:0.68rem;color:rgba(255,255,255,0.4);">{severity_str}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**{name}** — data loading...")

# ── Fire Season Profile ────────────────────────────────────────────────────────
st.markdown(section_header("🔥", "FIRE SEASON PROFILE — WESTERN GHATS / SOUTHERN DECCAN REGIME"), unsafe_allow_html=True)

season = analyze_fire_season(*TN_REGIONS["Tamil Nadu (Full State)"])

st.markdown(f"""
<div class="cx-metrics">
  {metric_card("SEASON ONSET", season['onset_month'], "Fire season beginning (10% cumulative burn)", "#60a5fa")}
  {metric_card("PEAK BURN MONTH", season['peak_month'], "Maximum monthly hotspot density", "#ef4444")}
  {metric_card("SEASON CESSATION", season['cessation_month'], "Fire season end (90% cumulative burn)", "#10b981")}
  {metric_card("SEASON DURATION", f"{season['duration_months']} Months", f"~{season['duration_days']} active burning days", "#f59e0b")}
  {metric_card("INTER-ANNUAL SHIFT", f"{season['shift_days']} Days", "Earlier arrival vs 2000 baseline", "#a855f7")}
</div>
""", unsafe_allow_html=True)

prof_df = pd.DataFrame(season["monthly_profile"])
fig_season = go.Figure()
fig_season.add_trace(go.Bar(
    x=prof_df["month_name"], y=prof_df["mean_hotspots"],
    name="Mean Monthly Hotspots",
    marker_color=["#ef4444" if r else "#1e3a5f" for r in prof_df["is_core_season"]],
))
fig_season.add_trace(go.Scatter(
    x=prof_df["month_name"], y=prof_df["cum_pct"],
    name="Cumulative % of Annual Burn", yaxis="y2",
    mode="lines+markers", line=dict(color="#f59e0b", width=3)
))
fig_season.update_layout(
    title="Tamil Nadu Fire Climatology Curve (Western Ghats — Southern Deccan Regime)",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
    yaxis=dict(title="Mean Hotspot Count", gridcolor="rgba(255,255,255,0.06)"),
    yaxis2=dict(title="Cumulative Annual Burn (%)", overlaying="y", side="right", range=[0, 105]),
    legend=dict(bgcolor="rgba(0,0,0,0.5)"),
    margin=dict(l=40, r=40, t=50, b=40), height=380,
)
st.plotly_chart(fig_season, use_container_width=True)

# ── Inter-State Fire Corridor ──────────────────────────────────────────────────
st.markdown(section_header("🔗", "INTER-STATE FIRE CORRIDOR — MUDUMALAI TRI-JUNCTION"), unsafe_allow_html=True)
st.markdown("""
<div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.3);
            border-radius:14px;padding:22px 24px;margin-bottom:16px;">
  <b style="color:#ef4444;font-family:'Orbitron',sans-serif;font-size:0.9rem;">
    ⚠️ HIGH-PRIORITY ECOLOGICAL CORRIDOR MONITORING
  </b>
  <p style="color:rgba(255,255,255,0.75);font-size:0.84rem;margin-top:12px;line-height:1.9;">
    The <b style="color:#fff;">Mudumalai–Bandipur–Wayanad</b> fire corridor is one of India's most ecologically
    sensitive fire-prone zones, connecting Tamil Nadu, Karnataka, and Kerala at the tri-junction of the
    Western Ghats. It forms a continuous forest landscape spanning three states and three tiger reserves:
    <br><br>
    🐘 <b>Mudumalai Tiger Reserve</b> (Tamil Nadu) — Core habitat for Indian elephants, tigers, leopards<br>
    🌿 <b>Bandipur Tiger Reserve</b> (Karnataka) — Shares a 50-km unfenced boundary with Mudumalai<br>
    🌳 <b>Wayanad Wildlife Sanctuary</b> (Kerala) — Completes the tri-state ecological continuum<br>
    <br>
    Fires originating in one reserve can rapidly propagate across state boundaries due to dry grassland
    corridors, seasonal wind patterns, and the absence of natural firebreaks. CELESTIAL X monitors this
    corridor using harmonized MODIS + VIIRS hotspot data with H3 spatial indexing at 375-m resolution.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Protected Area Monitoring ──────────────────────────────────────────────────
st.markdown(section_header("🌿", "PROTECTED RESERVE FIRE MONITORING"), unsafe_allow_html=True)

pa_data = analyze_protected_areas()
tn_reserves = [r for r in pa_data["reserves"] if "Tamil Nadu" in r.get("region", "") or
               "Mudumalai" in r.get("name", "") or "Anamalai" in r.get("name", "") or
               "Nilgiri" in r.get("name", "")]

if tn_reserves:
    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("TN RESERVE HOTSPOTS", f"{sum(r['inside_hotspots'] for r in tn_reserves):,}", "Direct reserve hits", "#ef4444")}
      {metric_card("BUFFER ZONE ALERTS", f"{sum(r['buffer_hotspots'] for r in tn_reserves):,}", "≤10 km peripheral detections", "#f59e0b")}
      {metric_card("MONITORED TN RESERVES", f"{len(tn_reserves)}", "Tiger reserves + sanctuaries", "#10b981")}
    </div>
    """, unsafe_allow_html=True)
    pa_df = pd.DataFrame(tn_reserves)
    if not pa_df.empty:
        st.dataframe(
            pa_df[["name", "category", "inside_hotspots", "buffer_hotspots", "threat_level", "biodiversity_importance"]],
            use_container_width=True
        )
else:
    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("TOTAL RESERVE HOTSPOTS", f"{pa_data['total_inside_all']:,}", "Direct ecological reserve hits", "#ef4444")}
      {metric_card("BUFFER ZONE ALERTS", f"{pa_data['total_buffer_all']:,}", "≤10 km peripheral buffer", "#f59e0b")}
      {metric_card("MONITORED RESERVES", f"{len(pa_data['reserves'])}", "All monitored reserves", "#10b981")}
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(pa_data["reserves"]), use_container_width=True)

# ── Environmental Context ──────────────────────────────────────────────────────
st.markdown(section_header("🌡️", "ENVIRONMENTAL CONTEXT — TAMIL NADU FIRE WEATHER DRIVERS"), unsafe_allow_html=True)
env = get_environmental_context("Tamil Nadu, India")
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
    title="Tamil Nadu Annual Environmental Regimes (Temperature · Humidity · Fuel Dryness)",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#fff"), yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    legend=dict(bgcolor="rgba(0,0,0,0.5)"), margin=dict(l=40, r=20, t=40, b=40), height=340
)
st.plotly_chart(fig_env, use_container_width=True)

# ── Historical Monthly Trends ──────────────────────────────────────────────────
st.markdown(section_header("📊", "HISTORICAL MONTHLY HOTSPOT TRENDS — SELECTED SUB-REGION"), unsafe_allow_html=True)
totals = get_monthly_totals(w, s, e, n)
medians = get_historical_medians(w, s, e, n)

if not totals.empty:
    pivot_yr = totals.pivot_table(index="year", columns="month", values="total", aggfunc="sum").fillna(0)
    pivot_yr.columns = [MONTH_NAMES[m - 1] for m in pivot_yr.columns]

    fig_hist = go.Figure(data=go.Heatmap(
        z=pivot_yr.values,
        x=pivot_yr.columns.tolist(),
        y=[str(y) for y in pivot_yr.index.tolist()],
        colorscale="Inferno",
        colorbar=dict(
            title=dict(text="Hotspots", font=dict(color="#fff", size=11)),
            tickfont=dict(color="#fff", size=10),
        ),
        hovertemplate="<b>Year: %{y} · %{x}</b><br>Hotspots: <b>%{z:,.0f}</b><extra></extra>",
    ))
    fig_hist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=420, font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        xaxis=dict(tickfont=dict(color="#fff", size=11), side="top", showgrid=False),
        yaxis=dict(tickfont=dict(color="#fff", size=11), dtick=1, showgrid=False),
        margin=dict(l=50, r=20, t=50, b=30),
        title=f"Historical Burning Calendar — {selected_region}",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown(footer(), unsafe_allow_html=True)

