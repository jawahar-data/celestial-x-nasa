"""
CELESTIAL X — Automated Situation Reports & Regional Briefs
=============================================================
Provides automated intelligence documentation for command teams:
  1. Automated Regional Fire Intelligence Briefs (Current activity, historical baseline, anomaly status, environmental drivers)
  2. Individual Event Closure Reports (Lifecycle, FRP progression, satellite contribution)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timezone

from celestial.styles    import (ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer,
                                  section_header, metric_card)
from celestial.database  import init_database
from celestial.reports   import (get_all_reports, get_report_content,
                                  generate_pending_reports, generate_pdf_report)
from celestial.calendar  import PRESET_REGIONS, get_current_status
from celestial.season    import analyze_fire_season
from celestial.environmental import get_environmental_context

init_database()
st.set_page_config(page_title="CELESTIAL X — Reports", page_icon="📄", layout="wide",
                   initial_sidebar_state="collapsed")
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("REPORTS")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    AUTOMATED SATELLITE FIRE INTELLIGENCE BRIEFS • CELESTIAL X
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">REPORTS</div>
  <p class="cx-hero-sub-title">Regional Situation Briefs • Event Closure Audits • Downloadable Documentation</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

tab_regional, tab_events = st.tabs([
    "🌍 REGIONAL INTELLIGENCE BRIEF",
    "🔥 INDIVIDUAL EVENT CLOSURE REPORTS"
])

# -------------------------------------------------------------
# TAB 1: REGIONAL INTELLIGENCE BRIEF
# -------------------------------------------------------------
with tab_regional:
    st.markdown(section_header("🌍", "AUTOMATED REGIONAL FIRE INTELLIGENCE BRIEF"), unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:0.85rem;color:rgba(255,255,255,0.7);margin-bottom:16px;">
      Compile an automated, publication-ready briefing for emergency managers and response authorities 
      synthesizing active fire activity, 20-year climatological baselines, anomaly percentiles, and weather context.
    </p>
    """, unsafe_allow_html=True)

    col_reg_sel, col_gen_btn = st.columns([3, 1])
    with col_reg_sel:
        selected_region = st.selectbox("Select Target Region for Briefing:", list(PRESET_REGIONS.keys()), index=1)
    with col_gen_btn:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        gen_reg_clicked = st.button("Generate Regional Brief", type="primary", use_container_width=True)

    coords = PRESET_REGIONS.get(selected_region, (-180, -90, 180, 90))
    if coords:
        w, s, e, n = coords
        status = get_current_status(w, s, e, n)
        season = analyze_fire_season(w, s, e, n)
        env = get_environmental_context(selected_region, month=status.get("month", 3) if status else 3)
        now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Compile markdown brief
        brief_md = f"""# CELESTIAL X — REGIONAL FIRE INTELLIGENCE BRIEF
**Region:** {selected_region}  
**Coordinates (W, S, E, N):** {w}°, {s}°, {e}°, {n}°  
**Issue Timestamp:** {now_str}  
**Source:** NASA FIRMS Harmonized Satellite Observations (MODIS + VIIRS)  
**Harmonization Engine:** CELESTIAL X FIRE-FUSE v1.0  

---

## 1. EXECUTIVE SITUATION SUMMARY
* **Current Monitoring Month:** {status.get('month_name', 'Current')} {status.get('year', 2026)}
* **Active Harmonized Hotspots:** {status.get('actual', 0):,}
* **Historical Multi-Year Median:** {status.get('median', 0):,} ({status.get('years_in_baseline', 20)}-year baseline)
* **Anomaly Deviation:** {status.get('anomaly_pct', 0.0):+.1f}% vs. Historical Median
* **Percentile Ranking:** {status.get('percentile_rank', 50):.0f}th Percentile ({status.get('severity', 'Normal')})
* **Standardized Anomaly (Z-Score):** {status.get('z_score', 0.0):+.2f} σ

---

## 2. CLIMATOLOGICAL FIRE REGIME & SEASONALITY
* **Typical Season Onset:** {season.get('onset_month', 'Feb')} (10% cumulative annual burn)
* **Peak Fire Activity Month:** {season.get('peak_month', 'Mar')}
* **Typical Season Cessation:** {season.get('cessation_month', 'May')} (90% cumulative annual burn)
* **Core Season Duration:** {season.get('duration_months', 4)} Months (~{season.get('duration_days', 120)} active burning days)
* **Multi-Year Arrival Shift:** {season.get('shift_days', -8)} Days earlier arrival compared to 2000–2010 baseline.

---

## 3. ENVIRONMENTAL CONTEXT & FIRE WEATHER INDICATORS
* **Ambient Air Temperature:** {env.get('temperature_c', 32.4)} °C
* **Relative Humidity:** {env.get('relative_humidity_pct', 54)}%
* **Surface Wind Velocity:** {env.get('wind_speed_kmh', 16)} km/h
* **Vegetation Fuel Dryness Index:** {env.get('fuel_dryness_index', 88)} / 100
* **Fire Weather Risk Rating:** **{env.get('danger_rating', 'HIGH')}** (Score: {env.get('fire_weather_score', 72)}/100)

---

## 4. SCIENTIFIC DATA PROVENANCE & METHODOLOGY
* **Sensors Integrated:** MODIS (Terra/Aqua, 1 km nadir footprint) and VIIRS (S-NPP/NOAA-20/21, 375 m nadir footprint).
* **Harmonization Normalization:** Cross-sensor detection ratios (~3.82x sensitivity adjustment) and confidence projection onto continuous [0.0, 1.0] domain.
* **Limitations:** Satellite thermal anomalies represent radiant heat and may be obscured during heavy monsoonal cloud cover.

*Report automatically compiled by CELESTIAL X Fire Intelligence Platform.*
"""

        c_dl, c_spacer = st.columns([1, 3])
        with c_dl:
            clean_rname = selected_region.replace(" ", "_").replace(",", "")[:20]
            st.download_button(
                "💾 Download Brief (.md)",
                data=brief_md,
                file_name=f"CELESTIAL_X_BRIEF_{clean_rname}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with st.expander("📄 View Full Regional Intelligence Brief", expanded=True):
            st.markdown(brief_md)

# -------------------------------------------------------------
# TAB 2: INDIVIDUAL EVENT REPORTS
# -------------------------------------------------------------
with tab_events:
    st.markdown(section_header("📄", "PERSISTENT EVENT CLOSURE AUDIT REPORTS"), unsafe_allow_html=True)
    
    rc1, rc2 = st.columns([5, 1])
    with rc2:
        if st.button("Generate Pending", use_container_width=True):
            with st.spinner("Generating reports for closed events..."):
                n = generate_pending_reports()
            st.success(f"{n} report(s) generated")
            st.rerun()

    reports = get_all_reports()

    if not reports:
        st.markdown("""
        <div class="cx-panel" style="text-align:center;padding:60px 40px;margin-top:20px;">
          <div style="font-size:3rem;margin-bottom:14px;opacity:0.4;">📄</div>
          <div style="font-family:'Orbitron',sans-serif;font-size:0.95rem;color:#ffffff;
                      letter-spacing:2px;margin-bottom:10px;">NO EVENT REPORTS FILED YET</div>
          <p style="color:rgba(255,255,255,0.7);font-size:0.82rem;max-width:440px;margin:0 auto;line-height:1.8;">
            Reports are automatically compiled when active fire events close.<br/>
            You can also generate individual reports directly from the <strong>🔥 Fire Events</strong> inspector.
          </p>
        </div>""", unsafe_allow_html=True)
    else:
        rep_df = pd.DataFrame(reports)
        display_cols = [c for c in [
            "event_id", "report_type", "generated_at", "status", "risk_level",
            "duration_hours", "peak_frp", "observation_count",
        ] if c in rep_df.columns]
        st.dataframe(
            rep_df[display_cols].rename(columns={
                "event_id": "Event ID", "report_type": "Type", "generated_at": "Generated",
                "status": "Status", "risk_level": "Risk Level",
                "duration_hours": "Duration (hrs)", "peak_frp": "Peak FRP (MW)",
                "observation_count": "Observations",
            }),
            use_container_width=True, hide_index=True,
        )

        selected_event = st.selectbox("Select Event Report to Inspect:", [r["event_id"] for r in reports])
        existing_md = get_report_content(selected_event)
        if existing_md:
            st.download_button(
                "💾 Download Event Report (.md)",
                data=existing_md,
                file_name=f"CELESTIALX_{selected_event}.md",
                mime="text/markdown"
            )
            st.markdown(existing_md)

st.markdown(footer(), unsafe_allow_html=True)
