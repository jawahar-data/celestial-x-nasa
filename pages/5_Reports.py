"""CELESTIAL X — Reports Page (Premium)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from celestial.styles    import (ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer,
                                  section_header, metric_card)
from celestial.database  import init_database
from celestial.reports   import (get_all_reports, get_report_content,
                                  generate_pending_reports, generate_pdf_report)

init_database()
st.set_page_config(page_title="CELESTIAL X · Reports", page_icon="📋", layout="wide",
                   initial_sidebar_state="collapsed")
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("REPORTS")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    AUTOMATED FIRE EVENT REPORTS &nbsp;·&nbsp; CELESTIAL X
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">REPORTS</div>
  <p class="cx-hero-sub-title">Auto-Generated on Event Closure · PDF &amp; Markdown · Downloadable</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# ── Generate button ────────────────────────────────────────────────────────────
rc1, rc2 = st.columns([5, 1])
with rc2:
    if st.button("🔄 Generate", use_container_width=True):
        with st.spinner("Generating reports for closed events…"):
            n = generate_pending_reports()
        st.success(f"✓ {n} report(s) generated")
        st.rerun()

reports = get_all_reports()

if not reports:
    st.markdown("""
    <div class="cx-panel" style="text-align:center;padding:80px 40px;margin-top:24px;">
      <div style="font-size:4rem;margin-bottom:20px;">📋</div>
      <div style="font-family:'Orbitron',sans-serif;font-size:1rem;color:#ffffff;
                  letter-spacing:2px;margin-bottom:12px;">NO REPORTS YET</div>
      <p style="color:#ffffff;font-size:0.82rem;max-width:440px;margin:0 auto;line-height:1.8;">
        Reports are auto-generated when fire events close.<br/>
        You can also generate them manually from the <strong>🔥 Fire Events</strong> page.
      </p>
    </div>""", unsafe_allow_html=True)
    st.markdown(footer(), unsafe_allow_html=True)
    st.stop()

# ── Summary table ──────────────────────────────────────────────────────────────
st.markdown(section_header("📋", f"FIRE EVENT REPORTS  ·  {len(reports)} TOTAL"),
            unsafe_allow_html=True)

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

# ── Report Viewer ─────────────────────────────────────────────────────────────
st.markdown(section_header("📄", "REPORT VIEWER & DOWNLOAD"), unsafe_allow_html=True)

selected_event = st.selectbox(
    "Select report",
    [r["event_id"] for r in reports],
    label_visibility="collapsed",
)

if selected_event:
    content_md = get_report_content(selected_event)
    if content_md:

        # ── Download button row ────────────────────────────────────────────────
        st.markdown("""
        <div style="
          background:rgba(255,255,255,0.04);
          border:1px solid rgba(255,255,255,0.09);
          border-radius:12px;
          padding:20px 24px;
          margin-bottom:20px;
          display:flex;
          align-items:center;
          gap:16px;
          flex-wrap:wrap;">
          <div style="flex:1;min-width:200px;">
            <div style="font-family:'Orbitron',sans-serif;font-size:0.7rem;font-weight:700;
                        letter-spacing:1.5px;color:#ffffff;margin-bottom:4px;">
              📥 DOWNLOAD INCIDENT REPORT
            </div>
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);">
              Choose PDF for a professional formatted report or Markdown for raw data
            </div>
          </div>
        """, unsafe_allow_html=True)

        btn_col1, btn_col2, _ = st.columns([1, 1, 4])

        with btn_col1:
            # Generate PDF on demand
            with st.spinner(""):
                pdf_bytes = generate_pdf_report(selected_event)
            if pdf_bytes:
                st.download_button(
                    label="⬇ Download PDF",
                    data=pdf_bytes,
                    file_name=f"CELESTIALX_{selected_event}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_pdf",
                )
            else:
                st.warning("PDF library not available. Install fpdf2.")

        with btn_col2:
            st.download_button(
                label="⬇ Download .md",
                data=content_md,
                file_name=f"CELESTIALX_{selected_event}.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_md",
            )

        # Removed split close div

        # ── Report preview ─────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown(content_md)

st.markdown(footer(), unsafe_allow_html=True)
