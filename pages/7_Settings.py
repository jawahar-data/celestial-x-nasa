"""CELESTIAL X — Settings Page (Premium)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import platform
import streamlit as st
import streamlit.components.v1 as components
from celestial.styles    import (ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header)
from celestial.database  import init_database
from celestial.config    import get_key_status, validate_api_key, save_api_key, mask_key
from celestial.fire_fuse  import DEFAULT_CONFIG

init_database()
st.set_page_config(page_title="CELESTIAL X · Settings", page_icon="⚙", layout="wide", initial_sidebar_state="collapsed")
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("SETTINGS")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge">
    <span class="cx-hero-badge-dot"></span>
    SYSTEM CONFIGURATION &nbsp;·&nbsp; API SECURITY &nbsp;·&nbsp; ALGORITHM DEFAULTS
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">SETTINGS</div>
  <p class="cx-hero-sub-title">API Key Management · Threshold Defaults · System Information · Security</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

key_status = get_key_status()
demo_mode  = key_status["key"] == "DEMO_MODE"

# ── API Key ────────────────────────────────────────────────────────────────────
st.markdown(section_header("🔑", "NASA FIRMS API KEY"), unsafe_allow_html=True)
# Removed empty split div wrapper

if key_status["configured"] and not demo_mode:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
      <span style="font-size:1.2rem;">✅</span>
      <div>
        <div style="font-family:'Orbitron',sans-serif;font-size:0.62rem;font-weight:700;
                    letter-spacing:2px;color:rgba(34,197,94,0.9);margin-bottom:4px;">API KEY CONFIGURED</div>
        <code style="font-size:0.78rem;color: #ffffff;">{key_status['masked']}</code>
      </div>
    </div>
    """, unsafe_allow_html=True)
elif demo_mode:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
      <span style="font-size:1.2rem;">🎯</span>
      <div>
        <div style="font-family:'Orbitron',sans-serif;font-size:0.62rem;font-weight:700;
                    letter-spacing:2px;color:rgba(59,130,246,0.9);margin-bottom:4px;">DEMO MODE ACTIVE</div>
        <span style="font-size:0.78rem;color: #ffffff;">Using synthetic data. Configure a real key below.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
      <span style="font-size:1.2rem;">⚠️</span>
      <div style="font-family:'Orbitron',sans-serif;font-size:0.62rem;font-weight:700;
                  letter-spacing:2px;color:rgba(245,158,11,0.9);">NO API KEY CONFIGURED</div>
    </div>
    """, unsafe_allow_html=True)

new_key = st.text_input(
    "NASA FIRMS API Key",
    type="password",
    placeholder="Enter new NASA FIRMS API key…",
    label_visibility="collapsed",
)
k1, k2, k3 = st.columns(3)
with k1:
    if st.button("🔍  Validate Key", use_container_width=True):
        if new_key.strip():
            with st.spinner("Validating…"):
                valid, msg = validate_api_key(new_key.strip())
            st.success(f"✓ {msg}") if valid else st.error(f"✗ {msg}")
        else:
            st.warning("Enter a key first.")
with k2:
    if st.button("💾  Save Key", use_container_width=True):
        if new_key.strip():
            with st.spinner("Validating and saving…"):
                valid, msg = validate_api_key(new_key.strip())
            if valid:
                save_api_key(new_key.strip())
                st.success(f"✓ Saved: `{mask_key(new_key.strip())}`")
                st.rerun()
            else:
                st.error(f"✗ {msg}")
        else:
            st.warning("Enter a key first.")
with k3:
    if st.button("🎯  Demo Mode", use_container_width=True):
        save_api_key("DEMO_MODE")
        st.success("Demo mode activated.")
        st.rerun()

st.markdown("""
<div style="margin-top:14px;padding:12px 16px;background:rgba(255,255,255,0.03);border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
  <p style="margin:0;color: #ffffff;font-size:0.72rem;line-height:1.9;font-family:'JetBrains Mono',monospace;">
    Get a free API key at <a href="https://firms.modaps.eosdis.nasa.gov/api/area/" target="_blank">firms.modaps.eosdis.nasa.gov</a><br/>
    Key is stored in local <code>.env</code> file · Never committed to git · Never sent to browser
  </p>
</div>
""", unsafe_allow_html=True)
# Removed split close div

# ── Algorithm defaults ─────────────────────────────────────────────────────────
st.markdown(section_header("⚡", "FIRE-FUSE ALGORITHM DEFAULTS"), unsafe_allow_html=True)
with st.expander("View documented default thresholds and their scientific basis"):
    st.markdown(f"""
| Parameter | Default | Scientific Basis |
|---|---|---|
| `SPATIAL_THRESHOLD_KM` | **{DEFAULT_CONFIG['SPATIAL_THRESHOLD_KM']} km** | H3 res-7 ≈ 5.16 km · 15 km allows ~3-cell fire growth |
| `TEMPORAL_THRESHOLD_HRS` | **{DEFAULT_CONFIG['TEMPORAL_THRESHOLD_HRS']} hrs** | MODIS ≈ 1-2 passes/day · 36 hrs covers full revisit gap |
| `EVENT_CLOSURE_DAYS` | **{DEFAULT_CONFIG['EVENT_CLOSURE_DAYS']} days** | No obs for N days → fire inactive |
| `H3_RESOLUTION_EVENT` | **{DEFAULT_CONFIG['H3_RESOLUTION_EVENT']}** | Res-7 ≈ 5.16 km — event-level matching |
| `H3_K_RING` | **{DEFAULT_CONFIG['H3_K_RING']}** | 2-ring at res-7 ≈ 10–20 km search radius |
| `H3_RESOLUTION_OBS` | **{DEFAULT_CONFIG['H3_RESOLUTION_OBS']}** | Res-8 ≈ 0.74 km² — pixel-level dedup |

All thresholds are **configurable per pipeline run** on the 💾 Data page.
    """)

# ── System info ────────────────────────────────────────────────────────────────
st.markdown(section_header("ℹ", "SYSTEM INFORMATION"), unsafe_allow_html=True)
with st.expander("Runtime environment and library versions"):
    try:
        import h3 as h3lib
        h3v = h3lib.__version__
    except Exception:
        h3v = "installed"
    try:
        import pydeck
        pdv = pydeck.__version__
    except Exception:
        pdv = "installed"
    import pandas as pd, numpy as np
    st.markdown(f"""
| Component | Version |
|---|---|
| Python | {platform.python_version()} |
| Streamlit | {st.__version__} |
| H3 | {h3v} |
| PyDeck | {pdv} |
| Pandas | {pd.__version__} |
| NumPy | {np.__version__} |
| Platform | {platform.system()} {platform.release()} |
| Database | SQLite · `celestial_x.db` |
| Algorithm | CELESTIAL X FIRE-FUSE v1 |
| Risk Model | CELESTIAL-X-RISK-v1 (project-defined analytical indicator) |
| Data Source | NASA FIRMS MODIS NRT + VIIRS SNPP/NOAA-20 NRT |
    """)

# ── Security notes ─────────────────────────────────────────────────────────────
st.markdown(section_header("🔒", "SECURITY"), unsafe_allow_html=True)
st.markdown("""
<div class="cx-panel">
  <ul style="color: #ffffff;line-height:2.2;font-size:0.80rem;margin:0;padding-left:1.2rem;">
    <li>API keys stored in local <code>.env</code> file — never in source code</li>
    <li><code>.env</code> listed in <code>.gitignore</code> — never committed to version control</li>
    <li>Only last 4 characters displayed in the UI</li>
    <li>All FIRMS API requests made server-side — key never reaches the browser</li>
    <li>No API keys in reports, logs, or database records</li>
  </ul>
  <div style="margin-top:14px;padding:10px 14px;background:rgba(255,255,255,0.03);
              border-radius:8px;border:1px solid rgba(255,255,255,0.06);">
    <p style="margin:0;color: #ffffff;font-size:0.70rem;font-family:'JetBrains Mono',monospace;">
      For cloud deployment: set <code>NASA_API_KEY</code> as a platform secret (Render, Railway, Heroku, etc.)
      rather than using the .env file.
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(footer(), unsafe_allow_html=True)
