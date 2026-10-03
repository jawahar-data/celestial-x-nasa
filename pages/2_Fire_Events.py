"""
CELESTIAL X — Fire Events Page (Premium)
Persistent multi-day fire event registry with detail inspector.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pydeck as pdk

from celestial.styles    import (ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer,
                                  section_header, metric_card, DECK_TOOLTIP)
from celestial.database  import init_database
from celestial.fire_fuse  import (get_events_dataframe, get_event_timeline,
                                   get_event_observations, get_event_h3_cells)
from celestial.risk       import compute_risk_score, RISK_COLOR_MAP
from celestial.reports    import generate_event_report, get_report_content

init_database()
st.set_page_config(
    page_title="CELESTIAL X · Fire Events",
    page_icon="🔥", layout="wide",
    initial_sidebar_state="collapsed",
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("FIRE EVENTS")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    PERSISTENT FIRE EVENT REGISTRY &nbsp;·&nbsp; CELESTIAL X FIRE-FUSE
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">FIRE EVENTS</div>
  <p class="cx-hero-sub-title">Multi-Day Spatiotemporal Reconciliation · Lifecycle Tracking · Automated Reports</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# ── Load events ───────────────────────────────────────────────────────────────
all_events = get_events_dataframe()

if all_events.empty:
    st.markdown("""
    <div class="cx-panel" style="text-align:center;padding:80px 40px;margin-top:24px;">
      <div style="font-size:4rem;margin-bottom:20px;opacity:0.35;">🔥</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:1rem;color: #ffffff;
                  margin-bottom:12px;letter-spacing:2px;">NO FIRE EVENTS IN DATABASE</div>
      <p style="color: #ffffff;font-size:0.82rem;max-width:440px;margin:0 auto;line-height:1.8;">
        Run the <strong>CELESTIAL X FIRE-FUSE</strong> pipeline from the
        <strong>💾 Data</strong> page to begin tracking persistent multi-day fire events.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(footer(), unsafe_allow_html=True)
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.container(border=True):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        status_filter = st.multiselect(
            "Status", ["DETECTED","ACTIVE","PERSISTENT","EXPANDING","DECLINING","CLOSED"],
            default=["DETECTED","ACTIVE","PERSISTENT","EXPANDING","DECLINING"],
        )
    with fc2:
        risk_filter = st.multiselect(
            "Risk Level", ["VERY HIGH","HIGH","MODERATE","LOW"], default=[]
        )
    with fc3:
        sort_by = st.selectbox(
            "Sort by", ["last_observed_time","peak_frp","observation_count","start_time"],
            index=0,
        )

if status_filter:
    all_events = all_events[all_events["status"].isin(status_filter)]
if risk_filter:
    all_events = all_events[all_events["risk_level"].isin(risk_filter)]
if sort_by in all_events.columns:
    all_events = all_events.sort_values(sort_by, ascending=False)

# ── Event table ───────────────────────────────────────────────────────────────
st.markdown(section_header("🔥", f"FIRE EVENTS  ·  {len(all_events)} RESULTS"), unsafe_allow_html=True)

display_cols = [c for c in [
    "event_id","status","risk_level","start_time","last_observed_time",
    "duration_hours","observation_count","modis_count","viirs_count",
    "peak_frp","mean_frp","h3_cell_count","centroid_lat","centroid_lon",
] if c in all_events.columns]

st.dataframe(
    all_events[display_cols].rename(columns={
        "event_id":"Event ID", "status":"Status", "risk_level":"Risk",
        "start_time":"Start", "last_observed_time":"Last Observed",
        "duration_hours":"Duration (hrs)", "observation_count":"Obs",
        "modis_count":"MODIS", "viirs_count":"VIIRS",
        "peak_frp":"Peak FRP (MW)", "mean_frp":"Mean FRP (MW)",
        "h3_cell_count":"H3 Cells", "centroid_lat":"Lat", "centroid_lon":"Lon",
    }).head(50),
    use_container_width=True, hide_index=True, height=300,
)

# ── Event detail inspector ─────────────────────────────────────────────────────
st.markdown(section_header("🔍", "FIRE EVENT INSPECTOR"), unsafe_allow_html=True)

if all_events.empty:
    st.info("No events match the current filters.")
    st.markdown(footer(), unsafe_allow_html=True)
    st.stop()

event_ids  = all_events["event_id"].tolist()
selected_id = st.selectbox(
    "Select event to inspect",
    event_ids,
    format_func=lambda x: f"{x}",
    label_visibility="collapsed",
)

if selected_id:
    ev = all_events[all_events["event_id"] == selected_id].iloc[0]
    score, level = compute_risk_score(ev.to_dict())

    dur_hrs = ev.get("duration_hours")
    dur_str = f"{int(dur_hrs//24)}d {int(dur_hrs%24)}h" if dur_hrs else "—"
    sat_str = " + ".join(
        [s for s, c in [("MODIS", "modis_count"), ("VIIRS", "viirs_count")]
         if ev.get(c, 0) > 0]
    ) or "—"

    # Status + Risk ribbon
    status_color = {
        "DETECTED":"rgba(59,130,246,0.25)","ACTIVE":"rgba(234,88,12,0.25)",
        "PERSISTENT":"rgba(139,92,246,0.25)","EXPANDING":"rgba(239,68,68,0.25)",
        "DECLINING":"rgba(245,158,11,0.25)","CLOSED":"rgba(75,85,99,0.25)",
    }.get(ev["status"], "rgba(255,255,255,0.08)")
    risk_color = {
        "VERY HIGH":"rgba(239,68,68,0.25)","HIGH":"rgba(234,88,12,0.25)",
        "MODERATE":"rgba(245,158,11,0.25)","LOW":"rgba(34,197,94,0.25)",
    }.get(level, "rgba(255,255,255,0.08)")

    st.markdown(f"""
    <div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;">
      <span style="font-family:'Orbitron',sans-serif;font-size:0.7rem;font-weight:700;
                   letter-spacing:2px;color:#fff;background:{status_color};
                   border:1px solid rgba(255,255,255,0.15);border-radius:100px;
                   padding:5px 16px;">{ev['status']}</span>
      <span style="font-family:'Orbitron',sans-serif;font-size:0.7rem;font-weight:700;
                   letter-spacing:2px;color:#fff;background:{risk_color};
                   border:1px solid rgba(255,255,255,0.15);border-radius:100px;
                   padding:5px 16px;">{level} RISK  ·  {score:.2f}/1.00</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;
                   color: #ffffff;padding:5px 12px;
                   background:rgba(255,255,255,0.04);border-radius:100px;
                   border:1px solid rgba(255,255,255,0.08);">{selected_id}</span>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    st.markdown(
        '<div class="cx-metrics" style="grid-template-columns:repeat(6,1fr);">'
        + metric_card("Duration",     dur_str,                                         f"Start: {str(ev['start_time'])[:10]}",      "blue")
        + metric_card("Peak FRP",     f"{ev.get('peak_frp',0) or 0:.0f} MW",          "Max fire intensity",                         "red")
        + metric_card("Mean FRP",     f"{ev.get('mean_frp',0) or 0:.0f} MW",          "Average observed intensity",                 "orange")
        + metric_card("Observations", str(ev.get("observation_count",0)),               sat_str,                                      "purple")
        + metric_card("H3 Cells",     str(ev.get("h3_cell_count",0)),                  "Spatial footprint (res-7)",                  "amber")
        + metric_card("Risk Score",   f"{score:.3f}",                                   "CELESTIAL-X-RISK-v1",                        "red" if level=="VERY HIGH" else "orange" if level=="HIGH" else "amber" if level=="MODERATE" else "green")
        + "</div>",
        unsafe_allow_html=True,
    )
    # Removed split close div

    # Detail tabs
    t1, t2, t3, t4 = st.tabs(["📅  Timeline", "🗺  Satellite Map", "📊  Analysis", "📋  Report"])

    with t1:
        timeline = get_event_timeline(selected_id)
        if not timeline.empty:
            st.dataframe(
                timeline.rename(columns={
                    "obs_date":"Date","satellite":"Satellite","obs_count":"Observations",
                    "avg_frp":"Avg FRP (MW)","max_frp":"Max FRP (MW)",
                    "avg_confidence":"Confidence","centroid_lat":"Lat","centroid_lon":"Lon",
                }),
                use_container_width=True, hide_index=True,
            )
            frp_chart = timeline.groupby("obs_date")["max_frp"].max().reset_index()
            frp_chart.columns = ["Date","Max FRP (MW)"]
            st.markdown("**FRP Trend** — peak fire intensity per observation day")
            st.line_chart(frp_chart.set_index("Date"))
            st.caption("Fire Radiative Power (MW) — satellite-derived intensity indicator · Not a complete measure of fire severity")
        else:
            st.info("No timeline data for this event yet.")

    with t2:
        obs_df = get_event_observations(selected_id, limit=3000)
        if not obs_df.empty:
            obs_df["color"]  = obs_df["satellite"].apply(
                lambda s: [255,80,60,200] if s=="MODIS" else [255,210,60,200]
            )
            obs_df["radius"] = obs_df["frp"].fillna(0).apply(
                lambda f: max(2500, min(20000, (max(f,1)**0.55)*2800))
            )
            layer = pdk.Layer(
                "ScatterplotLayer", data=obs_df,
                get_position="[longitude, latitude]",
                get_radius="radius",
                get_fill_color="color",
                pickable=True, stroked=True,
                get_line_color=[255,255,255,40],
                line_width_min_pixels=1,
            )
            view = pdk.ViewState(
                latitude=obs_df["latitude"].mean(),
                longitude=obs_df["longitude"].mean(),
                zoom=7, pitch=50, bearing=-5,
            )
            deck = pdk.Deck(
                layers=[layer], initial_view_state=view,
                map_style="mapbox://styles/mapbox/satellite-v9",
                tooltip={
                    "html": "<b>{satellite}</b><br/>FRP: {frp} MW<br/>Time: {timestamp}",
                    "style": DECK_TOOLTIP,
                },
            )
            st.markdown('<div style="border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);">', unsafe_allow_html=True)
            st.pydeck_chart(deck, use_container_width=True, height=480)
            # Removed split close div
            st.caption("🔴 MODIS (1 km)  |  🟡 VIIRS (375 m)  |  Size ∝ √FRP  |  Satellite basemap")
        else:
            st.info("No observation map data for this event.")

    with t3:
        st.markdown(f"""
> ⚠️ **CELESTIAL-X-RISK-v1** is a project-defined analytical indicator — **NOT** a scientifically validated forecast.

| Component | Value | Weight |
|---|---|---|
| Fire Radiative Power | {ev.get('peak_frp', 0) or 0:.0f} MW peak | 40% |
| Duration | {dur_str} | 25% |
| Spatial Extent | {ev.get('h3_cell_count', 0)} H3 res-7 cells | 20% |
| Satellite Agreement | MODIS: {ev.get('modis_count',0)} &nbsp; VIIRS: {ev.get('viirs_count',0)} | 10% |
| Confidence | {(ev.get('max_confidence',0.5) or 0.5)*100:.0f}% normalized | 5% |

**Composite Score:** `{score:.4f} / 1.0000` &nbsp;&nbsp;|&nbsp;&nbsp; **Risk Level:** **{level}**
        """)
        if not (timeline := get_event_timeline(selected_id)).empty:
            sat_cnt = timeline.groupby("satellite")["obs_count"].sum().reset_index()
            sat_cnt.columns = ["Satellite","Observations"]
            st.markdown("**Satellite Contribution**")
            st.bar_chart(sat_cnt.set_index("Satellite"))

    with t4:
        existing = get_report_content(selected_id)
        if existing:
            dc1, dc2 = st.columns([1, 4])
            with dc1:
                st.download_button(
                    "⬇ Download .md",
                    data=existing,
                    file_name=f"CELESTIALX_{selected_id}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with st.expander("📄 Full Report", expanded=True):
                st.markdown(existing)
        else:
            st.info(f"No report generated yet. Status: **{ev.get('status')}**")
            if st.button("📋  Generate Report Now", use_container_width=False):
                with st.spinner("Generating…"):
                    r = generate_event_report(selected_id)
                if r:
                    st.success("✓ Report generated!")
                    st.rerun()

st.markdown(footer(), unsafe_allow_html=True)
