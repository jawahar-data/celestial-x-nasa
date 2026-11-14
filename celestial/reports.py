"""
CELESTIAL X 2.0 — Report Generation Module
===========================================
Automatically generates a structured Markdown & PDF incident report when a fire
event transitions to CLOSED status or on-demand from the Reports console.
Integrates:
  1. Spatiotemporal satellite observation timeline (MODIS / VIIRS)
  2. Atmospheric fire weather indicators (Meteomatics / Open-Meteo / Fosberg FFWI)
  3. Microsoft Planetary Computer STAC environmental terrain & protected area proximity
  4. Potential fire spread & downwind exposure screening (CELESTIAL-X-SPREAD-v1)
  5. Scientific 5-pillar composite risk score (CELESTIAL-X-RISK-v2)

Important: Reports use careful, scientifically cautious language.
No fire cause is claimed unless causal evidence exists.
Environmental conditions are labeled as "associated" or "observed,"
not as definitive causes.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import io

from .database import get_connection
from .risk import compute_risk_score, compute_risk_score_v2
from .weather_intelligence import get_event_weather
from .environmental_intelligence import get_event_environmental_context
from .fire_spread import get_latest_spread_assessment


def _now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def generate_pdf_report(event_id: str) -> Optional[bytes]:
    """
    Generate a professional PDF incident report for a given event_id.
    Returns the PDF as bytes, or None if the event was not found.
    Uses legacy fpdf (1.7.2) for maximum cross-platform compatibility.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM fire_events WHERE event_id=?", (event_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    event = dict(row)

    cur.execute("""
        SELECT DATE(ho.timestamp) as obs_date,
               ho.satellite, COUNT(*) as cnt,
               AVG(ho.frp) as avg_frp, MAX(ho.frp) as max_frp
        FROM harmonized_observations ho
        JOIN event_observations eo ON ho.id = eo.obs_id
        WHERE eo.event_id = ?
        GROUP BY DATE(ho.timestamp), ho.satellite
        ORDER BY obs_date
    """, (event_id,))
    timeline_rows = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT COUNT(*) as n FROM event_h3_cells WHERE event_id=?", (event_id,))
    h3_count = cur.fetchone()[0]
    conn.close()

    # Multi-pillar contextual data
    weather = get_event_weather(event_id) or {}
    env = get_event_environmental_context(event_id) or {}
    spread = get_latest_spread_assessment(event_id) or {}
    risk_v2 = compute_risk_score_v2(event, weather, env)

    score = risk_v2["composite_risk_score"]
    level = risk_v2["risk_level"]

    dur_hrs = event.get("duration_hours")
    if dur_hrs is not None:
        dur_str = f"{int(dur_hrs // 24)}d {int(dur_hrs % 24)}h"
    else:
        dur_str = "Ongoing / Active"

    sat_sources = []
    if event.get("modis_count", 0) > 0:
        sat_sources.append("MODIS NRT")
    if event.get("viirs_count", 0) > 0:
        sat_sources.append("VIIRS (SNPP/NOAA-20)")
    sat_str = ", ".join(sat_sources) if sat_sources else "Unknown"

    # ── Build PDF ──────────────────────────────────────────────────────────────
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    BLACK  = (0, 0, 0)
    WHITE  = (255, 255, 255)
    L_GREY = (245, 245, 245)
    D_GREY = (230, 230, 230)

    def set_font_safe(style="", size=10):
        pdf.set_font("Helvetica", style=style, size=size)

    # ── Header band ────────────────────────────────────────────────────────────
    pdf.set_fill_color(*L_GREY)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_text_color(*BLACK)
    set_font_safe("B", 18)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "CELESTIAL X 2.0", ln=1)
    set_font_safe("", 7)
    pdf.set_x(10)
    pdf.cell(0, 5, "SATELLITE WILDFIRE INTELLIGENCE & MULTI-PILLAR ENVIRONMENTAL PLATFORM", ln=1)
    pdf.set_x(10)
    set_font_safe("", 6)
    pdf.cell(0, 5, f"Report generated: {_now()}   |   NASA Space Apps Challenge 2026", ln=1)
    pdf.ln(8)

    # ── Title ──────────────────────────────────────────────────────────────────
    pdf.set_text_color(*BLACK)
    set_font_safe("B", 14)
    pdf.cell(0, 9, f"FIRE INCIDENT INTELLIGENCE REPORT - {event_id}", ln=1)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    pdf.set_fill_color(*L_GREY)
    set_font_safe("I", 7)
    pdf.set_x(10)
    pdf.multi_cell(
        190, 4,
        "DISCLAIMER: Auto-generated from NASA FIRMS satellite observations, Meteomatics/Open-Meteo weather data, "
        "and Microsoft Planetary Computer STAC environmental catalogs. Potential spread paths represent downwind screening corridors "
        "(CELESTIAL-X-SPREAD-v1) and not deterministic physical perimeters. No fire causation is claimed.",
        fill=True
    )
    pdf.ln(4)

    # Helper: section title
    def section_title(txt):
        pdf.set_fill_color(*D_GREY)
        pdf.set_text_color(*BLACK)
        set_font_safe("B", 9)
        pdf.cell(0, 6.5, f"  {txt}", ln=1, fill=True)
        pdf.ln(1)

    # Helper: two-column key/value row
    def kv(key, val, alt=False):
        pdf.set_fill_color(*(L_GREY if alt else WHITE))
        pdf.set_text_color(*BLACK)
        set_font_safe("B", 8)
        pdf.cell(65, 5.5, f"  {key}", fill=True)
        set_font_safe("", 8)
        pdf.cell(125, 5.5, str(val), ln=1, fill=True)

    # ── Event Summary ──────────────────────────────────────────────────────────
    section_title("EVENT SUMMARY & RISK STATUS")
    kv("Event ID",        event_id)
    kv("Status",          event.get("status", "CLOSED"), alt=True)
    kv("Risk Level (v2)", f"{level}  (score: {score:.3f}/1.000)")
    kv("Region",          event.get("region") or "Not specified", alt=True)
    pdf.ln(3)

    # ── Temporal Info ──────────────────────────────────────────────────────────
    section_title("TEMPORAL SPAN")
    kv("Start Time",      event.get("start_time", "Unknown"))
    kv("Last Observed",   event.get("last_observed_time", "Unknown"), alt=True)
    kv("Duration",        dur_str)
    pdf.ln(3)

    # ── Location ───────────────────────────────────────────────────────────────
    section_title("GEOGRAPHIC LOCATION")
    kv("Centroid Lat",    f"{event.get('centroid_lat', 'Unknown')}°N")
    kv("Centroid Lon",    f"{event.get('centroid_lon', 'Unknown')}°E", alt=True)
    kv("Bounding Box",
       f"W:{event.get('bbox_west','?')} S:{event.get('bbox_south','?')} "
       f"E:{event.get('bbox_east','?')} N:{event.get('bbox_north','?')}")
    pdf.ln(3)

    # ── Satellite Observations ─────────────────────────────────────────────────
    section_title("SATELLITE OBSERVATIONS (NASA FIRMS)")
    kv("Sensors",         sat_str)
    kv("Total Obs",       event.get("observation_count", 0), alt=True)
    kv("Peak FRP",        f"{round(event.get('peak_frp') or 0, 1)} MW")
    kv("Mean FRP",        f"{round(event.get('mean_frp') or 0, 1)} MW", alt=True)
    kv("H3 Spatial Cells",f"{h3_count} (Resolution 7)")
    pdf.ln(3)

    # ── Atmospheric Weather ───────────────────────────────────────────────────
    if weather:
        section_title("ATMOSPHERIC FIRE WEATHER (METEOMATICS / OPEN-METEO)")
        kv("Temperature",     f"{weather.get('temp_c', 'N/A')} °C")
        kv("Relative Humidity", f"{weather.get('relative_humidity_pct', 'N/A')}%", alt=True)
        kv("Wind Velocity",   f"{weather.get('wind_speed_kmh', 'N/A')} km/h ({weather.get('wind_cardinal', 'N/A')} · {weather.get('wind_direction_deg', 'N/A')}°)")
        kv("Fosberg FFWI",    f"{weather.get('fosberg_index', 'N/A')}/100", alt=True)
        kv("Data Provenance", f"{weather.get('weather_source', 'N/A')} (Forecast: {weather.get('is_forecast', False)})")
        pdf.ln(3)

    # ── Environmental Context ─────────────────────────────────────────────────
    if env:
        section_title("ENVIRONMENTAL CONTEXT & TOPOGRAPHY (STAC CATALOG)")
        kv("Elevation / Slope", f"{env.get('elevation_m', 'N/A')} m  ·  {env.get('slope_deg', 'N/A')}° ({env.get('aspect_cardinal', 'N/A')})")
        kv("ESA WorldCover",    f"{env.get('landcover_class', 'N/A')} (Flammability: {env.get('fuel_flammability_class', 'N/A')})", alt=True)
        kv("Protected Area",    f"{env.get('nearest_protected_area', 'N/A')} ({env.get('protected_area_distance_km', 'N/A')} km)")
        kv("Sensitivity (ESI)", f"{env.get('environmental_sensitivity_score', 'N/A')}/100", alt=True)
        pdf.ln(3)

    # ── Potential Spread & Exposure ────────────────────────────────────────────
    if spread:
        section_title("POTENTIAL FIRE SPREAD SCREENING (CELESTIAL-X-SPREAD-v1)")
        kv("Downwind Bearing",  f"{spread.get('downwind_cardinal', 'N/A')} ({spread.get('downwind_bearing_deg', 'N/A')}°)")
        kv("Rate of Spread",    f"{spread.get('rate_of_spread_kmh', 'N/A')} km/h (screening proxy)", alt=True)
        kv("24h Exposure",      f"Up to {spread.get('exposure_radius_24h_km', 'N/A')} km downwind")
        kv("Threatened Assets", f"{spread.get('threatened_assets', 'None identified')}", alt=True)
        pdf.ln(3)

    # ── Risk Methodology ──────────────────────────────────────────────────────
    section_title("RISK INDICATOR  (CELESTIAL-X-RISK-v2)")
    pdf.set_text_color(*BLACK)
    set_font_safe("", 7.5)
    pdf.set_x(10)
    pdf.multi_cell(190, 4.5,
        f"Composite Score: {score:.3f} / 1.000   |   Risk Level: {level}\n"
        "5-Pillar Model:  Thermal FRP (30%)  |  Persistence (20%)  |  Fire Weather Deficit (20%)  |  Fuel/Terrain (15%)  |  Conservation Proximity (15%)\n"
        "NOTE: Project-defined multi-criteria index for Space Apps Challenge, NOT a certified statutory fire danger rating."
    )
    pdf.ln(3)

    # ── Footer band ────────────────────────────────────────────────────────────
    pdf.set_fill_color(*L_GREY)
    pdf.set_text_color(*BLACK)
    set_font_safe("", 6)
    pdf.cell(0, 6, f"  CELESTIAL X 2.0  |  NASA Space Apps Challenge 2026  |  FIRE-FUSE Engine  |  {_now()}",
             fill=True, ln=1)

    return bytes(pdf.output(dest='S').encode('latin-1'))


def generate_event_report(event_id: str, log_fn=None) -> Optional[str]:
    """
    Generate a final CELESTIAL X Fire Event Report in Markdown format.
    Stores the result in the reports table.
    Returns the Markdown string, or None if the event was not found.
    """
    def log(msg):
        if log_fn:
            log_fn(msg)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM fire_events WHERE event_id=?", (event_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    event = dict(row)

    # Fetch timeline
    cur.execute("""
        SELECT DATE(ho.timestamp) as obs_date,
               ho.satellite, COUNT(*) as cnt,
               AVG(ho.frp) as avg_frp, MAX(ho.frp) as max_frp
        FROM harmonized_observations ho
        JOIN event_observations eo ON ho.id = eo.obs_id
        WHERE eo.event_id = ?
        GROUP BY DATE(ho.timestamp), ho.satellite
        ORDER BY obs_date
    """, (event_id,))
    timeline_rows = [dict(r) for r in cur.fetchall()]

    # Fetch H3 cells
    cur.execute("SELECT COUNT(*) as n FROM event_h3_cells WHERE event_id=?", (event_id,))
    h3_count = cur.fetchone()[0]

    # Contextual modules
    weather = get_event_weather(event_id) or {}
    env = get_event_environmental_context(event_id) or {}
    spread = get_latest_spread_assessment(event_id) or {}
    risk_v2 = compute_risk_score_v2(event, weather, env)

    score = risk_v2["composite_risk_score"]
    level = risk_v2["risk_level"]
    factors = risk_v2["factor_scores"]

    # Duration
    start_str = event.get("start_time", "Unknown")
    end_str   = event.get("end_time", event.get("last_observed_time", "Unknown"))
    dur_hrs   = event.get("duration_hours")
    if dur_hrs is not None:
        dur_str = f"{int(dur_hrs // 24)} days {int(dur_hrs % 24)} hrs ({dur_hrs:.1f} hrs)"
    else:
        dur_str = "Ongoing / Active"

    # Format timeline table
    if timeline_rows:
        timeline_md = "| Date | Satellite | Observations | Avg FRP (MW) | Max FRP (MW) |\n"
        timeline_md += "|---|---|---|---|---|\n"
        for trow in timeline_rows:
            timeline_md += (
                f"| {trow['obs_date']} | {trow['satellite']} | {trow['cnt']} | "
                f"{round(trow['avg_frp'] or 0, 1)} | {round(trow['max_frp'] or 0, 1)} |\n"
            )
    else:
        timeline_md = "_No observation timeline available._"

    sat_sources = []
    if event.get("modis_count", 0) > 0:
        sat_sources.append("MODIS NRT")
    if event.get("viirs_count", 0) > 0:
        sat_sources.append("VIIRS (SNPP/NOAA-20)")
    sat_str = ", ".join(sat_sources) if sat_sources else "Unknown"

    # Build weather table
    if weather:
        weather_md = f"""
| Metric | Value |
|---|---|
| **Ambient Temperature** | {weather.get('temp_c', 'N/A')} °C |
| **Relative Humidity** | {weather.get('relative_humidity_pct', 'N/A')}% |
| **Wind Speed** | {weather.get('wind_speed_kmh', 'N/A')} km/h |
| **Wind Direction** | {weather.get('wind_cardinal', 'N/A')} ({weather.get('wind_direction_deg', 'N/A')}°) |
| **Fosberg Fire Weather Index (FFWI)** | {weather.get('fosberg_index', 'N/A')} / 100 |
| **Weather Source** | `{weather.get('weather_source', 'N/A')}` ({'Forecast Model' if weather.get('is_forecast') else 'Observed Station/Climatology'}) |
"""
    else:
        weather_md = "_No localized atmospheric weather observations available for this event._"

    # Build environmental context table
    if env:
        env_md = f"""
| Environmental Parameter | Observation |
|---|---|
| **Copernicus DEM Elevation** | {env.get('elevation_m', 'N/A')} m MSL |
| **Terrain Slope & Aspect** | {env.get('slope_deg', 'N/A')}° ({env.get('aspect_cardinal', 'N/A')} aspect) |
| **ESA WorldCover 10m Land Cover** | {env.get('landcover_class', 'N/A')} |
| **Fuel Flammability Class** | {env.get('fuel_flammability_class', 'N/A')} |
| **Nearest Protected Sanctuary** | **{env.get('nearest_protected_area', 'N/A')}** ({env.get('protected_area_distance_km', 'N/A')} km) |
| **Environmental Sensitivity Score (ESI)** | {env.get('environmental_sensitivity_score', 'N/A')} / 100 |
"""
    else:
        env_md = "_No STAC environmental context observations recorded._"

    # Build spread assessment table
    if spread:
        spread_md = f"""
| Spread Screening Metric | Assessment |
|---|---|
| **Downwind Exposure Direction** | **{spread.get('downwind_cardinal', 'N/A')} ({spread.get('downwind_bearing_deg', 'N/A')}°)** |
| **Forward Rate of Spread Proxy** | {spread.get('rate_of_spread_kmh', 'N/A')} km/h |
| **12-Hour Exposure Corridor** | Up to {spread.get('exposure_radius_12h_km', 'N/A')} km |
| **24-Hour Exposure Corridor** | Up to {spread.get('exposure_radius_24h_km', 'N/A')} km |
| **48-Hour Exposure Corridor** | Up to {spread.get('exposure_radius_48h_km', 'N/A')} km |
| **Threatened Ecological Assets** | `{spread.get('threatened_assets', 'None identified')}` |
"""
    else:
        spread_md = "_No potential fire spread assessment logged for this event._"

    # ── Build the complete report Markdown ──────────────────────────────────────
    report_md = f"""# CELESTIAL X 2.0 FIRE INCIDENT REPORT

---

**Report generated:** {_now()}  
**System:** CELESTIAL X 2.0 · Satellite Fire Intelligence & Environmental Platform  
**Algorithm:** CELESTIAL X FIRE-FUSE (Two-Stage Spatiotemporal Reconciliation)  
**Risk Engine:** CELESTIAL-X-RISK-v2 (5-Pillar Explainable Multi-Criteria Index)  
**Exposure Model:** CELESTIAL-X-SPREAD-v1 (Downwind Atmospheric Screening Model)  
**Disclaimer:** This report is synthesized from NASA FIRMS satellite observations, Meteomatics/Open-Meteo weather data, 
and Microsoft Planetary Computer STAC catalogs. It describes observed indicators and potential exposure corridors. 
Deterministic perimeters or ignition causation are not claimed.

---

## 1. Event Identification & Status

| Field | Value |
|---|---|
| **Event ID** | `{event_id}` |
| **Status** | {event.get("status", "CLOSED")} |
| **Composite Risk (v2)** | **{level}** ({score:.3f} / 1.000) |
| **Region** | {event.get("region") or "Western Ghats / Tamil Nadu"} |

---

## 2. Spatiotemporal Timeline

| Field | Value |
|---|---|
| **Start Time** | {start_str} |
| **Last Observed** | {event.get("last_observed_time", "Unknown")} |
| **End Time (Closed)** | {end_str} |
| **Total Duration** | {dur_str} |
| **Centroid Coordinate** | `{event.get("centroid_lat", "Unknown")}°N, {event.get("centroid_lon", "Unknown")}°E` |
| **Bounding Box** | `W:{event.get('bbox_west','?')} S:{event.get('bbox_south','?')} E:{event.get('bbox_east','?')} N:{event.get('bbox_north','?')}` |

---

## 3. Satellite Observations & Radiometry (NASA FIRMS)

| Metric | Value |
|---|---|
| **Satellite Sources** | {sat_str} |
| **Total Observations** | {event.get("observation_count", 0)} |
| **MODIS Observations** | {event.get("modis_count", 0)} |
| **VIIRS Observations** | {event.get("viirs_count", 0)} |
| **H3 Cells Covered** | {h3_count} (H3 resolution 7) |
| **Max Normalized Confidence** | {round((event.get("max_confidence") or 0) * 100, 1)}% |
| **Peak FRP** | {round(event.get("peak_frp") or 0, 1)} MW |
| **Mean FRP** | {round(event.get("mean_frp") or 0, 1)} MW |
| **Total FRP (sum)** | {round(event.get("total_frp") or 0, 1)} MW |

---

## 4. Atmospheric Fire Weather Context
{weather_md}

---

## 5. Environmental STAC & Topographic Context
{env_md}

---

## 6. Potential Fire Spread & Downwind Exposure Screening (v1)
{spread_md}

---

## 7. Observation Timeline

{timeline_md}

---

## 8. Scientific Risk Score Breakdown (CELESTIAL-X-RISK-v2)

| Pillar | Weight | Sub-score (0-1) | Weighted Contribution |
|---|---|---|---|
| **Thermal Intensity (Peak FRP)** | 30% | {factors.get('thermal_intensity', 0):.3f} | {factors.get('thermal_intensity', 0)*0.30:.3f} |
| **Persistence & Duration** | 20% | {factors.get('duration_persistence', 0):.3f} | {factors.get('duration_persistence', 0)*0.20:.3f} |
| **Atmospheric Fire Weather Deficit** | 20% | {factors.get('weather_deficit', 0):.3f} | {factors.get('weather_deficit', 0)*0.20:.3f} |
| **Fuel & Topographic Alignment** | 15% | {factors.get('fuel_topography', 0):.3f} | {factors.get('fuel_topography', 0)*0.15:.3f} |
| **Conservation & Asset Proximity** | 15% | {factors.get('conservation_proximity', 0):.3f} | {factors.get('conservation_proximity', 0)*0.15:.3f} |
| **Composite Index** | **100%** | — | **{score:.3f} ({level})** |

---

## 9. Limitations & Scientific Cautions

1. **Satellite Coverage:** Orbital revisit intervals and cloud attenuation mean low-intensity understory burns may evade detection.
2. **Screening Exposure:** Downwind cone geometry represents atmospheric screening zones, not physical fire perimeters.
3. **Sensor Cross-Calibration:** VIIRS (375m) detects 3.8x more low-FRP hotspots than MODIS (1km); CELESTIAL X normalizes confidence and spatial footprints.
4. **Causality:** Ignition mechanisms are not determined by satellite observations.

---

## 10. Data Source Provenance

- **NASA FIRMS:** MODIS Terra/Aqua (MOD14 NRT) & VIIRS SNPP/NOAA-20 (VNP14IMG/VJ114IMG NRT)
- **Meteomatics & Open-Meteo API:** Atmospheric reanalysis and numerical weather prediction
- **Microsoft Planetary Computer STAC:** Copernicus GLO-30 DEM & ESA WorldCover 10m
- **Protected Areas:** Wildlife reserves & sanctuaries of the Western Ghats / Nilgiri Biosphere

---

*CELESTIAL X 2.0 · NASA Space Apps Challenge 2026*  
*Report auto-generated on {_now()}*
"""

    # Store in DB
    title = f"CELESTIAL X 2.0 Fire Incident Report — {event_id}"
    cur.execute("""
        INSERT OR REPLACE INTO reports (event_id, report_type, title, content_md)
        VALUES (?,?,?,?)
    """, (event_id, "FINAL", title, report_md))
    cur.execute(
        "UPDATE fire_events SET report_status='GENERATED' WHERE event_id=?",
        (event_id,)
    )
    conn.commit()
    conn.close()
    log(f"✓ Report generated for event {event_id}")
    return report_md


def generate_pending_reports(log_fn=None) -> int:
    """Generate reports for all CLOSED events that don't yet have a report."""
    def log(msg):
        if log_fn:
            log_fn(msg)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT event_id FROM fire_events
        WHERE status='CLOSED' AND report_status='PENDING'
    """)
    pending = [r[0] for r in cur.fetchall()]
    conn.close()

    generated = 0
    for event_id in pending:
        result = generate_event_report(event_id, log_fn)
        if result:
            generated += 1
    if generated:
        log(f"✓ Auto-generated {generated} pending report(s)")
    return generated


def get_all_reports() -> list[dict]:
    """Return all reports as a list of dicts for the Reports page."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.event_id, r.report_type, r.title, r.generated_at,
               fe.status, fe.risk_level, fe.duration_hours,
               fe.centroid_lat, fe.centroid_lon,
               fe.observation_count, fe.peak_frp
        FROM reports r
        JOIN fire_events fe ON r.event_id = fe.event_id
        ORDER BY r.generated_at DESC
    """)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_report_content(event_id: str) -> Optional[str]:
    """Return the Markdown content of a report for a given event_id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT content_md FROM reports WHERE event_id=?", (event_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
