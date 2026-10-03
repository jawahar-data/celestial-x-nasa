"""
CELESTIAL X — Live Map Page
Premium satellite-view interactive map with all data layers.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pydeck as pdk
import h3

from celestial.styles    import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header, DECK_TOOLTIP
from celestial.database  import init_database
from celestial.harmonizer import get_harmonized_dataframe
from celestial.fire_fuse  import get_events_dataframe, get_event_h3_cells
from celestial.risk       import get_risk_map_data, RISK_COLOR_MAP

init_database()
st.set_page_config(
    page_title="CELESTIAL X · Live Map",
    page_icon="🗺", layout="wide",
    initial_sidebar_state="collapsed",
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("LIVE MAP")

# ── Premium page header ────────────────────────────────────────────────────────
st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    LIVE SATELLITE INTELLIGENCE &nbsp;·&nbsp; NASA FIRMS NRT
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">SATELLITE MAP</div>
  <p class="cx-hero-sub-title">MODIS &amp; VIIRS Fire Observations · H3 Grid · Event Centroids · Risk Indicators</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# ── Layer controls ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin:16px 0 4px;">
  <span style="font-family:'Orbitron',sans-serif;font-size:0.54rem;font-weight:700;
               text-transform:uppercase;letter-spacing:2.5px;color: #ffffff;">
    MAP LAYERS &amp; CONTROLS
  </span>
</div>
""", unsafe_allow_html=True)

with st.container(border=True):
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1,1,1,1,1,1,1,1.8])
    with c1: show_modis  = st.checkbox("🔴 MODIS",        value=True)
    with c2: show_viirs  = st.checkbox("🟡 VIIRS",        value=True)
    with c3: show_active = st.checkbox("🔥 Active Events", value=True)
    with c4: show_closed = st.checkbox("⬛ Closed",       value=False)
    with c5: show_risk   = st.checkbox("⚠ Risk",          value=True)
    with c6: show_h3     = st.checkbox("⬡ H3 Grid",       value=False)
    with c7: show_3d     = st.checkbox("🏛 3D Columns",   value=True)
    with c8:
        map_style_label = st.selectbox("Basemap", [
            "🛰 Satellite", "🛰 Satellite Streets", "🌑 Dark", "☀ Light"
        ], index=0, label_visibility="collapsed")

MAP_STYLES = {
    "🛰 Satellite":          "mapbox://styles/mapbox/satellite-v9",
    "🛰 Satellite Streets":  "mapbox://styles/mapbox/satellite-streets-v12",
    "🌑 Dark":               "mapbox://styles/mapbox/dark-v11",
    "☀ Light":               "mapbox://styles/mapbox/light-v11",
}
SELECTED_MAP = MAP_STYLES.get(map_style_label, "mapbox://styles/mapbox/satellite-v9")

# ── Load data ─────────────────────────────────────────────────────────────────
harm_df   = get_harmonized_dataframe(limit=10000)
events_df = get_events_dataframe()
risk_df   = get_risk_map_data()

layers = []

# ── MODIS scatterplot ──────────────────────────────────────────────────────────
if show_modis and not harm_df.empty:
    modis = harm_df[harm_df["satellite"] == "MODIS"].copy()
    if not modis.empty:
        modis["radius"] = modis["frp"].fillna(0).apply(
            lambda f: max(4000, min(35000, (max(f,1) ** 0.55) * 3800))
        )
        layers.append(pdk.Layer(
            "ScatterplotLayer", data=modis,
            get_position="[longitude, latitude]",
            get_radius="radius",
            get_fill_color=[255, 80, 60, 190],
            pickable=True, stroked=True,
            get_line_color=[255, 140, 100, 100],
            line_width_min_pixels=1,
            id="modis_scatter",
        ))

# ── VIIRS scatterplot ──────────────────────────────────────────────────────────
if show_viirs and not harm_df.empty:
    viirs = harm_df[harm_df["satellite"].str.contains("VIIRS", na=False)].copy()
    if not viirs.empty:
        viirs["radius"] = viirs["frp"].fillna(0).apply(
            lambda f: max(2500, min(22000, (max(f,1) ** 0.55) * 2400))
        )
        layers.append(pdk.Layer(
            "ScatterplotLayer", data=viirs,
            get_position="[longitude, latitude]",
            get_radius="radius",
            get_fill_color=[255, 210, 60, 185],
            pickable=True, stroked=True,
            get_line_color=[255, 240, 100, 100],
            line_width_min_pixels=1,
            id="viirs_scatter",
        ))

# ── 3D Column layer (harmonised events) ────────────────────────────────────────
if show_3d and not risk_df.empty:
    col_df = risk_df.copy()
    max_frp = col_df["peak_frp"].max() or 1.0
    col_df["elevation"] = col_df["peak_frp"].fillna(0).apply(
        lambda f: max(5000, (f / max_frp) * 180_000)
    )
    col_df["color"] = col_df["risk_level"].apply(
        lambda x: RISK_COLOR_MAP.get(x, [100,100,100,180])
    )
    layers.append(pdk.Layer(
        "ColumnLayer", data=col_df,
        get_position="[longitude, latitude]",
        get_elevation="elevation",
        elevation_scale=1,
        radius=6000,
        get_fill_color="color",
        pickable=True,
        extruded=True,
        coverage=0.85,
        id="event_columns",
    ))

# ── Active event centroids (risk-colored halos) ────────────────────────────────
if show_active and not risk_df.empty:
    active = risk_df[risk_df["status"].isin(
        ["ACTIVE","EXPANDING","PERSISTENT","DETECTED"]
    )].copy()
    if not active.empty:
        active["color"]  = active["risk_level"].apply(
            lambda x: RISK_COLOR_MAP.get(x, RISK_COLOR_MAP[None])
        )
        active["radius"] = active["observation_count"].fillna(1).apply(
            lambda n: max(18000, min(120000, n * 4500))
        )
        layers.append(pdk.Layer(
            "ScatterplotLayer", data=active,
            get_position="[longitude, latitude]",
            get_radius="radius",
            get_fill_color="color",
            pickable=True, stroked=True,
            get_line_color=[255,255,255,50],
            line_width_min_pixels=2,
            id="active_halos",
        ))

# ── Closed events ─────────────────────────────────────────────────────────────
if show_closed and not risk_df.empty:
    closed = risk_df[risk_df["status"] == "CLOSED"].copy()
    if not closed.empty:
        closed["radius"] = closed["observation_count"].fillna(1).apply(
            lambda n: max(12000, n * 2500)
        )
        layers.append(pdk.Layer(
            "ScatterplotLayer", data=closed,
            get_position="[longitude, latitude]",
            get_radius="radius",
            get_fill_color=[60, 60, 80, 120],
            pickable=True,
            id="closed_events",
        ))

# ── H3 hexagon grid ────────────────────────────────────────────────────────────
if show_h3 and not events_df.empty:
    h3_features = []
    for _, ev in events_df.head(20).iterrows():
        cells = get_event_h3_cells(ev["event_id"])
        for cell in cells[:40]:
            try:
                boundary = h3.cell_to_boundary(cell)
                coords   = [[p[1], p[0]] for p in boundary]
                coords.append(coords[0])
                h3_features.append({
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [coords]},
                    "properties": {"event_id": ev["event_id"]},
                })
            except Exception:
                continue
    if h3_features:
        layers.append(pdk.Layer(
            "GeoJsonLayer",
            data={"type": "FeatureCollection", "features": h3_features},
            get_fill_color=[120, 60, 255, 30],
            get_line_color=[160, 100, 255, 200],
            line_width_min_pixels=1,
            pickable=True,
            id="h3_grid",
        ))

# ── Compute view state ─────────────────────────────────────────────────────────
if not risk_df.empty and len(risk_df) > 0:
    clat, clon = float(risk_df["latitude"].mean()), float(risk_df["longitude"].mean())
elif not harm_df.empty:
    clat, clon = float(harm_df["latitude"].mean()), float(harm_df["longitude"].mean())
else:
    clat, clon = 20.0, 78.0

view = pdk.ViewState(
    latitude=clat, longitude=clon,
    zoom=4, pitch=50, bearing=-10,
)

# ── Render map ─────────────────────────────────────────────────────────────────
if not layers:
    st.markdown("""
    <div class="cx-panel" style="text-align:center;padding:80px 40px;margin-top:20px;">
      <div style="font-size:4rem;margin-bottom:20px;opacity:0.4;">🗺</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:1.1rem;color: #ffffff;
                  margin-bottom:12px;letter-spacing:2px;">NO DATA TO DISPLAY</div>
      <p style="color: #ffffff;font-size:0.82rem;max-width:400px;margin:0 auto;line-height:1.8;">
        Go to the <strong>💾 Data</strong> page and run the FIRE-FUSE pipeline to ingest satellite observations.
      </p>
    </div>
    """, unsafe_allow_html=True)
else:
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style=SELECTED_MAP,
        tooltip={
            "html": (
                "<div style='font-family:Orbitron,sans-serif;font-size:11px;font-weight:700;"
                "color:#fff;margin-bottom:6px;'>{satellite}{event_id}</div>"
                "<div style='font-size:11px;color: #ffffff;line-height:1.8;'>"
                "Lat: {latitude} &nbsp;|&nbsp; Lon: {longitude}<br/>"
                "FRP: <b>{frp} MW</b><br/>"
                "Status: {status}<br/>"
                "Risk: <b>{risk_level}</b><br/>"
                "Observations: {observation_count}"
                "</div>"
            ),
            "style": DECK_TOOLTIP,
        },
    )
    # Wrapped in a premium card container
    st.markdown('<div style="border-radius:20px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);box-shadow:0 20px 80px rgba(0,0,0,0.8);margin-top:16px;">', unsafe_allow_html=True)
    st.pydeck_chart(deck, use_container_width=True, height=600)
    st.markdown('</div>', unsafe_allow_html=True)

    # Legend
    st.markdown("""
    <div style="display:flex;gap:24px;justify-content:center;padding:14px 0 0;flex-wrap:wrap;">
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color: #ffffff;">
        🔴 MODIS 1km &nbsp;|&nbsp; 🟡 VIIRS 375m &nbsp;|&nbsp;
        🔴 Very High Risk &nbsp;|&nbsp; 🟠 High &nbsp;|&nbsp; 🟡 Moderate &nbsp;|&nbsp; 🟢 Low &nbsp;|&nbsp;
        ⬡ H3 Res-7 &nbsp;|&nbsp; 🏛 3D = Peak FRP
      </span>
    </div>
    """, unsafe_allow_html=True)

# ── Stats row ─────────────────────────────────────────────────────────────────
if not harm_df.empty or not risk_df.empty:
    st.markdown(section_header("📊", "MAP DATA SUMMARY"), unsafe_allow_html=True)
    from celestial.styles import metric_card
    n_modis  = len(harm_df[harm_df["satellite"]=="MODIS"])                                   if not harm_df.empty else 0
    n_viirs  = len(harm_df[harm_df["satellite"].str.contains("VIIRS",na=False)])             if not harm_df.empty else 0
    n_active = len(risk_df[risk_df["status"].isin(["ACTIVE","EXPANDING","PERSISTENT"])]) if not risk_df.empty else 0
    n_total  = len(risk_df)                                                                  if not risk_df.empty else 0

    st.markdown(
        '<div class="cx-metrics" style="grid-template-columns:repeat(4,1fr);">'
        + metric_card("MODIS Obs",     f"{n_modis:,}",  "Shown on map", "red")
        + metric_card("VIIRS Obs",     f"{n_viirs:,}",  "Shown on map", "amber")
        + metric_card("Active Events", f"{n_active:,}", "Tracked events","orange")
        + metric_card("Total Events",  f"{n_total:,}",  "All statuses",  "blue")
        + "</div>",
        unsafe_allow_html=True,
    )

st.markdown(footer(), unsafe_allow_html=True)
