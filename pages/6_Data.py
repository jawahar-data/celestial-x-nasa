"""CELESTIAL X — Data Pipeline Page (Premium)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from celestial.styles    import (ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer,
                                  section_header, metric_card, terminal_log)
from celestial.config    import get_key_status
from celestial.database  import init_database, get_stats
from celestial.ingestion  import (fetch_raw, store_raw, generate_demo_observations,
                                   REGION_BBOXES, PRODUCTS, PRODUCT_TO_SAT)
from celestial.harmonizer import harmonize_dataframe, store_harmonized
from celestial.fire_fuse  import run_fire_fuse, get_events_dataframe, DEFAULT_CONFIG, close_inactive_events
from celestial.risk       import assess_all_events
from celestial.reports    import generate_pending_reports

init_database()
st.set_page_config(page_title="CELESTIAL X · Data Pipeline", page_icon="💾", layout="wide", initial_sidebar_state="collapsed")
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("DATA")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    INGEST · HARMONIZE · FIRE-FUSE · RISK · REPORTS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">DATA PIPELINE</div>
  <p class="cx-hero-sub-title">NASA FIRMS API Ingestion &nbsp;·&nbsp; Schema Harmonization &nbsp;·&nbsp; CELESTIAL X FIRE-FUSE Engine</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

key_status = get_key_status()
api_key    = key_status["key"]
demo_mode  = (api_key in ("DEMO_MODE","") or not api_key)

if demo_mode:
    st.markdown("""
    <div class="cx-panel" style="background:rgba(59,130,246,0.06);border-color:rgba(59,130,246,0.20);
                                  padding:16px 24px;margin-top:16px;">
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:1.2rem;">🎯</span>
        <p style="margin:0;color: #ffffff;font-size:0.82rem;line-height:1.7;">
          <strong style="color:#fff;">Demo Mode</strong> — No API key configured.
          The pipeline will generate synthetic multi-day fire data for demonstration.
          Configure your NASA FIRMS key in <strong>⚙ Settings</strong> to use real satellite data.
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Configuration ──────────────────────────────────────────────────────────────
st.markdown(section_header("⚙", "PIPELINE CONFIGURATION"), unsafe_allow_html=True)
# Removed empty split div wrapper

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**🌍 Region & Data**")
    region_name  = st.selectbox("Region", list(REGION_BBOXES.keys()), index=0, label_visibility="collapsed")
    bbox         = REGION_BBOXES[region_name]
    day_range    = st.slider("Days of data", 1, 10, 3)
    viirs_label  = st.selectbox("VIIRS sensor", list(PRODUCTS.keys())[1:], index=0)
    viirs_product = PRODUCTS[viirs_label]
    st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;color: #ffffff;margin-top:4px;">bbox: {bbox}</div>', unsafe_allow_html=True)

with c2:
    st.markdown("**🔧 FIRE-FUSE Thresholds**")
    spatial_km   = st.slider("Spatial threshold (km)",   5.0,  50.0, float(DEFAULT_CONFIG["SPATIAL_THRESHOLD_KM"]),  2.5)
    temporal_hrs = st.slider("Temporal threshold (hrs)", 6.0, 120.0, float(DEFAULT_CONFIG["TEMPORAL_THRESHOLD_HRS"]), 6.0)
    closure_days = st.slider("Event closure (days)",       1,    14,  int(DEFAULT_CONFIG["EVENT_CLOSURE_DAYS"]))

with c3:
    st.markdown("**ℹ Threshold Documentation**")
    st.markdown(f"""
<div style="font-size:0.75rem;color: #ffffff;line-height:2;font-family:'JetBrains Mono',monospace;">
  Spatial: H3 res-7 cell ≈ 5.16 km<br/>
  Default {DEFAULT_CONFIG['SPATIAL_THRESHOLD_KM']} km ≈ 3-cell growth<br/><br/>
  Temporal: MODIS ≈ 1-2 passes/day<br/>
  Default {DEFAULT_CONFIG['TEMPORAL_THRESHOLD_HRS']} hrs = full revisit gap<br/><br/>
  Closure: No obs → fire inactive<br/>
  Default {DEFAULT_CONFIG['EVENT_CLOSURE_DAYS']} days (configurable)
</div>
""", unsafe_allow_html=True)

# Removed split close div

config = {
    "SPATIAL_THRESHOLD_KM":   spatial_km,
    "TEMPORAL_THRESHOLD_HRS": temporal_hrs,
    "EVENT_CLOSURE_DAYS":     closure_days,
    "H3_RESOLUTION_EVENT":    DEFAULT_CONFIG["H3_RESOLUTION_EVENT"],
    "H3_K_RING":              DEFAULT_CONFIG["H3_K_RING"],
    "H3_RESOLUTION_OBS":      DEFAULT_CONFIG["H3_RESOLUTION_OBS"],
}

# ── Launch buttons ─────────────────────────────────────────────────────────────
bc1, bc2, bc3 = st.columns([4, 1, 1])
with bc1:
    run_btn = st.button("⚡  LAUNCH CELESTIAL X FIRE-FUSE PIPELINE", use_container_width=True)
with bc2:
    close_btn = st.button("🔒 Close Inactive", use_container_width=True,
                           help="Mark events with no recent observations as CLOSED")
with bc3:
    if st.button("🗑 Clear Log", use_container_width=True):
        st.session_state["pipeline_log"] = []
        st.session_state["pipeline_results"] = {}

if close_btn:
    with st.spinner("Closing inactive events…"):
        n_closed = close_inactive_events(closure_days=closure_days)
        n_rep    = generate_pending_reports()
    st.success(f"✓ {n_closed} events closed · {n_rep} reports generated")
    st.rerun()

# ── Pipeline execution ─────────────────────────────────────────────────────────
if "pipeline_log" not in st.session_state:
    st.session_state["pipeline_log"] = []
if "pipeline_results" not in st.session_state:
    st.session_state["pipeline_results"] = {}

if run_btn:
    logs = []
    def log(msg): logs.append(msg); st.session_state["pipeline_log"].append(msg)

    results = {}
    with st.spinner("Running CELESTIAL X FIRE-FUSE Pipeline…"):

        log('<span class="log-head">█ STEP 1 — INGESTION (NASA FIRMS API)</span>')
        if demo_mode:
            log('<span class="log-warn">⚠ Demo mode — generating synthetic multi-day fire data</span>')
            modis_raw, viirs_raw = generate_demo_observations(bbox, n_days=day_range, n_fires=8)
            log(f'<span class="log-ok">✓ MODIS demo: {len(modis_raw):,} observations</span>')
            log(f'<span class="log-ok">✓ VIIRS demo: {len(viirs_raw):,} observations</span>')
        else:
            modis_raw = fetch_raw(api_key, "MODIS_NRT", bbox, day_range, log)
            store_raw(modis_raw, "MODIS_NRT", bbox)
            viirs_raw = fetch_raw(api_key, viirs_product, bbox, day_range, log)
            store_raw(viirs_raw, viirs_product, bbox)

        results["modis_raw"] = len(modis_raw)
        results["viirs_raw"] = len(viirs_raw)

        log('<span class="log-head">█ STEP 2 — HARMONIZATION (Schema + H3 Mapping)</span>')
        modis_h = pd.DataFrame()
        viirs_h  = pd.DataFrame()
        if not modis_raw.empty:
            modis_h = harmonize_dataframe(modis_raw, "MODIS")
            n = store_harmonized(modis_h)
            log(f'<span class="log-ok">✓ MODIS: {len(modis_h):,} harmonized → {n:,} stored</span>')
        if not viirs_raw.empty:
            sat_lbl = "VIIRS_SNPP" if "SNPP" in viirs_product else "VIIRS_NOAA20"
            viirs_h  = harmonize_dataframe(viirs_raw, sat_lbl)
            n = store_harmonized(viirs_h)
            log(f'<span class="log-ok">✓ VIIRS: {len(viirs_h):,} harmonized → {n:,} stored</span>')

        all_h = pd.concat([modis_h, viirs_h], ignore_index=True) if not (modis_h.empty and viirs_h.empty) else pd.DataFrame()
        results["harmonized"] = len(all_h)

        log('<span class="log-head">█ STEP 3 — CELESTIAL X FIRE-FUSE (Spatiotemporal Reconciliation)</span>')
        ff = run_fire_fuse(all_h, config=config, log_fn=log)
        results["fire_fuse"] = ff

        log('<span class="log-head">█ STEP 4 — CELESTIAL-X-RISK-v1 Assessment</span>')
        n_risk = assess_all_events(log_fn=log)
        results["risk"] = n_risk

        log('<span class="log-head">█ STEP 5 — Auto-Report Generation</span>')
        n_rep = generate_pending_reports(log_fn=log)
        results["reports"] = n_rep

        log('<span class="log-ok">✓✓ CELESTIAL X FIRE-FUSE Pipeline complete.</span>')

    st.session_state["pipeline_results"] = results

# ── Log & results ──────────────────────────────────────────────────────────────
if st.session_state.get("pipeline_log"):
    st.markdown(section_header("📋", "PIPELINE EXECUTION LOG"), unsafe_allow_html=True)
    st.markdown(terminal_log(st.session_state["pipeline_log"], "celestial-x-fire-fuse.log"), unsafe_allow_html=True)

res = st.session_state.get("pipeline_results", {})
if res:
    st.markdown(section_header("📊", "PIPELINE RESULTS"), unsafe_allow_html=True)
    ff = res.get("fire_fuse", {})
    st.markdown(
        '<div class="cx-metrics">'
        + metric_card("MODIS Raw",      str(res.get("modis_raw",0)),            "Pixels ingested",           "blue")
        + metric_card("VIIRS Raw",      str(res.get("viirs_raw",0)),            "Pixels ingested",           "amber")
        + metric_card("Harmonized",     str(res.get("harmonized",0)),           "Common schema obs",         "green")
        + metric_card("Events Created", str(ff.get("events_created",0)),        "New fire events",           "orange")
        + metric_card("Events Updated", str(ff.get("events_updated",0)),        "Extended existing events",  "purple")
        + metric_card("Events Closed",  str(ff.get("events_closed",0)),         "Reports auto-generated",    "red")
        + "</div>", unsafe_allow_html=True
    )
    st.info(
        f"**FIRE-FUSE Interpretation:** "
        f"{ff.get('events_created',0)} new events + "
        f"{ff.get('events_updated',0)} updated (multi-day obs linked) = "
        f"{ff.get('obs_new_event',0) + ff.get('obs_matched',0)} total observations processed."
    )

# ── Algorithm docs ─────────────────────────────────────────────────────────────
st.markdown(section_header("📖", "ALGORITHM DOCUMENTATION"), unsafe_allow_html=True)
with st.expander("CELESTIAL X FIRE-FUSE — Full design and threshold documentation"):
    st.markdown(f"""
### CELESTIAL X FIRE-FUSE: Two-Stage Spatiotemporal Reconciliation

#### Stage 1 — H3 Candidate Search
For each incoming harmonized observation:
1. Convert `(latitude, longitude)` → H3 cell at resolution **{DEFAULT_CONFIG['H3_RESOLUTION_EVENT']}**
2. Expand to **k-ring = {DEFAULT_CONFIG['H3_K_RING']}** neighborhood cells
3. Query open fire events matching any of those cells
4. Replaces O(N²) with spatial index lookup

#### Stage 2 — Precise Spatiotemporal Validation
For each candidate event:
- Compute **haversine distance** to event centroid
- Compute **temporal gap** to event's last observed time
- MATCH if: `distance ≤ {spatial_km} km` AND `gap ≤ {temporal_hrs} hrs`
- Else: CREATE new fire event

#### Fire Event Lifecycle
```
DETECTED → ACTIVE → PERSISTENT (≥3 days)
                  → EXPANDING  (growing H3 coverage)
                  → DECLINING  (FRP decreasing)
                  → CLOSED     (no obs > {closure_days} days)
                              ↓
                  Auto-report generated
```
    """)

st.markdown(footer(), unsafe_allow_html=True)
