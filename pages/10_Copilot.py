"""
CELESTIAL X - Fire Intelligence Copilot
=========================================
AI-powered conversational and analytical assistant querying the harmonized
satellite database directly. All answers are grounded in verifiable SQL queries.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px

from celestial.styles   import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header, metric_card
from celestial.database import init_database
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
  <p class="cx-hero-sub-title">Natural Language Queries • Direct SQL Provenance • Verifiable Satellite Science</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

st.markdown(section_header("💡", "QUICK ANALYTICAL PROMPTS"), unsafe_allow_html=True)

# Suggested prompt buttons
cols = st.columns(len(COPILOT_SUGGESTED_PROMPTS))
selected_prompt = None
for idx, prompt_text in enumerate(COPILOT_SUGGESTED_PROMPTS):
    with cols[idx]:
        if st.button(prompt_text, key=f"chip_{idx}", use_container_width=True):
            selected_prompt = prompt_text

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# User input text box
user_input = st.text_input(
    "Ask a question about the satellite fire database:",
    value=selected_prompt or "",
    placeholder="e.g. Which month had the highest fire activity in Tamil Nadu?",
    help="Type any query about historical trends, persistent events, or sensor comparisons."
)

if user_input:
    with st.spinner("Analyzing harmonized database..."):
        res = query_copilot(user_input)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown(section_header("🤖", "COPILOT RESPONSE"), unsafe_allow_html=True)

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
            st.caption("Grounded in CELESTIAL X SQLite Database (`harmonized_observations` & `fire_events`).")

st.markdown(footer(), unsafe_allow_html=True)
