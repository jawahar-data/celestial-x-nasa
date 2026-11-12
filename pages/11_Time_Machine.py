"""
CELESTIAL X — Historical Fire Time Machine
===========================================
Interactive timeline slider from 2001 to present.
Drag the slider to watch the burning activity calendar
update live for the selected year and month.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from celestial.styles import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header, metric_card
from celestial.database import init_database
from celestial.calendar import PRESET_REGIONS, MONTH_NAMES, get_monthly_totals, get_historical_medians, get_heatmap_pivot

init_database()
st.set_page_config(
    page_title="CELESTIAL X — Time Machine",
    page_icon="🕰️", layout="wide",
    initial_sidebar_state="collapsed"
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("TIME MACHINE")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge"><span class="cx-hero-badge-dot"></span>
    HISTORICAL FIRE TIME MACHINE — 2001 TO PRESENT — MODIS + VIIRS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">TIME MACHINE</div>
  <p class="cx-hero-sub-title">Drag the timeline slider to travel through 20+ years of satellite fire history</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# Region selector
st.markdown(section_header("📍", "SELECT MONITORED REGION"), unsafe_allow_html=True)
preset_opts = [k for k, v in PRESET_REGIONS.items() if v is not None]
preset = st.selectbox("Region:", preset_opts, index=1)
coords = PRESET_REGIONS.get(preset, (-180, -90, 180, 90))
west, south, east, north = coords

# Timeline slider
st.markdown(section_header("🕰️", "TRAVEL THROUGH TIME — SELECT YEAR"), unsafe_allow_html=True)
current_year = datetime.now().year
selected_year = st.slider(
    "Select Year:",
    min_value=2001, max_value=current_year, value=2021, step=1,
    help="Move the slider to travel through the multi-decade satellite fire record"
)

# Load data
with st.spinner(f"Loading {selected_year} fire activity for {preset}..."):
    totals = get_monthly_totals(west, south, east, north)
    medians = get_historical_medians(west, south, east, north)

# Year's monthly profile
if not totals.empty:
    yr_data = totals[totals["year"] == selected_year].copy()
    if yr_data.empty:
        # Show nearest available year
        closest = totals["year"].sub(selected_year).abs().idxmin()
        yr_data = totals[totals["year"] == totals.loc[closest, "year"]].copy()

    yr_data = yr_data.sort_values("month")
    yr_data["month_name"] = yr_data["month"].apply(lambda m: MONTH_NAMES[m - 1])

    # Merge with medians for comparison
    if not medians.empty:
        yr_data = yr_data.merge(medians[["month", "median_count"]], on="month", how="left")
        yr_data["anomaly_pct"] = (
            (yr_data["total"] - yr_data["median_count"])
            / yr_data["median_count"].replace(0, np.nan) * 100
        ).round(1)

    total_yr = int(yr_data["total"].sum())
    if not yr_data.empty and yr_data["total"].max() > 0:
        peak_month_row = yr_data.loc[yr_data["total"].idxmax()]
        peak_month = MONTH_NAMES[int(peak_month_row["month"]) - 1]
        peak_val = int(peak_month_row["total"])
    else:
        peak_month, peak_val = "N/A", 0

    baseline_yr = int(medians["median_count"].sum()) if not medians.empty else 0
    yr_anom = round((total_yr - baseline_yr) / max(baseline_yr, 1) * 100, 1) if baseline_yr > 0 else 0
    color = "#ef4444" if yr_anom > 20 else ("#f59e0b" if yr_anom > 0 else "#10b981")

    st.markdown(f"""
    <div class="cx-metrics">
      {metric_card("SELECTED YEAR", str(selected_year), "Historical fire record")}
      {metric_card("ANNUAL HOTSPOTS", f"{total_yr:,}", "Harmonized MODIS + VIIRS")}
      {metric_card("PEAK MONTH", peak_month, f"{peak_val:,} hotspots at peak")}
      {metric_card("VS. HISTORICAL MEDIAN", f"{yr_anom:+.1f}%", "Annual anomaly", color)}
    </div>
    """, unsafe_allow_html=True)

    # Monthly bar chart vs historical median
    st.markdown(
        section_header("📊", f"MONTHLY FIRE ACTIVITY — {selected_year} vs HISTORICAL MEDIAN"),
        unsafe_allow_html=True
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yr_data["month_name"],
        y=yr_data["total"],
        name=f"{selected_year} Hotspots",
        marker_color="#ef4444",
        hovertemplate="<b>%{x} " + str(selected_year) + "</b><br>Hotspots: <b>%{y:,}</b><extra></extra>",
    ))
    if "median_count" in yr_data.columns:
        fig.add_trace(go.Scatter(
            x=yr_data["month_name"],
            y=yr_data["median_count"],
            name="Historical Median",
            mode="lines+markers",
            line=dict(color="#60a5fa", width=3, dash="dash"),
            marker=dict(size=8),
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=380, font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        legend=dict(bgcolor="rgba(0,0,0,0.5)"),
        xaxis=dict(showgrid=False, tickfont=dict(color="#fff")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Hotspot Count"),
        margin=dict(l=40, r=20, t=20, b=40),
        barmode="group",
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No fire activity data available for the selected region. Using demo data.")

# Full multi-decade heatmap
st.markdown(
    section_header("📅", f"FULL MULTI-DECADE RECORD — {selected_year} HIGHLIGHTED"),
    unsafe_allow_html=True
)
pivot = get_heatmap_pivot(west, south, east, north, mode="total")
if not pivot.empty:
    fig_hm = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=[str(y) for y in pivot.index.tolist()],
        colorscale="Inferno",
        colorbar=dict(
            title=dict(text="Hotspots", font=dict(color="#fff", size=11)),
            tickfont=dict(color="#fff", size=10),
        ),
        hovertemplate="<b>Year: %{y} · %{x}</b><br>Hotspots: <b>%{z:,.0f}</b><extra></extra>",
    ))
    # Highlight selected year with a shape overlay
    year_labels = [str(y) for y in pivot.index.tolist()]
    if str(selected_year) in year_labels:
        fig_hm.add_shape(
            type="rect",
            xref="paper", x0=0, x1=1,
            yref="y", y0=str(selected_year), y1=str(selected_year),
            line=dict(color="#60a5fa", width=4),
        )
    fig_hm.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=500, font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        xaxis=dict(tickfont=dict(color="#fff", size=11), side="top", showgrid=False),
        yaxis=dict(tickfont=dict(color="#fff", size=11), dtick=1, showgrid=False),
        margin=dict(l=50, r=20, t=50, b=30),
    )
    st.plotly_chart(fig_hm, use_container_width=True)
    st.markdown(
        f'<p style="font-size:0.78rem;color:rgba(255,255,255,0.5);margin-top:-8px;">'
        f'🕰️ Selected year <b style="color:#60a5fa">{selected_year}</b> is highlighted. '
        f'Blue line marks the row. Demo data shown when live DB is empty.</p>',
        unsafe_allow_html=True
    )

st.markdown(footer(), unsafe_allow_html=True)

