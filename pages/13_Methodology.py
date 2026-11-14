"""
CELESTIAL X — Scientific Methodology
======================================
Transparent documentation of the harmonization science, algorithms,
statistical methods, and known limitations of the FIRE-FUSE engine.
Includes LaTeX equations rendered via Streamlit's st.latex() (KaTeX).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components

from celestial.styles import ASTRA_ORB_HTML, GLOBAL_CSS, render_nav, footer, section_header

st.set_page_config(
    page_title="CELESTIAL X — Methodology",
    page_icon="📐", layout="wide",
    initial_sidebar_state="collapsed"
)
components.html(ASTRA_ORB_HTML, height=2, scrolling=False)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_nav("METHODOLOGY")

st.markdown("""
<div class="cx-hero" style="padding:50px 3rem 40px;">
  <div class="cx-hero-badge"><span class="cx-hero-badge-dot"></span>
    SCIENTIFIC METHODOLOGY — FIRE-FUSE HARMONIZATION ENGINE
  </div>
  <div class="cx-hero-title" style="font-size:clamp(2rem,4vw,3.2rem);">METHODOLOGY</div>
  <p class="cx-hero-sub-title">Transparent documentation of harmonization science, algorithms, and statistical methods</p>
</div>
<div class="cx-divider"></div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SECTION 1: THE HARMONIZATION PROBLEM
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("🔭", "1. THE HARMONIZATION PROBLEM"), unsafe_allow_html=True)
st.markdown("""
**MODIS** (Terra/Aqua, 2000–present) and **VIIRS** (Suomi NPP/NOAA-20/NOAA-21, 2012–present) have
fundamentally different spatial resolutions, scan geometries, and thermal sensitivity profiles.

A direct numerical comparison of raw hotspot counts produces **misleading historical trends** because:
- VIIRS resolves fires at 375 m vs MODIS at 1 km — a spatial area ratio of approximately **7.1×**
- VIIRS detects smaller, cooler fires that MODIS misses (higher sensitivity in MIR band)
- Different equatorial crossing times produce different diurnal fire detection windows

The FIRE-FUSE engine harmonizes both records into a single consistent schema before analysis.
""")
st.markdown(section_header("📐", "Resolution Area Ratio"), unsafe_allow_html=True)
st.latex(r"""
R_{area} = \left(\frac{d_{MODIS}}{d_{VIIRS}}\right)^2 = \left(\frac{1000\text{ m}}{375\text{ m}}\right)^2 \approx 7.11
""")
st.markdown("*Each MODIS pixel covers ~7.1× more area than a VIIRS pixel, explaining the higher per-fire detection rate of VIIRS.*")

# ═══════════════════════════════════════════════════════════════
# SECTION 2: CONFIDENCE NORMALIZATION
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("📊", "2. CONFIDENCE NORMALIZATION"), unsafe_allow_html=True)
st.markdown("""
Both sensors report fire detection confidence using different scales:
- **MODIS**: Integer 0–100 (direct percentage confidence)
- **VIIRS**: Categorical — `low`, `nominal`, `high`

FIRE-FUSE maps both to a normalized **[0.0, 1.0]** confidence scale:
""")
st.latex(r"""
c_{norm} = \begin{cases}
  c_{MODIS} / 100 & \text{if sensor = MODIS} \\
  0.35 & \text{if VIIRS = low} \\
  0.65 & \text{if VIIRS = nominal} \\
  0.95 & \text{if VIIRS = high}
\end{cases}
""")

# ═══════════════════════════════════════════════════════════════
# SECTION 3: SPATIAL INDEXING — H3
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("🌐", "3. SPATIAL INDEXING — UBER H3 DISCRETE GLOBAL GRID"), unsafe_allow_html=True)
st.markdown("""
CELESTIAL X indexes every hotspot into the **Uber H3** discrete global grid system at two resolutions:

| Resolution | Avg Area | Use Case |
|-----------|----------|----------|
| **H3 Res-7** | ~5.16 km² | Regional clustering and cross-sensor matching |
| **H3 Res-8** | ~0.74 km² | Fine-grained event delineation |

H3 cells are hexagonal (not rectangular), providing uniform adjacency — each cell has exactly
6 neighbors at equal distances, eliminating the corner-adjacency ambiguity of rectangular grids.
""")

# ═══════════════════════════════════════════════════════════════
# SECTION 4: FIRE-FUSE ALGORITHM
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("🔥", "4. FIRE-FUSE SPATIOTEMPORAL EVENT RECONCILIATION"), unsafe_allow_html=True)
st.markdown("""
The FIRE-FUSE algorithm groups spatially and temporally proximate hotspots from multiple sensors
into a single **canonical fire event**, eliminating double-counting.
""")
st.markdown("**Haversine Distance Formula** (great-circle distance between two hotspots):")
st.latex(r"""
d = 2R \arcsin\!\left(\sqrt{\sin^2\!\left(\frac{\phi_2 - \phi_1}{2}\right)
    + \cos(\phi_1)\cos(\phi_2)\sin^2\!\left(\frac{\lambda_2 - \lambda_1}{2}\right)}\right)
""")
st.markdown(r"""where $R = 6371$ km, $\phi$ = latitude (radians), $\lambda$ = longitude (radians).

**Event Fusion Criteria:**
- Two hotspots are merged into one event if **both** conditions hold:
""")
st.latex(r"""
d(\text{obs}_i, \text{obs}_j) \leq \delta_{spatial} \quad \text{AND} \quad
|t_i - t_j| \leq \delta_{temporal}
""")
st.markdown(r"""
where $\delta_{spatial} = 1.5$ km (default matching radius) and $\delta_{temporal} = 24$ hours.

**Event Attributes Derived:**
- Canonical centroid (area-weighted mean latitude/longitude)
- Duration (first to last detection timestamp)
- Peak FRP (maximum Fire Radiative Power observed across all merged detections)
- Dominant sensor (sensor contributing most detections)
""")

# ═══════════════════════════════════════════════════════════════
# SECTION 5: CLIMATOLOGICAL BASELINE
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("📅", "5. CLIMATOLOGICAL BASELINE & ANOMALY DETECTION"), unsafe_allow_html=True)
st.markdown("""
**Why Median, Not Mean?** Fire distributions are right-skewed (a few extreme fire years pull the mean upward).
The **historical median** is robust to outliers and better represents a "typical" fire month.
""")
st.markdown("**Standardized Anomaly Score (Z-score):**")
st.latex(r"""
Z_{m,y} = \frac{H_{m,y} - \tilde{H}_m}{\sigma_m}
""")
st.markdown(r"""
where $H_{m,y}$ = hotspot count in month $m$, year $y$; $\tilde{H}_m$ = historical median for month $m$;
$\sigma_m$ = historical standard deviation for month $m$.

**Historical Percentile Rank:**
""")
st.latex(r"""
P_{rank}(H_{m,y}) = \frac{|\{H_{m,k} : H_{m,k} \leq H_{m,y}, k \in \text{baseline years}\}|}{N_{baseline}} \times 100\%
""")
st.markdown("*A value of 92nd percentile means the month had more fire activity than 92% of historical observations.*")

# ═══════════════════════════════════════════════════════════════
# SECTION 6: FIRE ACTIVITY INDEX
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("⚡", "6. FIRE ACTIVITY INDEX (FAI)"), unsafe_allow_html=True)
st.markdown("""
The **Fire Activity Index** combines hotspot count and Fire Radiative Power into a single composite score:
""")
st.latex(r"""
FAI = w_1 \cdot \frac{H}{\tilde{H}} + w_2 \cdot \frac{\overline{FRP}}{\overline{FRP}_{baseline}}
""")
st.latex(r"""
w_1 = 0.6, \quad w_2 = 0.4
""")
st.markdown(r"""
where $H$ = current hotspot count, $\tilde{H}$ = historical median hotspot count,
$\overline{FRP}$ = current average FRP, $\overline{FRP}_{baseline}$ = baseline average FRP.

FAI > 1.5 indicates significantly elevated fire activity. FAI > 2.0 indicates an extreme fire event.

> **Disclaimer:** FAI is a project-defined analytical indicator developed for the NASA Space Apps
Challenge. It is **not** a scientifically validated forecast and should not be used as the sole basis
for emergency response decisions.
""")

# ═══════════════════════════════════════════════════════════════
# SECTION 7: COVERAGE ADJUSTMENT
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("🛰️", "7. SATELLITE COVERAGE ADJUSTMENT"), unsafe_allow_html=True)
st.markdown("""
When observation days are missing (cloud cover, orbital gaps, sensor downtime), the raw hotspot count
is an **underestimate**. CELESTIAL X applies a coverage adjustment:
""")
st.latex(r"""
H_{adj} = H_{obs} \times \frac{D_{total}}{D_{observed}}
""")
st.markdown(r"""
where $H_{obs}$ = observed hotspot count, $D_{total}$ = total days in period,
$D_{observed}$ = days with valid satellite observations.

> **Note:** This adjustment is applied only when $D_{observed} / D_{total} < 0.85$ (less than 85% coverage).
When coverage is high, $H_{adj} \approx H_{obs}$.
""")

# ═══════════════════════════════════════════════════════════════
# SECTION 8: KNOWN LIMITATIONS
# ═══════════════════════════════════════════════════════════════
st.markdown(section_header("⚠️", "8. KNOWN LIMITATIONS & TRANSPARENCY"), unsafe_allow_html=True)
st.markdown("""
Scientific transparency is a core principle of CELESTIAL X. The following limitations apply:

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| **Demo data when DB is empty** | Synthetic Tamil Nadu-pattern data, not real NASA observations | Clearly labeled; app ingests real data when API key is configured |
| **MODIS sensor degradation** | Terra MODIS Band 21/22 degradation since ~2018 may reduce detection sensitivity | VIIRS continuity sensors provide primary post-2018 record |
| **Cloud cover gaps** | Monsoonal cloud decks (June–September in TN) suppress hotspot detection | Coverage adjustment applied; observation completeness shown |
| **Prescribed burns vs wildfires** | FIRMS does not distinguish fire types | Agricultural burning calendar cross-referenced in season module |
| **H3 boundary effects** | Fires near H3 cell edges may be split across two cells | Res-8 grid uses overlapping buffers to minimize edge artifacts |
| **FAI weights** | The 0.6/0.4 FRP/count weighting is empirically set, not scientifically validated | Weights are configurable; labeled as project-defined |
| **FRP calibration** | MODIS and VIIRS FRP are not directly comparable | FRP harmonization uses empirical calibration ratio (~3.82× VIIRS/MODIS) |

**Data Sources:**
- NASA FIRMS (Fire Information for Resource Management System)
- MODIS MCD14ML Collection 6 — Active Fire Product
- VIIRS VNP14IMGTDL_NRT — 375m Active Fire Product
- NASA Earthdata API (live ingestion when API key is configured)
""")

st.markdown(footer(), unsafe_allow_html=True)

