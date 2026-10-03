"""
CELESTIAL X — Report Generation Module
========================================
Automatically generates a structured Markdown report when a fire event
transitions to CLOSED status. Reports are stored in the reports table
and can be viewed/downloaded from the Reports page.

Important: Reports use careful, scientifically cautious language.
No fire cause is claimed unless causal evidence exists.
Environmental conditions are labeled as "associated" or "observed,"
not as definitive causes.
"""

from datetime import datetime, timezone
from typing import Optional
import io

from .database import get_connection
from .risk import compute_risk_score


def _now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def generate_pdf_report(event_id: str) -> Optional[bytes]:
    """
    Generate a professional PDF incident report for a given event_id.
    Returns the PDF as bytes, or None if the event was not found.
    Uses legacy fpdf (1.7.2) because fpdf2 DLLs are blocked on this system.
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

    score, level = compute_risk_score(event)

    dur_hrs = event.get("duration_hours")
    if dur_hrs:
        dur_str = f"{int(dur_hrs // 24)}d {int(dur_hrs % 24)}h"
    else:
        dur_str = "Unknown"

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

    # ── Colour helpers ─────────────────────────────────────────────────────────
    BLACK  = (0, 0, 0)
    WHITE  = (255, 255, 255)
    L_GREY = (245, 245, 245)
    D_GREY = (230, 230, 230)
    ACCENT = (220, 235, 245) # light blue/cyan tint for headers

    def set_font_safe(style="", size=10):
        pdf.set_font("Helvetica", style=style, size=size)

    # ── Header band ────────────────────────────────────────────────────────────
    pdf.set_fill_color(*L_GREY)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_text_color(*BLACK)
    set_font_safe("B", 18)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "CELESTIAL X", ln=1)
    set_font_safe("", 7)
    pdf.set_x(10)
    pdf.cell(0, 5, "SATELLITE FIRE INTELLIGENCE & SPATIOTEMPORAL EVENT HARMONIZATION", ln=1)
    pdf.set_x(10)
    set_font_safe("", 6)
    pdf.cell(0, 5, f"Report generated: {_now()}   |   NASA Space Apps Challenge 2026", ln=1)
    pdf.ln(8)

    # ── Title ──────────────────────────────────────────────────────────────────
    pdf.set_text_color(*BLACK)
    set_font_safe("B", 15)
    pdf.cell(0, 10, f"FIRE EVENT REPORT - {event_id}", ln=1)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    pdf.set_fill_color(*L_GREY)
    set_font_safe("I", 7)
    pdf.set_x(10)
    pdf.multi_cell(
        190, 4,
        "DISCLAIMER: This report is auto-generated from NASA FIRMS satellite observations. "
        "No fire causation is claimed. The CELESTIAL-X-RISK-v1 score is a project-defined "
        "analytical indicator, not a nationally recognised fire danger rating.",
        fill=True
    )
    pdf.ln(5)

    # Helper: section title
    def section_title(txt):
        pdf.set_fill_color(*D_GREY)
        pdf.set_text_color(*BLACK)
        set_font_safe("B", 9)
        pdf.cell(0, 7, f"  {txt}", ln=1, fill=True)
        pdf.ln(1)

    # Helper: two-column key/value row
    def kv(key, val, alt=False):
        pdf.set_fill_color(*(L_GREY if alt else WHITE))
        pdf.set_text_color(*BLACK)
        set_font_safe("B", 8)
        pdf.cell(65, 6, f"  {key}", fill=True)
        set_font_safe("", 8)
        # Using ln=1 to go to the next line
        pdf.cell(125, 6, str(val), ln=1, fill=True)

    # ── Event Summary ──────────────────────────────────────────────────────────
    section_title("EVENT SUMMARY")
    kv("Event ID",        event_id)
    kv("Status",          event.get("status", "CLOSED"), alt=True)
    kv("Risk Level",      f"{level}  (score: {score:.3f}/1.000)")
    kv("Region",          event.get("region") or "Not specified", alt=True)
    pdf.ln(4)

    # ── Temporal Info ──────────────────────────────────────────────────────────
    section_title("TEMPORAL INFORMATION")
    kv("Start Time",      event.get("start_time", "Unknown"))
    kv("Last Observed",   event.get("last_observed_time", "Unknown"), alt=True)
    kv("Duration",        dur_str)
    pdf.ln(4)

    # ── Location ───────────────────────────────────────────────────────────────
    section_title("LOCATION")
    kv("Centroid Lat",    event.get("centroid_lat", "Unknown"))
    kv("Centroid Lon",    event.get("centroid_lon", "Unknown"), alt=True)
    kv("Bounding Box",
       f"W:{event.get('bbox_west','?')} S:{event.get('bbox_south','?')} "
       f"E:{event.get('bbox_east','?')} N:{event.get('bbox_north','?')}")
    pdf.ln(4)

    # ── Satellite Observations ─────────────────────────────────────────────────
    section_title("SATELLITE OBSERVATIONS")
    kv("Sources",         sat_str)
    kv("Total Obs",       event.get("observation_count", 0), alt=True)
    kv("MODIS Obs",       event.get("modis_count", 0))
    kv("VIIRS Obs",       event.get("viirs_count", 0), alt=True)
    kv("H3 Cells (res 7)",h3_count)
    pdf.ln(4)

    # ── FRP ────────────────────────────────────────────────────────────────────
    section_title("FIRE RADIATIVE POWER (FRP)")
    kv("Peak FRP",        f"{round(event.get('peak_frp') or 0, 1)} MW")
    kv("Mean FRP",        f"{round(event.get('mean_frp') or 0, 1)} MW", alt=True)
    kv("Total FRP",       f"{round(event.get('total_frp') or 0, 1)} MW")
    pdf.ln(4)

    # ── Observation Timeline table ─────────────────────────────────────────────
    if timeline_rows:
        section_title("OBSERVATION TIMELINE")
        # Header row
        pdf.set_fill_color(*D_GREY)
        pdf.set_text_color(*BLACK)
        set_font_safe("B", 7)
        for hdr, w in [("Date", 32), ("Satellite", 48), ("Obs", 20), ("Avg FRP (MW)", 40), ("Max FRP (MW)", 40)]:
            pdf.cell(w, 6, hdr, fill=True, border=0)
        pdf.ln()
        # Data rows
        for i, tr in enumerate(timeline_rows):
            pdf.set_fill_color(*(L_GREY if i % 2 else WHITE))
            pdf.set_text_color(*BLACK)
            set_font_safe("", 7)
            pdf.cell(32, 5, str(tr.get("obs_date", "")), fill=True)
            pdf.cell(48, 5, str(tr.get("satellite", "")), fill=True)
            pdf.cell(20, 5, str(tr.get("cnt", "")), fill=True)
            pdf.cell(40, 5, str(round(tr.get("avg_frp") or 0, 1)), fill=True)
            pdf.cell(40, 5, str(round(tr.get("max_frp") or 0, 1)), fill=True)
            pdf.ln()
        pdf.ln(4)

    # ── Risk Methodology ──────────────────────────────────────────────────────
    section_title("RISK INDICATOR  (CELESTIAL-X-RISK-v1)")
    pdf.set_text_color(*BLACK)
    set_font_safe("", 7.5)
    pdf.set_x(10)
    pdf.multi_cell(190, 4.5,
        f"Composite Score: {score:.3f} / 1.000   |   Risk Level: {level}\n"
        "Components:  FRP 40%  |  Duration 25%  |  Spatial 20%  |  Multi-satellite 10%  |  Confidence 5%\n"
        "NOTE: This is a project-defined metric, NOT a nationally validated fire danger rating."
    )
    pdf.ln(4)

    # ── Data Sources ──────────────────────────────────────────────────────────
    section_title("DATA SOURCES")
    pdf.set_text_color(*BLACK)
    set_font_safe("", 7.5)
    pdf.set_x(10)
    pdf.multi_cell(190, 4.5,
        "- NASA FIRMS MODIS Near Real-Time (NRT) fire observations\n"
        "- NASA FIRMS VIIRS SNPP / NOAA-20 NRT fire observations\n"
        "- NASA FIRMS API: https://firms.modaps.eosdis.nasa.gov/"
    )
    pdf.ln(6)

    # ── Footer band ────────────────────────────────────────────────────────────
    pdf.set_fill_color(*L_GREY)
    pdf.set_text_color(*BLACK)
    set_font_safe("", 6)
    pdf.cell(0, 6, f"  CELESTIAL X  |  NASA Space Apps Challenge 2026  |  FIRE-FUSE Engine  |  {_now()}",
             fill=True, ln=1)

    # fpdf legacy output(dest='S') returns a string in Py3 instead of bytes sometimes,
    # let's be careful. bytes(pdf.output(dest='S').encode('latin-1')) is standard.
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

    # Fetch event
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

    # Risk score
    score, level = compute_risk_score(event)

    # Duration
    start_str = event.get("start_time", "Unknown")
    end_str   = event.get("end_time", event.get("last_observed_time", "Unknown"))
    dur_hrs   = event.get("duration_hours")
    if dur_hrs:
        dur_str = f"{int(dur_hrs // 24)} days {int(dur_hrs % 24)} hrs"
    else:
        dur_str = "Unknown"

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

    # ── Build the report Markdown ──────────────────────────────────────────────
    report_md = f"""# CELESTIAL X FIRE EVENT REPORT

---

**Report generated:** {_now()}  
**System:** CELESTIAL X · Satellite Fire Intelligence & Spatiotemporal Event Harmonization  
**Algorithm:** CELESTIAL X FIRE-FUSE (Two-Stage Spatiotemporal Reconciliation)  
**Disclaimer:** This report is generated automatically from satellite observations. 
It describes observed fire activity indicators. Causal attributions (e.g., fire cause, 
wind effects) are not claimed unless supported by verified evidence.

---

## Event Summary

| Field | Value |
|---|---|
| **Event ID** | `{event_id}` |
| **Status** | {event.get("status", "CLOSED")} |
| **Risk Indicator (CELESTIAL-X-RISK-v1)** | {level} ({score:.2f}/1.00) |
| **Region** | {event.get("region") or "Not specified"} |

---

## Temporal Information

| Field | Value |
|---|---|
| **Start Time** | {start_str} |
| **Last Observed** | {event.get("last_observed_time", "Unknown")} |
| **End Time (Closed)** | {end_str} |
| **Total Duration** | {dur_str} |

---

## Location

| Field | Value |
|---|---|
| **Centroid Latitude** | {event.get("centroid_lat", "Unknown")} |
| **Centroid Longitude** | {event.get("centroid_lon", "Unknown")} |
| **Bounding Box (W, S, E, N)** | {event.get("bbox_west","?")} , {event.get("bbox_south","?")} , {event.get("bbox_east","?")} , {event.get("bbox_north","?")} |

---

## Satellite Observations

| Metric | Value |
|---|---|
| **Satellite Sources** | {sat_str} |
| **Total Observations** | {event.get("observation_count", 0)} |
| **MODIS Observations** | {event.get("modis_count", 0)} |
| **VIIRS Observations** | {event.get("viirs_count", 0)} |
| **H3 Cells Covered** | {h3_count} (H3 resolution 7) |
| **Max Confidence** | {round((event.get("max_confidence") or 0) * 100, 1)}% (normalized) |

---

## Fire Radiative Power (FRP)

> FRP is a satellite-derived measure of fire intensity in Megawatts (MW).
> It is an observed indicator, not a complete measure of fire severity.

| Metric | Value |
|---|---|
| **Peak FRP** | {round(event.get("peak_frp") or 0, 1)} MW |
| **Mean FRP** | {round(event.get("mean_frp") or 0, 1)} MW |
| **Total FRP (sum)** | {round(event.get("total_frp") or 0, 1)} MW |

---

## Observation Timeline

{timeline_md}

---

## Risk Indicator (Analytical)

> **IMPORTANT:** The CELESTIAL-X-RISK-v1 indicator is a project-defined analytical 
> metric based entirely on observable satellite data. It is NOT a scientifically 
> validated fire danger rating. For operational fire danger assessment, consult 
> national meteorological and fire management authorities.

| Component | Contribution |
|---|---|
| Fire Radiative Power (40%) | Observed FRP peak and trend |
| Duration (25%) | Length of continuous fire activity |
| Spatial Expansion (20%) | Number of distinct H3 cells affected |
| Satellite Agreement (10%) | Multi-satellite confirmation rate |
| Confidence (5%) | Detection confidence level |

**Composite Score:** {score:.3f} / 1.000  
**Risk Level:** {level}

---

## Observed Environmental Context

> The following are observed satellite indicators. They are described as 
> "associated conditions," not causal factors. Fire causation requires 
> detailed ground-truth investigation beyond the scope of this system.

- Observed peak FRP of **{round(event.get("peak_frp") or 0, 1)} MW** indicates 
  {"high" if (event.get("peak_frp") or 0) > 200 else "moderate" if (event.get("peak_frp") or 0) > 50 else "low"} 
  fire intensity based on satellite-derived radiometry.
- The fire was detected by **{len(sat_sources)}** satellite system(s): {sat_str}.
- Cross-satellite detection by multiple platforms increases observation confidence.

---

## Limitations

1. This report is based solely on NASA FIRMS MODIS and VIIRS satellite data.
2. Satellite detection is limited by cloud cover, overflight timing, and sensor resolution.
3. The FIRE-FUSE algorithm uses configurable spatial/temporal thresholds; 
   results may vary with different threshold choices.
4. No real-time meteorological data (temperature, humidity, wind) has been 
   incorporated — this is documented as a future improvement.
5. Fire causation is NOT determined by this system.
6. The CELESTIAL-X-RISK-v1 indicator is a project-defined analytical tool,
   not a nationally recognized fire danger rating.

---

## Data Sources

- NASA FIRMS MODIS Near Real-Time (NRT) fire observations
- NASA FIRMS VIIRS SNPP / NOAA-20 NRT fire observations
- NASA FIRMS API: https://firms.modaps.eosdis.nasa.gov/

---

*CELESTIAL X · NASA Space Apps Challenge 2026*  
*CELESTIAL X FIRE-FUSE Spatiotemporal Event Reconciliation Engine*  
*Report auto-generated on {_now()}*
"""

    # Store in DB
    title = f"CELESTIAL X Fire Event Report — {event_id}"
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
