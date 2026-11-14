"""
CELESTIAL X 2.0 - Fire Intelligence Copilot
============================================
AI-powered conversational and analytical assistant querying the harmonized
satellite database directly. All answers are grounded in verifiable SQL queries.
Features:
  - Real-time weather, fuel condition, and Fosberg index context
  - Microsoft Planetary Computer STAC environmental sensitivity & protected reserves
  - Potential downwind spread & exposure corridors
  - Full SQL provenance and audit trail
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px

from celestial.styles   import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header, metric_card
from celestial.database import init_database, get_connection
from celestial.copilot  import query_copilot, COPILOT_SUGGESTED_PROMPTS

init_database()
st.set_page_config(
    page_title="CELESTIAL X — Copilot",
    page_icon="🤖", layout="wide",
    initial_sidebar_state="collapsed",
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("COPILOT")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge"><span class="cx-hero-badge-dot"></span>
    DATA-GROUNDED FIRE INTELLIGENCE ASSISTANT — NO HALLUCINATIONS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">FIRE INTELLIGENCE COPILOT</div>
  <p class="cx-hero-sub-title">Natural Language Queries • Multi-Pillar Environmental Context • Direct SQL Provenance</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

st.markdown(section_header("💡", "ANALYTICAL INTELLIGENCE PROMPTS"), unsafe_allow_html=True)

# Grid layout for suggested prompt chips (2 columns)
selected_prompt = None
c1, c2 = st.columns(2)
for idx, prompt_text in enumerate(COPILOT_SUGGESTED_PROMPTS):
    target_col = c1 if idx % 2 == 0 else c2
    with target_col:
        if st.button(f"⚡ {prompt_text}", key=f"chip_{idx}", use_container_width=True):
            selected_prompt = prompt_text

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# User input text box
user_input = st.text_input(
    "Ask a question about the satellite fire database:",
    value=selected_prompt or "",
    placeholder="e.g. Which fire events are associated with high winds or dry weather?",
    help="Type any query about historical trends, multi-day events, weather, spread, or protected reserves."
)

if user_input:
    with st.spinner("Executing verifiable SQL queries across satellite intelligence tables..."):
        res = query_copilot(user_input)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown(section_header("🤖", "COPILOT INTELLIGENCE RESPONSE"), unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);
                border-radius:14px;padding:24px 28px;font-size:0.95rem;line-height:1.8;
                color:rgba(255,255,255,0.9);">
      {res['answer_text'].replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    # Show data table if available
    if res.get("result_data"):
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        res_df = pd.DataFrame(res["result_data"])
        st.dataframe(res_df, use_container_width=True)

    # SQL Provenance inspection (Transparency)
    if res.get("sql_executed"):
        with st.expander("🔍 Inspect Verifiable SQL Query Executed", expanded=False):
            st.code(res["sql_executed"], language="sql")
            st.caption("Grounded in CELESTIAL X SQLite Database (`harmonized_observations`, `fire_events`, `weather_observations`, `environmental_context`, `fire_spread_assessments`).")

# Recent Copilot Query History
st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
with st.expander("📜 Recent Query Audit Log (ai_query_history)", expanded=False):
    try:
        conn = get_connection()
        history_df = pd.read_sql_query(
            "SELECT query_id, user_query, sql_executed, response_status, timestamp FROM ai_query_history ORDER BY query_id DESC LIMIT 10;",
            conn
        )
        conn.close()
        if not history_df.empty:
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No query history recorded yet.")
    except Exception as e:
        st.caption(f"Query history unavailable: {e}")

st.markdown(footer(), unsafe_allow_html=True)
