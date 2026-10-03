"""CELESTIAL X — Analytics Page (Premium)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from celestial.styles    import (ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer,
                                  section_header, metric_card, terminal_log)
from celestial.database  import init_database, get_stats
from celestial.fire_fuse  import get_events_dataframe, benchmark_h3_vs_naive
from celestial.harmonizer import get_harmonized_dataframe

init_database()
st.set_page_config(page_title="CELESTIAL X · Analytics", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("ANALYTICS")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    PERFORMANCE BENCHMARKS &nbsp;·&nbsp; FIRE EVENT STATISTICS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">ANALYTICS</div>
  <p class="cx-hero-sub-title">H3 Spatial Index Benchmark · Event Statistics · Satellite Coverage Analysis</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

stats   = get_stats()
events  = get_events_dataframe()
harm_df = get_harmonized_dataframe(limit=10000)

# ── System overview ────────────────────────────────────────────────────────────
st.markdown(section_header("📊", "SYSTEM STATISTICS"), unsafe_allow_html=True)
st.markdown(
    '<div class="cx-metrics">'
    + metric_card("Raw Observations",  f"{stats['raw_total']:,}",     "Total satellite pixels",   "blue")
    + metric_card("MODIS Pixels",      f"{stats['modis_total']:,}",   "~1 km resolution",         "red")
    + metric_card("VIIRS Pixels",      f"{stats['viirs_total']:,}",   "375 m resolution",         "amber")
    + metric_card("Fire Events",       f"{stats['events_total']:,}",  "FIRE-FUSE reconciled",     "orange")
    + metric_card("Active Events",     f"{stats['events_active']:,}", "Currently tracked",        "purple")
    + metric_card("Reports",           f"{stats['reports_total']:,}", "Auto-generated",           "green")
    + "</div>", unsafe_allow_html=True
)

# ── H3 Performance Benchmark ───────────────────────────────────────────────────
st.markdown(section_header("⚡", "H3 SPATIAL INDEX — PERFORMANCE BENCHMARK"), unsafe_allow_html=True)
st.markdown("""
<div class="cx-panel" style="margin-bottom:20px;">
  <p style="color: #ffffff;font-size:0.82rem;line-height:1.8;margin:0;">
    This benchmark demonstrates why <strong style="color:#fff;">CELESTIAL X FIRE-FUSE</strong> uses H3 spatial
    indexing instead of naive O(N²) pairwise comparison. All measurements are <em>real runtime results</em> —
    no numbers are fabricated. The naive comparison time is measured on a 500-obs sample and extrapolated.
  </p>
</div>
""", unsafe_allow_html=True)

bc1, bc2 = st.columns([3,1])
with bc1:
    n_obs = st.slider("Benchmark observation count", 100, 3000, 1000, 100,
                      help="Number of synthetic observations to use in the benchmark")
with bc2:
    st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
    run_bench = st.button("▶  Run Benchmark", use_container_width=True)

if run_bench or "bench" not in st.session_state:
    with st.spinner(f"Running H3 benchmark with {n_obs:,} observations…"):
        st.session_state["bench"] = benchmark_h3_vs_naive(n_obs)

br = st.session_state.get("bench", {})
if br:
    st.markdown(
        '<div class="cx-metrics" style="grid-template-columns:repeat(5,1fr);">'
        + metric_card("Naive Comparisons",    f"{br['naive_comparisons']:,}",    "O(N²) pairwise",           "red")
        + metric_card("H3 Comparisons",       f"{br['h3_comparisons']:,}",       "Index-filtered candidates", "green")
        + metric_card("Reduction",            f"{br['comparison_reduction_pct']}%", "Fewer comparisons",      "blue")
        + metric_card("Naive Time (est.)",    f"{br['naive_time_ms']} ms",       "Extrapolated from N=500",  "orange")
        + metric_card("H3 Time",              f"{br['h3_time_ms']} ms",          f"Full N={br['n_observations']:,}", "purple")
        + "</div>", unsafe_allow_html=True
    )
    st.markdown(f"""
    <div class="cx-panel" style="background:rgba(34,197,94,0.06);border-color:rgba(34,197,94,0.18);padding:16px 24px;">
      <p style="color: #ffffff;margin:0;font-size:0.82rem;line-height:1.8;">
        With <strong style="color:#fff;">{br['n_observations']:,} observations</strong>, H3 reduces the candidate
        comparison count from <strong style="color:rgba(239,68,68,0.9);">{br['naive_comparisons']:,}</strong> to
        only <strong style="color:rgba(34,197,94,0.9);">{br['h3_comparisons']:,}</strong> —
        a <strong style="color:#fff;">{br['comparison_reduction_pct']}% reduction</strong>.
        This allows FIRE-FUSE to scale to real-world FIRMS datasets with thousands of daily observations.
      </p>
    </div>
    """, unsafe_allow_html=True)

# ── Event statistics ────────────────────────────────────────────────────────────
if not events.empty:
    st.markdown(section_header("🔥", "FIRE EVENT STATISTICS"), unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📊  Status Distribution", "📈  FRP Analysis", "📅  Temporal Analysis"])

    with tab1:
        sc = events["status"].value_counts().reset_index()
        sc.columns = ["Status","Count"]
        st.bar_chart(sc.set_index("Status"), color="#ff4444")
        st.caption("Fire events grouped by lifecycle status")

    with tab2:
        if "peak_frp" in events.columns:
            frp = events[events["peak_frp"].notna()].copy()
            frp["peak_frp"] = frp["peak_frp"].round(1)
            by_level = frp.groupby("risk_level")["peak_frp"].agg(["max","mean","count"]).reset_index()
            by_level.columns = ["Risk Level","Max FRP (MW)","Mean FRP (MW)","Count"]
            st.dataframe(by_level, use_container_width=True, hide_index=True)
            st.bar_chart(frp[["peak_frp"]].rename(columns={"peak_frp":"Peak FRP (MW)"}).head(80))

    with tab3:
        if "duration_hours" in events.columns:
            dur = events[events["duration_hours"].notna()].copy()
            dur["Duration (days)"] = (dur["duration_hours"] / 24).round(1)
            dur_top = dur[["event_id","Duration (days)","status"]].sort_values("Duration (days)", ascending=False).head(30)
            st.dataframe(dur_top.rename(columns={"event_id":"Event ID","status":"Status"}),
                         use_container_width=True, hide_index=True)
            st.bar_chart(dur[["Duration (days)"]].head(50))

# ── Satellite coverage ─────────────────────────────────────────────────────────
if not harm_df.empty:
    st.markdown(section_header("🛰", "SATELLITE COVERAGE"), unsafe_allow_html=True)
    sat_c = harm_df["satellite"].value_counts().reset_index()
    sat_c.columns = ["Satellite","Observations"]
    st.bar_chart(sat_c.set_index("Satellite"))
    if "timestamp" in harm_df.columns:
        harm_df["date"] = harm_df["timestamp"].str[:10]
        daily = harm_df.groupby(["date","satellite"]).size().reset_index(name="count")
        daily_pivot = daily.pivot(index="date", columns="satellite", values="count").fillna(0)
        st.markdown("**Daily Observations by Satellite**")
        st.line_chart(daily_pivot)
        st.caption("Daily observation counts — higher counts indicate better satellite coverage density")

st.markdown(footer(), unsafe_allow_html=True)
