"""
CELESTIAL X — Burning Activity Calendar
=========================================
The core NASA challenge deliverable:
A harmonized burning activity calendar combining MODIS and VIIRS
hotspot observations, enabling emergency managers to:
  - Identify seasonal fire patterns
  - Compare current activity to historical medians
  - Detect anomalies and unusual fire years
  - Download filtered hotspot data as CSV
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

from celestial.styles   import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header, metric_card
from celestial.database import init_database
from celestial.calendar import (
    PRESET_REGIONS, MONTH_NAMES,
    get_monthly_totals, get_historical_medians,
    get_anomaly_data, get_heatmap_pivot,
    get_sensor_yearly, get_current_status,
    export_hotspots_csv,
)

init_database()
st.set_page_config(
    page_title="CELESTIAL X · Burning Calendar",
    page_icon="🔥", layout="wide",
    initial_sidebar_state="collapsed",
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("BURNING CALENDAR")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    HARMONIZED FIRE ACTIVITY · MODIS + VIIRS · NASA FIRMS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">BURNING CALENDAR</div>
  <p class="cx-hero-sub-title">Historical Fire Activity · Seasonal Patterns · Anomaly Detection · MODIS–VIIRS Harmonized</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# ── Region selector ───────────────────────────────────────────────────────────
st.markdown(section_header("🌍", "SELECT REGION"), unsafe_allow_html=True)

col_preset, col_gap, col_coords = st.columns([2, 0.1, 3])
with col_preset:
    preset = st.selectbox("Preset Region", list(PRESET_REGIONS.keys()), index=0,
                           label_visibility="collapsed")

coords = PRESET_REGIONS.get(preset)
with col_coords:
    if coords:
        west, south, east, north = coords
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);'
            f'border-radius:12px;padding:12px 20px;font-size:0.82rem;color:rgba(255,255,255,0.7);">'
            f'<b style="color:#fff;">Bounding Box</b> &nbsp;·&nbsp; '
            f'W: {west} &nbsp;S: {south} &nbsp;E: {east} &nbsp;N: {north}</div>',
            unsafe_allow_html=True
        )
    else:
        c1, c2, c3, c4 = st.columns(4)
        west  = c1.number_input("West",  value=-180.0, min_value=-180.0, max_value=180.0, step=0.5)
        south = c2.number_input("South", value=-90.0,  min_value=-90.0,  max_value=90.0,  step=0.5)
        east  = c3.number_input("East",  value=180.0,  min_value=-180.0, max_value=180.0, step=0.5)
        north = c4.number_input("North", value=90.0,   min_value=-90.0,  max_value=90.0,  step=0.5)

# ── Date range for CSV export ─────────────────────────────────────────────────
col_d1, col_d2, col_dl = st.columns([1, 1, 2])
with col_d1:
    start_date = st.date_input("From date (CSV export)", value=date(2020, 1, 1))
with col_d2:
    end_date = st.date_input("To date (CSV export)", value=date.today())

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading historical fire data..."):
    status     = get_current_status(west, south, east, north)
    pivot_abs  = get_heatmap_pivot(west, south, east, north, normalize=False)
    pivot_anom = get_heatmap_pivot(west, south, east, north, normalize=True)
    medians    = get_historical_medians(west, south, east, north)
    totals     = get_monthly_totals(west, south, east, north)
    sensor_yr  = get_sensor_yearly(west, south, east, north)

# ── No data state ─────────────────────────────────────────────────────────────
if pivot_abs.empty:
    st.markdown("""
    <div class="cx-panel" style="text-align:center;padding:80px 40px;">
      <div style="font-size:4rem;margin-bottom:20px;opacity:0.3;">📅</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:0.9rem;color:#fff;letter-spacing:2px;margin-bottom:12px;">
        NO HISTORICAL DATA YET
      </div>
      <p style="color:rgba(255,255,255,0.6);font-size:0.85rem;max-width:500px;margin:0 auto;line-height:1.8;">
        Go to <strong style="color:#fff;">💾 Data</strong> and run the FIRE-FUSE pipeline to ingest
        NASA FIRMS MODIS &amp; VIIRS observations. Once data is available, the burning activity
        calendar will populate automatically.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(footer(), unsafe_allow_html=True)
    st.stop()

# ── Current month status cards ────────────────────────────────────────────────
st.markdown(section_header("📊", "CURRENT FIRE ACTIVITY STATUS"), unsafe_allow_html=True)
if status:
    anom = status.get("anomaly_pct")
    anom_display = f"{'+' if anom and anom > 0 else ''}{anom}%" if anom is not None else "N/A"
    anom_color = "red" if (anom or 0) > 20 else "green" if (anom or 0) < -20 else "amber"
    st.markdown(
        '<div class="cx-metrics">'
        + metric_card("Latest Month", f"{status.get('month_name','')} {status.get('year','')}",
                      "Most recent data", "blue")
        + metric_card("Hotspots Detected", f"{status.get('actual',0):,}",
                      "This month (harmonized)", "orange")
        + metric_card("Historical Median", f"{status.get('median',0):,}" if status.get("median") else "N/A",
                      f"For {status.get('month_name','')}", "purple")
        + metric_card("Anomaly vs Median", anom_display,
                      "Current vs historical", anom_color)
        + metric_card("Years in Baseline", str(status.get("years_in_baseline", 0)),
                      "Historical record depth", "green")
        + "</div>",
        unsafe_allow_html=True
    )

# ── Burning Activity Heatmap Calendar (absolute) ──────────────────────────────
st.markdown(section_header("🗓", "BURNING ACTIVITY CALENDAR  ·  HOTSPOT COUNT"), unsafe_allow_html=True)
st.markdown("""
<p style="font-size:0.82rem;color:rgba(255,255,255,0.6);margin-bottom:16px;">
Each cell = total harmonized hotspots (MODIS + VIIRS) detected in that year and month.
Color intensity indicates fire activity level. Darker = more hotspots detected.
</p>
""", unsafe_allow_html=True)

fig_cal = go.Figure(data=go.Heatmap(
    z=pivot_abs.values,
    x=pivot_abs.columns.tolist(),
    y=pivot_abs.index.tolist(),
    colorscale=[
        [0.00, "#0a0a1a"],
        [0.15, "#1a1a3a"],
        [0.30, "#3d1a00"],
        [0.50, "#8b3a00"],
        [0.70, "#cc5500"],
        [0.85, "#ef4444"],
        [1.00, "#ffffff"],
    ],
    colorbar=dict(
        title="Hotspots",
        titlefont=dict(color="rgba(255,255,255,0.7)", size=11),
        tickfont=dict(color="rgba(255,255,255,0.7)", size=10),
        thickness=12,
    ),
    hoverongaps=False,
    hovertemplate=(
        "<b>%{y} — %{x}</b><br>"
        "Hotspots: <b>%{z:,}</b><br>"
        "<extra></extra>"
    ),
    xgap=2, ygap=2,
))
fig_cal.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=max(300, len(pivot_abs) * 28 + 80),
    font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
    xaxis=dict(side="top", tickfont=dict(size=11, color="#fff"),
               showgrid=False, zeroline=False),
    yaxis=dict(tickfont=dict(size=11, color="#fff"),
               showgrid=False, zeroline=False, autorange="reversed"),
    margin=dict(l=60, r=40, t=60, b=20),
)
st.plotly_chart(fig_cal, use_container_width=True)

# ── Anomaly Calendar (current vs historical median) ───────────────────────────
st.markdown(section_header("⚡", "ANOMALY CALENDAR  ·  vs. HISTORICAL MEDIAN"), unsafe_allow_html=True)
st.markdown("""
<p style="font-size:0.82rem;color:rgba(255,255,255,0.6);margin-bottom:16px;">
Anomaly (%) = (Observed − Historical Median) ÷ Historical Median × 100.
<span style="color:#ef4444;">Red</span> = above normal &nbsp;|&nbsp;
<span style="color:#3b82f6;">Blue</span> = below normal &nbsp;|&nbsp;
<span style="color:rgba(255,255,255,0.4);">White</span> = near normal.
</p>
""", unsafe_allow_html=True)

if not pivot_anom.empty:
    max_abs = float(max(abs(pivot_anom.values[~np.isnan(pivot_anom.values)].max()),
                        abs(pivot_anom.values[~np.isnan(pivot_anom.values)].min())) or 100)
    fig_anom = go.Figure(data=go.Heatmap(
        z=pivot_anom.values,
        x=pivot_anom.columns.tolist(),
        y=pivot_anom.index.tolist(),
        zmid=0,
        zmin=-max_abs, zmax=max_abs,
        colorscale=[
            [0.00, "#1e3a8a"],
            [0.25, "#3b82f6"],
            [0.45, "#dbeafe"],
            [0.50, "#f8fafc"],
            [0.55, "#fef3c7"],
            [0.75, "#ef4444"],
            [1.00, "#7f1d1d"],
        ],
        colorbar=dict(
            title="Anomaly %",
            titlefont=dict(color="rgba(255,255,255,0.7)", size=11),
            tickfont=dict(color="rgba(255,255,255,0.7)", size=10),
            thickness=12,
        ),
        hoverongaps=False,
        hovertemplate=(
            "<b>%{y} — %{x}</b><br>"
            "Anomaly: <b>%{z:.1f}%</b><br>"
            "<extra></extra>"
        ),
        xgap=2, ygap=2,
    ))
    fig_anom.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(300, len(pivot_anom) * 28 + 80),
        font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        xaxis=dict(side="top", tickfont=dict(size=11, color="#fff"),
                   showgrid=False, zeroline=False),
        yaxis=dict(tickfont=dict(size=11, color="#fff"),
                   showgrid=False, zeroline=False, autorange="reversed"),
        margin=dict(l=60, r=40, t=60, b=20),
    )
    st.plotly_chart(fig_anom, use_container_width=True)

# ── Monthly seasonal profile (current vs median) ──────────────────────────────
st.markdown(section_header("📈", "SEASONAL FIRE PROFILE  ·  CURRENT YEAR vs HISTORICAL"), unsafe_allow_html=True)
if not totals.empty and not medians.empty:
    current_year = int(totals["year"].max())
    current = totals[totals["year"] == current_year].set_index("month")["total"].reindex(range(1,13), fill_value=0)

    fig_season = go.Figure()
    # Historical range (min-max band)
    if "min_count" in medians.columns and "max_count" in medians.columns:
        fig_season.add_trace(go.Scatter(
            x=MONTH_NAMES + MONTH_NAMES[::-1],
            y=list(medians["max_count"]) + list(medians["min_count"])[::-1],
            fill="toself", fillcolor="rgba(59,130,246,0.1)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Historical Range", showlegend=True,
        ))
    # Historical median
    fig_season.add_trace(go.Scatter(
        x=MONTH_NAMES, y=medians["median_count"],
        line=dict(color="#3b82f6", width=2, dash="dash"),
        mode="lines+markers", marker=dict(size=5),
        name="Historical Median",
    ))
    # Current year
    fig_season.add_trace(go.Scatter(
        x=MONTH_NAMES, y=current.values,
        line=dict(color="#ef4444", width=3),
        mode="lines+markers", marker=dict(size=7),
        name=f"{current_year} (Current)",
    ))
    fig_season.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        height=360,
        font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        legend=dict(bgcolor="rgba(0,0,0,0.4)", bordercolor="rgba(255,255,255,0.1)",
                    borderwidth=1, font=dict(size=11)),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(color="#fff")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(color="#fff"), title="Hotspots",
                   titlefont=dict(color="rgba(255,255,255,0.6)")),
        margin=dict(l=60, r=20, t=20, b=40),
    )
    st.plotly_chart(fig_season, use_container_width=True)

# ── Yearly trend ──────────────────────────────────────────────────────────────
st.markdown(section_header("📉", "YEARLY HOTSPOT TREND"), unsafe_allow_html=True)
if not totals.empty:
    yearly = totals.groupby("year")["total"].sum().reset_index()
    fig_yr = go.Figure()
    fig_yr.add_trace(go.Bar(
        x=yearly["year"], y=yearly["total"],
        marker=dict(
            color=yearly["total"],
            colorscale=[[0,"#1a3a1a"],[0.5,"#ea580c"],[1,"#dc2626"]],
            showscale=False,
        ),
        hovertemplate="<b>%{x}</b><br>Hotspots: <b>%{y:,}</b><extra></extra>",
        name="Yearly Total",
    ))
    # Trend line
    if len(yearly) > 2:
        z = np.polyfit(yearly["year"], yearly["total"], 1)
        p = np.poly1d(z)
        fig_yr.add_trace(go.Scatter(
            x=yearly["year"], y=p(yearly["year"]),
            mode="lines", line=dict(color="#a78bfa", width=2, dash="dot"),
            name="Trend",
        ))
    fig_yr.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        height=320,
        font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        legend=dict(bgcolor="rgba(0,0,0,0.4)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
        xaxis=dict(showgrid=False, tickfont=dict(color="#fff")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(color="#fff"), title="Total Hotspots"),
        margin=dict(l=60, r=20, t=20, b=40),
        bargap=0.2,
    )
    st.plotly_chart(fig_yr, use_container_width=True)

# ── Sensor comparison (MODIS vs VIIRS) ───────────────────────────────────────
st.markdown(section_header("🛰", "SENSOR COMPARISON  ·  MODIS vs VIIRS"), unsafe_allow_html=True)
st.markdown("""
<p style="font-size:0.82rem;color:rgba(255,255,255,0.6);margin-bottom:12px;">
<b style="color:#fff;">Why harmonization matters:</b> MODIS (1 km, since ~2000) and VIIRS (375 m, since ~2012)
have different spatial resolutions and sensitivities. Direct comparison without harmonization is scientifically
invalid. CELESTIAL X FIRE-FUSE normalizes both into a consistent schema before analysis.
</p>
""", unsafe_allow_html=True)
if not sensor_yr.empty:
    modis = sensor_yr[sensor_yr["satellite_group"]=="MODIS"]
    viirs = sensor_yr[sensor_yr["satellite_group"]=="VIIRS"]
    fig_sensor = go.Figure()
    fig_sensor.add_trace(go.Bar(
        x=modis["year"], y=modis["hotspot_count"],
        name="MODIS (1 km)", marker_color="#ef4444",
        hovertemplate="<b>MODIS %{x}</b><br>Hotspots: %{y:,}<extra></extra>",
    ))
    fig_sensor.add_trace(go.Bar(
        x=viirs["year"], y=viirs["hotspot_count"],
        name="VIIRS (375 m)", marker_color="#eab308",
        hovertemplate="<b>VIIRS %{x}</b><br>Hotspots: %{y:,}<extra></extra>",
    ))
    fig_sensor.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        barmode="group", height=320,
        font=dict(color="rgba(255,255,255,0.8)", family="Inter"),
        legend=dict(bgcolor="rgba(0,0,0,0.4)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
        xaxis=dict(showgrid=False, tickfont=dict(color="#fff")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(color="#fff"), title="Raw Hotspot Count"),
        margin=dict(l=60, r=20, t=20, b=40),
        bargap=0.1, bargroupgap=0.05,
    )
    st.plotly_chart(fig_sensor, use_container_width=True)
    st.markdown(
        '<p style="font-size:0.75rem;color:rgba(255,255,255,0.4);text-align:center;">'
        'Raw counts shown above — <b style="color:rgba(255,255,255,0.6);">not directly comparable</b> between sensors without harmonization. '
        'FIRE-FUSE normalizes spatial resolution, confidence, and temporal alignment.</p>',
        unsafe_allow_html=True
    )

# ── Historical median table ────────────────────────────────────────────────────
st.markdown(section_header("📋", "HISTORICAL MEDIAN TABLE"), unsafe_allow_html=True)
if not medians.empty:
    display = medians.copy()
    display["month"] = display["month"].apply(lambda m: MONTH_NAMES[m-1])
    display = display.rename(columns={
        "month":"Month","median_count":"Median","mean_count":"Mean",
        "std_count":"Std Dev","min_count":"Min","max_count":"Max","year_count":"Years"
    })
    for col in ["Median","Mean","Std Dev","Min","Max"]:
        display[col] = display[col].round(0).astype("Int64")
    st.dataframe(display.set_index("Month"), use_container_width=True)

# ── CSV Download ──────────────────────────────────────────────────────────────
st.markdown(section_header("⬇", "DOWNLOAD HOTSPOT DATA"), unsafe_allow_html=True)
st.markdown("""
<p style="font-size:0.82rem;color:rgba(255,255,255,0.6);margin-bottom:16px;">
Download harmonized MODIS + VIIRS hotspot observations for the selected region and date range
as a CSV file. Maximum 100,000 records per download.
</p>
""", unsafe_allow_html=True)

col_csv, col_info = st.columns([1, 2])
with col_csv:
    if st.button("Generate CSV Download", use_container_width=True, type="primary"):
        with st.spinner("Preparing CSV..."):
            csv_bytes = export_hotspots_csv(
                west, south, east, north,
                str(start_date), str(end_date)
            )
        region_label = preset.replace(" ","_").replace(",","").replace("/","_")[:20]
        filename = f"celestialx_hotspots_{region_label}_{start_date}_{end_date}.csv"
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
        )
with col_info:
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
        f'border-radius:12px;padding:16px 20px;font-size:0.82rem;color:rgba(255,255,255,0.6);">'
        f'<b style="color:#fff;">Export includes:</b> Satellite, Lat/Lon, Date, Time, Confidence, FRP (MW), '
        f'Brightness Temperature, Day/Night flag<br><br>'
        f'<b style="color:#fff;">Region:</b> {preset}<br>'
        f'<b style="color:#fff;">Date range:</b> {start_date} → {end_date}'
        f'</div>',
        unsafe_allow_html=True
    )

st.markdown(footer(), unsafe_allow_html=True)
