# CELESTIAL X 🛰️🔥
### Space-Grade Satellite Fire Intelligence & Spatiotemporal Event Harmonization
**NASA Space Apps Challenge 2026** • *Challenge: Burning Activity Calendar & Hotspot Harmonization*

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NASA FIRMS](https://img.shields.io/badge/Data-NASA%20FIRMS-red.svg)](https://firms.modaps.eosdis.nasa.gov/)

---

## 🌍 The Challenge: MODIS–VIIRS Hotspot Harmonization

Earth Observation (EO) satellites have monitored active fire hotspots across the globe for over two decades. However, **MODIS** sensors (onboard Terra & Aqua, 1 km spatial resolution) are approaching their operational end-of-life and are being succeeded by **VIIRS** sensors (onboard Suomi-NPP, NOAA-20, NOAA-21, 375 m spatial resolution).

Because VIIRS has:
1. **$7.1\times$ smaller nadir pixel area** ($0.14\text{ km}^2$ vs. $1.0\text{ km}^2$),
2. **Sub-pixel sensitivity** detecting fires as small as $10\text{--}20\text{ m}^2$,
3. **An empirical $3.82\times$ higher hotspot detection rate** in coincident scenes,

> ⚠️ **Directly combining raw MODIS and VIIRS records creates an artificial +280% surge in fire counts post-2012.**  
> Without scientific harmonization, historical fire comparisons, multi-year median baselines, and trend analyses become invalid.

**CELESTIAL X** solves this challenge by delivering a scientifically grounded **Harmonized Burning Activity Calendar** and the **FIRE-FUSE** spatiotemporal reconciliation engine.

---

## 🚀 Key Modules & Capabilities

```
CELESTIAL X Platform
├── 📅 BURNING CALENDAR     • 2000–2026 Multi-Decade Heatmaps, Anomaly %, Percentiles & CSV Export
├── 🔬 CALIBRATION LAB     • Cross-Sensor Calibration, Before/After Consistency & FIRE-FUSE Traceability
├── 🗺️ LIVE SATELLITE MAP  • 3D Interactive Hotspot Map (FRP, Day/Night, Sensor Layers)
├── 🔥 FIRE EVENTS         • Persistent Event Tracking, Lifecycle & Intensity Evolution Curves
├── 🤖 COPILOT             • Data-Grounded AI Assistant with Verifiable SQL Queries (No Hallucinations)
├── 🛰️ COVERAGE INTEL      • Orbital Pass Availability Timelines & Coverage-Adjusted Activity Indicators
├── 🔥 SEASON REGIMES      • Automated Fire Season Onset, Peak, Cessation, and Arrival Shifts
├── 🌿 PROTECTED AREAS     • Inside vs. 10 km Buffer Geofencing for Conservation Hotspots (e.g. Mudumalai)
├── 🌡️ ENVIRONMENTAL CONTEXT• Temperature, Humidity, Wind Velocity, and Fine Fuel Dryness Integration
├── 📄 REPORTS & BRIEFS    • Automated Situation Briefings for Command Teams & PDF/MD Event Audits
└── 📥 DATA ENGINE         • Live NASA FIRMS API Pipeline + SQLite Immutable Provenance Store
```

---

## 🔬 Scientific Methodology: FIRE-FUSE

```mermaid
flowchart TD
    A[NASA FIRMS Raw Stream<br>MODIS Terra/Aqua + VIIRS SNPP/NOAA] --> B[Data Ingestion Engine]
    B --> C[(Immutable Raw Observations)]
    C --> D[Sensor Bias Calibration Engine]
    D -->|Confidence Normalization [0,1]<br>Empirical Sensitivity Scaling (3.82x)<br>Uber H3 Res-7 & Res-8 Indexing| E[(Harmonized Hotspots)]
    E --> F[FIRE-FUSE Spatiotemporal Fusion]
    F -->|Stage 1: H3 Hexagonal Candidate Lookup<br>Stage 2: Haversine <= 15 km & Delta t <= 36 hrs| G[(Persistent Fire Events)]
    E --> H[Climatological Baseline Engine]
    H -->|20-Year Monthly Medians & Percentile Ranks| I[Harmonized Burning Calendar]
    G --> J[Decision Support & Emergency Dashboards]
    I --> J
```

### 1. Dual-Resolution Spatial Indexing
* **Uber H3 Resolution 8** (~460 m edge): Pixel-level spatial deduplication across overlapping orbital swaths.
* **Uber H3 Resolution 7** (~5.16 km edge): Candidate event clustering, eliminating $O(N^2)$ pairwise distance calculations.

### 2. Spatiotemporal Fusion Criteria
Observations are merged into persistent multi-day events if and only if:
$$\Delta d_{\text{Haversine}} \le 15.0\text{ km} \quad \text{and} \quad \Delta t \le 36.0\text{ hours}$$
All raw observations, satellite tags, timestamps, and detection confidences remain preserved and auditable.

### 3. Climatological Baseline & Percentile Rankings
To protect against extreme fire seasons distorting multi-year averages:
* Baselines are built on **Historical Monthly Medians** ($\tilde{X}_m$) rather than simple means.
* Anomaly indicators include **Interquartile Ranges ($P_{25}\text{--}P_{75}$)**, **Standardized Z-Scores ($Z = \frac{X - \mu}{\sigma}$)**, and **Historical Percentile Ranks**.

---

## 💻 Quick Start & Local Setup

### Prerequisites
* Python 3.10+
* Git

### Installation
```bash
# Clone the repository
git clone https://github.com/jawahar-data/celestial-x-nasa.git
cd celestial-x-nasa

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py
```

### Configuration
Create a `.env` file in the root directory (optional for live FIRMS API ingestion):
```ini
NASA_API_KEY=your_firms_map_key_here
```
*(Get a free MAP_KEY from [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/))*

---

## 📊 Challenge Deliverables Checklist

- [x] **Harmonized Burning Activity Calendar** (covering 2000 through present)
- [x] **Multi-Year Monthly Medians & Anomaly Comparisons**
- [x] **Downloadable CSV Export** of harmonized active fire hotspots
- [x] **Sensor Bias Calibration Laboratory** (MODIS vs. VIIRS detection rates & FRP distributions)
- [x] **Satellite Observation Coverage Intelligence** (accounting for clouds and orbital gaps)
- [x] **Harmonization Explainability & Traceability Audit**
- [x] **Demonstration Region Profiles**: Tamil Nadu (India), Amazon (Brazil), California (USA), Australia, Mediterranean
- [x] **Interactive Area-of-Interest Selection** (Presets, Bounding Boxes, GeoJSON upload)
- [x] **Accessible Color Ramps** (Viridis, Inferno, Plasma, Cividis)

---

## 🛡️ License & Acknowledgements
Built for the **NASA Space Apps Challenge 2026**.  
Data courtesy of **NASA Earth Science Data and Information System (ESDIS)** / **NASA FIRMS**.
