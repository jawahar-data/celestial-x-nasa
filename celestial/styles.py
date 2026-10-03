"""
CELESTIAL X — Premium Design System
=====================================
Ultra-premium NASA-grade UI: cinematic dark space aesthetic,
multi-layer glassmorphism, advanced particle galaxy, satellite maps.
"""

# ─────────────────────────────────────────────────────────────────────────────
# ASTRA GALAXY BACKGROUND — Enhanced Three.js (galaxy arms, nebula, mouse tilt)
# ─────────────────────────────────────────────────────────────────────────────
_ORB_CSS = (
    "<style>"
    "*{margin:0;padding:0;box-sizing:border-box;}"
    "html,body{width:100%;height:100%;overflow:hidden;background:radial-gradient(ellipse at 50% 40%,#040b16 0%,#010206 50%,#000000 100%);}"
    "canvas{display:block;position:fixed;top:0;left:0;}"
    "</style>"
)

_ORB_EXPAND_JS = """
(function(){
  var el=window.frameElement; if(!el) return;
  function fix(){
    el.style.cssText='position:fixed!important;top:0!important;left:0!important;width:100vw!important;height:100vh!important;z-index:0!important;pointer-events:none!important;border:none!important;background:transparent!important;border-radius:0!important;';
  }
  fix(); setInterval(fix,200);
  try{
    var id='cxbg2';
    var old=window.parent.document.getElementById(id); if(old)old.remove();
    var s=window.parent.document.createElement('style'); s.id=id;
    s.textContent=
      'html,body{background:#000!important;}'+
      '.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stApp"],'+
      '[data-testid="stVerticalBlock"],[data-testid="stAppViewBlockContainer"]'+
      '{background:transparent!important;}'+
      '[data-testid="stHeader"],[data-testid="stDecoration"],[data-testid="stToolbar"],'+
      'header,[data-testid="stStatusWidget"],.stDeployButton,#MainMenu'+
      '{display:none!important;opacity:0!important;height:0!important;}';
    window.parent.document.head.appendChild(s);
  }catch(e){}
})();
"""

ASTRA_ORB_HTML = (
    "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
    "</head><body>"
    "<script>" + _ORB_EXPAND_JS + "</script>"
    "</body></html>"
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — $10K Premium Design System
# ─────────────────────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ══════════════════════════════════════════════════════════
   RESET & BASE
═══════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  background: radial-gradient(ellipse at 50% 30%, #050a1a 0%, #010208 55%, #000 100%) !important;
  font-family: 'Inter', system-ui, sans-serif;
  color: #ffffff;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ══════════════════════════════════════════════════════════
   STREAMLIT CHROME — TOTAL SUPPRESSION
═══════════════════════════════════════════════════════════ */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
[data-testid="stVerticalBlock"],
[data-testid="stAppViewBlockContainer"] {
  background: transparent !important;
  border-radius: 0 !important;
}
html, body {
  background: #000 url('data:image/png;base64,{_bg_b64}') no-repeat center center fixed !important;
  background-size: cover !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  box-shadow: none !important;
}
[data-testid="stHeader"],
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
header, .stDeployButton, #MainMenu,
[data-testid="manage-app-button"] {
  display: none !important;
  opacity: 0 !important;
  height: 0 !important;
  pointer-events: none !important;
}
[data-testid="stMain"], [data-testid="block-container"], .main {
  position: relative !important;
  z-index: 10 !important;
  background: transparent !important;
}
.main .block-container,
[data-testid="stMainBlockContainer"],
[data-testid="block-container"] {
  padding-top: 0 !important;
  padding-left: 2.5rem !important;
  padding-right: 2.5rem !important;
  padding-bottom: 4rem !important;
  max-width: 100% !important;
}

/* Glassmorphism for Maps & DataFrames */
[data-testid="stDeckGlJsonChart"],
[data-testid="stDataFrame"] {
  background: rgba(255, 255, 255, 0.02) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 14px !important;
  padding: 12px !important;
  overflow: hidden !important;
}
[data-testid="stDeckGlJsonChart"] iframe {
  border-radius: 8px !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* ══════════════════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.18); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.35); }

/* ══════════════════════════════════════════════════════════
   NAV BAR — Mission Control Grade
═══════════════════════════════════════════════════════════ */
.cx-nav {
  position: sticky;
  top: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2.5rem;
  height: 68px;
  background: rgba(1,2,10,0.88);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  backdrop-filter: blur(48px) saturate(180%);
  -webkit-backdrop-filter: blur(48px) saturate(180%);
  box-shadow:
    0 1px 0 rgba(255,255,255,0.06),
    0 24px 64px rgba(0,0,0,0.8);
}
.cx-brand { display: flex; align-items: center; gap: 14px; }
.cx-logo {
  font-size: 1.75rem;
  filter: drop-shadow(0 0 16px rgba(120,180,255,0.8)) drop-shadow(0 0 40px rgba(80,140,255,0.4));
  animation: logoFloat 8s ease-in-out infinite;
}
.cx-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem;
  font-weight: 900;
  color: #ffffff;
  letter-spacing: 3px;
  line-height: 1;
  text-shadow: 0 0 30px rgba(150,200,255,0.5);
}
.cx-title span {
  display: block;
  font-size: 0.42rem;
  font-weight: 400;
  color: #ffffff;
  letter-spacing: 3.5px;
  text-transform: uppercase;
  margin-top: 4px;
  font-family: 'Inter', sans-serif;
}
.cx-nav-links { display: flex; gap: 1px; }
.cx-nav-link {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.54rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.8px;
  color: #ffffff;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.25s ease;
  cursor: default;
  white-space: nowrap;
}
.cx-nav-link:hover {
  color: #ffffff;
  background: rgba(255,255,255,0.05);
  border-color: #ffffff;
}
.cx-nav-link.active {
  color: #ffffff;
  background: rgba(255,255,255,0.08);
  border-color: #ffffff;
  box-shadow: 0 0 20px rgba(255,255,255,0.06), inset 0 0 12px rgba(255,255,255,0.03);
}
.cx-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.60rem;
  color: #ffffff;
  letter-spacing: 0.5px;
}
.cx-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34,197,94,0.9), 0 0 20px rgba(34,197,94,0.4);
  animation: blink 2.5s ease-in-out infinite;
}

/* ══════════════════════════════════════════════════════════
   HERO SECTION
═══════════════════════════════════════════════════════════ */
.cx-hero {
  position: relative;
  text-align: center;
  padding: 80px 3rem 64px;
  overflow: hidden;
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: none !important;
  border-radius: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
}

/* Force Glassmorphism on Nav Bar bypassing Python cache */
div[style*="position:sticky"], 
div[style*="position: sticky"] {
  background: rgba(255, 255, 255, 0.02) !important;
  backdrop-filter: blur(12px) saturate(150%) !important;
  -webkit-backdrop-filter: blur(12px) saturate(150%) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Force Nav Subtitle opacity bypass */
div[style*="font-size:0.5rem"][style*="text-transform:uppercase"] {
  opacity: 1.0 !important;
}

.cx-hero::before {
  content: '';
  position: absolute;
  top: -200px; left: 50%; transform: translateX(-50%);
  width: 900px; height: 600px; border-radius: 50%;
  background: radial-gradient(ellipse, rgba(80,120,255,0.08) 0%, transparent 65%);
  pointer-events: none;
  animation: heroGlow 10s ease-in-out infinite;
}
.cx-hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 100px;
  padding: 8px 24px;
  color: #ffffff;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.56rem;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 32px;
  backdrop-filter: blur(16px);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.04), 0 8px 32px rgba(0,0,0,0.4);
}
.cx-hero-badge-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34,197,94,0.8);
  animation: blink 2s ease-in-out infinite;
}
.cx-hero-title {
  font-family: 'Orbitron', sans-serif;
  font-size: clamp(3rem, 6vw, 5.5rem);
  font-weight: 900;
  color: #ffffff;
  letter-spacing: 8px;
  line-height: 1;
  margin-bottom: 10px;
  text-shadow:
    0 0 80px rgba(100,160,255,0.35),
    0 0 160px rgba(80,140,255,0.15),
    0 4px 40px rgba(0,0,0,0.9);
  position: relative;
}
.cx-hero-title::after {
  content: 'CELESTIAL X';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(100,160,255,0.15) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  pointer-events: none;
}
.cx-hero-sub-title {
  font-family: 'Inter', sans-serif;
  font-size: 0.78rem;
  font-weight: 400;
  color: #ffffff;
  letter-spacing: 5px;
  text-transform: uppercase;
  margin-bottom: 28px;
  text-shadow: 0 2px 10px rgba(0,0,0,1.0), 0 4px 20px rgba(0,0,0,0.8);
}
.cx-hero-desc {
  color: #ffffff;
  font-size: 1.02rem;
  line-height: 1.9;
  max-width: 680px;
  margin: 0 auto 40px;
  font-weight: 300;
  text-align: center !important;
  text-shadow: 0 2px 10px rgba(0,0,0,1.0), 0 4px 20px rgba(0,0,0,0.8);
}
.cx-hero-desc strong { color: #ffffff; font-weight: 600; }
.cx-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.cx-tag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  color: #ffffff;
  border-radius: 100px;
  padding: 6px 16px;
  font-size: 0.65rem;
  font-weight: 500;
  letter-spacing: 0.5px;
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
}
.cx-tag:hover {
  border-color: #ffffff;
  color: #ffffff;
  background: rgba(255,255,255,0.07);
}
.cx-tag .dot { width: 5px; height: 5px; border-radius: 50%; display: inline-block; }

/* ══════════════════════════════════════════════════════════
   DIVIDER
═══════════════════════════════════════════════════════════ */
.cx-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 30%, rgba(255,255,255,0.08) 70%, transparent 100%);
  margin: 0 2rem 0;
}

/* ══════════════════════════════════════════════════════════
   SECTION HEADERS
═══════════════════════════════════════════════════════════ */
.cx-shdr {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 36px 0 18px;
}
.cx-shdr-icon {
  font-size: 1.2rem;
  width: 40px; height: 40px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.cx-shdr-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.0rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2.5px;
  color: #ffffff;
}
.cx-shdr-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(255,255,255,0.10) 0%, transparent 100%);
}

/* ══════════════════════════════════════════════════════════
   METRIC CARDS — Premium Glass
═══════════════════════════════════════════════════════════ */
.cx-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.cx-card {
  position: relative;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 18px;
  padding: 22px 20px 20px;
  text-align: center;
  backdrop-filter: blur(32px) saturate(160%);
  -webkit-backdrop-filter: blur(32px) saturate(160%);
  overflow: hidden;
  transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}
.cx-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%);
  pointer-events: none;
  border-radius: inherit;
}
.cx-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.25) 50%, transparent 100%);
}
.cx-card:hover {
  transform: translateY(-5px);
  border-color: #ffffff;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.08);
}
/* Color accent top bars */
.cx-card.red::after    { background: linear-gradient(90deg, transparent, rgba(239,68,68,0.9), transparent); }
.cx-card.orange::after { background: linear-gradient(90deg, transparent, rgba(234,88,12,0.9), transparent); }
.cx-card.amber::after  { background: linear-gradient(90deg, transparent, rgba(245,158,11,0.9), transparent); }
.cx-card.green::after  { background: linear-gradient(90deg, transparent, rgba(34,197,94,0.9), transparent); }
.cx-card.blue::after   { background: linear-gradient(90deg, transparent, rgba(59,130,246,0.9), transparent); }
.cx-card.purple::after { background: linear-gradient(90deg, transparent, rgba(139,92,246,0.9), transparent); }
.cx-card.white::after  { background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent); }
/* Glow on hover */
.cx-card.red:hover    { box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(239,68,68,0.1); }
.cx-card.orange:hover { box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(234,88,12,0.1); }
.cx-card.blue:hover   { box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(59,130,246,0.1); }
.cx-card.green:hover  { box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(34,197,94,0.1); }

.cx-card-label {
  font-size: 0.54rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2.5px;
  color: #ffffff;
  margin-bottom: 12px;
  font-family: 'Orbitron', sans-serif;
}
.cx-card-value {
  font-size: 2.6rem;
  font-weight: 900;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
  margin-bottom: 8px;
  letter-spacing: -1px;
}
.cx-card-sub {
  font-size: 0.65rem;
  color: #ffffff;
  font-weight: 400;
  letter-spacing: 0.3px;
}

/* ══════════════════════════════════════════════════════════
   GLASS PANEL
═══════════════════════════════════════════════════════════ */
.cx-panel {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 20px;
  padding: 28px 32px;
  backdrop-filter: blur(40px) saturate(160%);
  -webkit-backdrop-filter: blur(40px) saturate(160%);
  box-shadow: 0 8px 48px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}
.cx-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 50%);
  pointer-events: none;
  border-radius: inherit;
}

/* ══════════════════════════════════════════════════════════
   TERMINAL LOG
═══════════════════════════════════════════════════════════ */
.cx-terminal {
  background: rgba(0,0,0,0.6);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 16px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.04);
  backdrop-filter: blur(24px);
}
.cx-t-hdr {
  background: rgba(0,0,0,0.5);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 7px;
}
.cx-t-dot { width: 11px; height: 11px; border-radius: 50%; }
.cx-t-dot.r { background: #ff5f57; box-shadow: 0 0 8px rgba(255,95,87,0.6); }
.cx-t-dot.y { background: #febc2e; box-shadow: 0 0 8px rgba(254,188,46,0.6); }
.cx-t-dot.g { background: #28c840; box-shadow: 0 0 8px rgba(40,200,64,0.6); }
.cx-t-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.64rem;
  color: #ffffff;
  margin-left: 8px;
  letter-spacing: 0.5px;
}
.cx-t-body {
  padding: 18px 22px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.73rem;
  color: #ffffff;
  max-height: 260px;
  overflow-y: auto;
  line-height: 2;
}
.log-ok   { color: #4ade80; }
.log-warn { color: #fbbf24; }
.log-info { color: #60a5fa; }
.log-err  { color: #f87171; }
.log-head { color: #ffffff; font-weight: 600; font-size: 0.78rem; }

/* ══════════════════════════════════════════════════════════
   TABS
═══════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.03) !important;
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  gap: 3px !important;
  padding: 4px !important;
  backdrop-filter: blur(24px) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: #ffffff !important;
  border-radius: 10px !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  padding: 9px 20px !important;
  border: none !important;
  transition: all 0.2s ease !important;
  font-family: 'Inter', sans-serif !important;
  letter-spacing: 0.3px !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: #ffffff !important;
  background: rgba(255,255,255,0.04) !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(255,255,255,0.09) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  box-shadow: 0 0 24px rgba(255,255,255,0.06) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 0 14px 14px 14px !important;
  padding: 20px !important;
  backdrop-filter: blur(24px) !important;
}

/* ══════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════ */
.stButton > button {
  background: rgba(255,255,255,0.06) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 12px !important;
  font-family: 'Orbitron', sans-serif !important;
  font-weight: 700 !important;
  font-size: 0.62rem !important;
  letter-spacing: 2.5px !important;
  text-transform: uppercase !important;
  padding: 14px 24px !important;
  backdrop-filter: blur(16px) !important;
  transition: all 0.25s ease !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}
.stButton > button:hover {
  background: rgba(255,255,255,0.12) !important;
  border-color: #ffffff !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 24px rgba(255,255,255,0.08) !important;
  transform: translateY(-2px) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }

/* ══════════════════════════════════════════════════════════
   INPUTS & SELECTS
═══════════════════════════════════════════════════════════ */
.stTextInput input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 12px !important;
  color: #ffffff !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.82rem !important;
  transition: all 0.2s ease !important;
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.2) !important;
}
.stTextInput input:focus {
  border-color: #ffffff !important;
  box-shadow: 0 0 0 3px rgba(255,255,255,0.06), inset 0 2px 8px rgba(0,0,0,0.2) !important;
}
.stTextInput input::placeholder { color: #ffffff !important; }

.stSelectbox > div > div {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 12px !important;
  color: #ffffff !important;
}
label,
.stSelectbox label,
.stSlider label,
.stTextInput label,
.stMultiSelect label {
  color: #ffffff !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.3px !important;
}
[data-baseweb="slider"] [role="slider"] {
  background: #ffffff !important;
  box-shadow: 0 0 12px rgba(255,255,255,0.6) !important;
  width: 16px !important; height: 16px !important;
}
[role="progressbar"] { background: rgba(255,255,255,0.4) !important; }
div[data-testid="stThumbValue"] {
  font-family: 'JetBrains Mono', monospace !important;
  color: #ffffff !important;
  background: rgba(0,0,0,0.7) !important;
  border: 1px solid rgba(255,255,255,0.2) !important;
  border-radius: 6px !important;
  padding: 2px 8px !important;
  font-size: 0.70rem !important;
}

/* Checkboxes */
.stCheckbox > label { color: #ffffff !important; font-size: 0.75rem !important; }

/* ══════════════════════════════════════════════════════════
   DATAFRAME / TABLE
═══════════════════════════════════════════════════════════ */
.stDataFrame {
  border-radius: 16px !important;
  overflow: hidden !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
}
[data-testid="stDataFrame"] table {
  background: rgba(255,255,255,0.02) !important;
}
[data-testid="stDataFrame"] thead tr th {
  background: rgba(255,255,255,0.04) !important;
  color: #ffffff !important;
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.55rem !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
  padding: 12px 16px !important;
  border-bottom: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stDataFrame"] tbody tr td {
  color: #ffffff !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.72rem !important;
  padding: 10px 16px !important;
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
}
[data-testid="stDataFrame"] tbody tr:hover td {
  background: rgba(255,255,255,0.04) !important;
}

/* ══════════════════════════════════════════════════════════
   EXPANDER
═══════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(24px) !important;
}
[data-testid="stExpander"] summary {
  color: #ffffff !important;
  font-size: 0.80rem !important;
  padding: 14px 20px !important;
}

/* ══════════════════════════════════════════════════════════
   STATUS BADGES
═══════════════════════════════════════════════════════════ */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 100px;
  font-size: 0.58rem;
  font-weight: 700;
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 1.2px;
  text-transform: uppercase;
}
.badge.detected   { background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.4); color: #93c5fd; }
.badge.active     { background: rgba(234,88,12,0.15);  border: 1px solid rgba(234,88,12,0.4);  color: #fdba74; }
.badge.persistent { background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.4); color: #c4b5fd; }
.badge.expanding  { background: rgba(239,68,68,0.15);  border: 1px solid rgba(239,68,68,0.4);  color: #fca5a5; }
.badge.declining  { background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.4); color: #fde68a; }
.badge.closed     { background: rgba(75,85,99,0.15);   border: 1px solid rgba(75,85,99,0.4);   color: #9ca3af; }

/* ══════════════════════════════════════════════════════════
   ALERTS & NOTIFICATIONS
═══════════════════════════════════════════════════════════ */
.stAlert {
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  backdrop-filter: blur(20px) !important;
}
.stAlert p { color: #ffffff !important; font-size: 0.82rem !important; }
.stSuccess { background: rgba(34,197,94,0.08) !important; border-color: rgba(34,197,94,0.25) !important; }
.stWarning { background: rgba(245,158,11,0.08) !important; border-color: rgba(245,158,11,0.25) !important; }
.stError   { background: rgba(239,68,68,0.08)  !important; border-color: rgba(239,68,68,0.25)  !important; }
.stInfo    { background: rgba(59,130,246,0.08)  !important; border-color: rgba(59,130,246,0.25)  !important; }

/* ══════════════════════════════════════════════════════════
   SPINNER
═══════════════════════════════════════════════════════════ */
.stSpinner > div { border-top-color: #ffffff !important; }

/* ══════════════════════════════════════════════════════════
   MARKDOWN TYPOGRAPHY
═══════════════════════════════════════════════════════════ */
p, .stMarkdown p { color: #ffffff; line-height: 1.85; font-weight: 300; }
h1, .stMarkdown h1 { color: #ffffff; font-family: 'Orbitron', sans-serif; font-size: 1.4rem; font-weight: 900; letter-spacing: 2px; margin-bottom: 16px; }
h2, .stMarkdown h2 { color: #ffffff; font-family: 'Orbitron', sans-serif; font-size: 1.1rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 12px; }
h3, .stMarkdown h3 { color: #ffffff; font-family: 'Orbitron', sans-serif; font-size: 0.82rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 10px; }
h4, .stMarkdown h4 { color: #ffffff; font-size: 0.85rem; font-weight: 600; }
strong { color: #ffffff; font-weight: 600; }
code { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 2px 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.82em; color: #ffffff; }
.stMarkdown table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  margin: 16px 0;
}
.stMarkdown table th {
  background: rgba(255,255,255,0.05);
  color: #ffffff;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.56rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  text-align: left;
}
.stMarkdown table td {
  color: #ffffff;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
}
.stMarkdown table tr:hover td { background: rgba(255,255,255,0.03); }
.stCaption { color: #ffffff !important; font-size: 0.67rem !important; letter-spacing: 0.3px; }
a { color: rgba(150,200,255,0.85); text-decoration: none; }
a:hover { color: rgba(200,230,255,1); }
ul li, ol li { color: #ffffff; line-height: 2; }

/* ══════════════════════════════════════════════════════════
   FOOTER
═══════════════════════════════════════════════════════════ */
.cx-footer {
  margin-top: 60px;
  padding: 28px 0 16px;
  text-align: center;
  border-top: 1px solid rgba(255,255,255,0.05);
  color: #ffffff;
  font-size: 0.62rem;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}
.cx-footer a { color: #ffffff; }
.cx-footer a:hover { color: #ffffff; }


/* ══════════════════════════════════════════════════════════
   MAP CONTAINER
═══════════════════════════════════════════════════════════ */
.cx-map-wrap {
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 16px 64px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04);
  margin-bottom: 12px;
}
.stDeckGlJsonChart iframe,
.element-container iframe {
  border-radius: 18px !important;
}

/* ══════════════════════════════════════════════════════════
   NAV — st.page_link() overrides
   Makes page_link buttons look like the premium nav bar
═══════════════════════════════════════════════════════════ */
[data-testid="stPageLink"] {
  text-decoration: none !important;
}
[data-testid="stPageLink"] p,
[data-testid="stPageLink-NavLink"] {
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.52rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 1.6px !important;
  color: #ffffff !important;
  padding: 5px 11px !important;
  border-radius: 8px !important;
  border: 1px solid transparent !important;
  transition: all 0.2s ease !important;
  white-space: nowrap !important;
  display: block !important;
  line-height: 1.4 !important;
}
[data-testid="stPageLink"]:hover p,
[data-testid="stPageLink-NavLink"]:hover {
  color: #ffffff !important;
  background: rgba(255,255,255,0.06) !important;
  border-color: #ffffff !important;
}
/* Active page link */
[data-testid="stPageLink"][aria-current="page"] p,
[data-testid="stPageLink-NavLink"][aria-current="page"] {
  color: #ffffff !important;
  background: rgba(255,255,255,0.09) !important;
  border-color: #ffffff !important;
  box-shadow: 0 0 18px rgba(255,255,255,0.06) !important;
}
/* Remove default Streamlit link decorations */
[data-testid="stPageLink"] a,
[data-testid="stPageLink"] a:hover {
  text-decoration: none !important;
  color: inherit !important;
}
/* Nav container wrapper */
.cx-nav-real {
  position: sticky;
  top: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  padding: 0 2.5rem;
  height: 68px;
  background: rgba(1,2,10,0.90);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  backdrop-filter: blur(48px) saturate(180%);
  -webkit-backdrop-filter: blur(48px) saturate(180%);
  box-shadow: 0 1px 0 rgba(255,255,255,0.06), 0 24px 64px rgba(0,0,0,0.8);
  gap: 0;
}
/* Collapse all Streamlit column/block margin inside nav */
.cx-nav-inner [data-testid="stHorizontalBlock"] {
  gap: 0 !important;
  align-items: center !important;
  flex-wrap: nowrap !important;
  overflow: hidden !important;
}
.cx-nav-inner [data-testid="stHorizontalBlock"] > div {
  flex-shrink: 0 !important;
  min-width: 0 !important;
  padding: 0 !important;
}
.cx-nav-inner [data-testid="column"] {
  padding: 0 !important;
  flex: 0 0 auto !important;
}

/* ═══════════════════════════════════════════════════════════════
   GAP FIX — Remove the giant empty space between nav and content
════════════════════════════════════════════════════════════════ */
.main .block-container {
  padding-top: 0 !important;
  padding-bottom: 2rem !important;
  max-width: 100% !important;
}
/* Kill stacked vertical margins around the nav HTML/columns */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
  margin-bottom: 0 !important;
}
.cx-navstrip [data-testid="stVerticalBlock"],
.cx-navstrip [data-testid="stHorizontalBlock"] {
  gap: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
}
.cx-navstrip [data-testid="column"] {
  padding: 0 !important;
  min-width: 0 !important;
}
/* Compact page_link buttons into tight nav pill shape */
.cx-navstrip [data-testid="stPageLink"] {
  display: block !important;
  width: 100% !important;
}
.cx-navstrip [data-testid="stPageLink"] a {
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.47rem !important;
  font-weight: 700 !important;
  letter-spacing: 1.2px !important;
  text-transform: uppercase !important;
  color: #ffffff !important;
  padding: 4px 7px !important;
  border-radius: 6px !important;
  border: 1px solid transparent !important;
  transition: all 0.2s ease !important;
  white-space: nowrap !important;
  display: block !important;
  text-decoration: none !important;
  line-height: 1.3 !important;
  text-align: center !important;
}
.cx-navstrip [data-testid="stPageLink"] a:hover {
  background: rgba(255,255,255,0.07) !important;
  border-color: rgba(255,255,255,0.15) !important;
  text-decoration: none !important;
}
/* Collapse element containers around the nav components */
.stMarkdown + [data-testid="stHorizontalBlock"] {
  margin-top: 0 !important;
}
/* Hide default Streamlit sidebar nav */
section[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
  display: none !important;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTON FIXES — Always visible text, never white-on-white
════════════════════════════════════════════════════════════════ */
.stButton > button {
  color: #ffffff !important;
  background: rgba(255,255,255,0.08) !important;
  border: 1px solid rgba(255,255,255,0.20) !important;
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.62rem !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  border-radius: 8px !important;
  padding: 8px 18px !important;
  transition: all 0.2s ease !important;
  white-space: nowrap !important;
  min-height: 38px !important;
}
.stButton > button:hover {
  background: rgba(255,255,255,0.14) !important;
  border-color: rgba(255,255,255,0.40) !important;
  box-shadow: 0 0 18px rgba(255,255,255,0.08) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, rgba(239,68,68,0.25), rgba(185,28,28,0.25)) !important;
  border-color: rgba(239,68,68,0.55) !important;
}
.stButton > button p {
  color: #ffffff !important;
}

/* ═══════════════════════════════════════════════════════════════
   MULTISELECT FIX — Keep filter rows on one line
════════════════════════════════════════════════════════════════ */
[data-testid="stMultiSelect"] > div > div {
  max-height: 48px !important;
  overflow: hidden !important;
}
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  flex-wrap: nowrap !important;
  overflow: hidden !important;
  max-height: 44px !important;
}

/* ═══════════════════════════════════════════════════════════════
   TABLE TEXT — Prevent timestamp/date wrapping
════════════════════════════════════════════════════════════════ */
[data-testid="stTable"] td,
.stDataFrame td,
[data-testid="stTable"] th {
  white-space: nowrap !important;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# PyDeck tooltip style
# ─────────────────────────────────────────────────────────────────────────────
DECK_TOOLTIP = {
    "backgroundColor": "rgba(2,4,16,0.96)",
    "color": "#ffffff",
    "fontSize": "12px",
    "borderRadius": "12px",
    "border": "1px solid rgba(255,255,255,0.12)",
    "padding": "12px 16px",
    "fontFamily": "Inter,sans-serif",
    "boxShadow": "0 12px 48px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.04)",
    "lineHeight": "1.7",
}

# ─────────────────────────────────────────────────────────────────────────────
# Component helpers
# ─────────────────────────────────────────────────────────────────────────────

def section_header(icon: str, text: str) -> str:
    return (
        f'<div class="cx-shdr">'
        f'<span class="cx-shdr-icon">{icon}</span>'
        f'<span class="cx-shdr-text">{text}</span>'
        f'<span class="cx-shdr-line"></span>'
        f'</div>'
    )


def metric_card(label: str, value: str, sub: str, color: str = "") -> str:
    return (
        f'<div class="cx-card {color}">'
        f'<div class="cx-card-label">{label}</div>'
        f'<div class="cx-card-value">{value}</div>'
        f'<div class="cx-card-sub">{sub}</div>'
        f'</div>'
    )


def status_badge(status: str) -> str:
    s = status.lower().replace(" ", ".")
    return f'<span class="badge {s}">{status}</span>'


def terminal_log(logs: list, title: str = "fire-fuse.log") -> str:
    body = "<br/>".join(logs) if logs else '<span class="log-info">Awaiting pipeline execution…</span>'
    return (
        f'<div class="cx-terminal">'
        f'<div class="cx-t-hdr">'
        f'<span class="cx-t-dot r"></span><span class="cx-t-dot y"></span><span class="cx-t-dot g"></span>'
        f'<span class="cx-t-title">{title}</span>'
        f'</div>'
        f'<div class="cx-t-body">{body}</div>'
        f'</div>'
    )

# Page route map — (icon, label, relative path from project root)
_NAV_PAGES = [
    ("🌐", "OVERVIEW",      "app"),
    ("🗺", "LIVE MAP",      "pages/1_Live_Map"),
    ("🔥", "FIRE EVENTS",   "pages/2_Fire_Events"),
    ("⚠", "RISK FORECAST",  "pages/3_Risk_Forecast"),
    ("📊", "ANALYTICS",     "pages/4_Analytics"),
    ("📋", "REPORTS",       "pages/5_Reports"),
    ("💾", "DATA",          "pages/6_Data"),
    ("⚙", "SETTINGS",      "pages/7_Settings"),
]


def render_nav(active: str = "OVERVIEW") -> None:
    """Render premium sticky nav bar — brand + nav links in one HTML block (no gap)."""
    import streamlit as st
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")

    # Page routes: (icon, label, url_path)
    pages = [
        ("🌐", "OVERVIEW",       "/"),
        ("🗺", "LIVE MAP",       "/Live_Map"),
        ("🔥", "FIRE EVENTS",    "/Fire_Events"),
        ("⚠",  "RISK FORECAST",  "/Risk_Forecast"),
        ("📊", "ANALYTICS",      "/Analytics"),
        ("📋", "REPORTS",        "/Reports"),
        ("💾", "DATA",           "/Data"),
        ("⚙",  "SETTINGS",      "/Settings"),
    ]

    def link_style(label: str) -> str:
        is_active = label == active
        base = (
            "font-family:'Orbitron',sans-serif;font-size:0.85rem;font-weight:700;"
            "letter-spacing:1.3px;text-transform:uppercase;text-decoration:none;"
            "padding:8px 16px;border-radius:6px;white-space:nowrap;display:inline-block;"
            "transition:all 0.2s ease;line-height:1.3;border:none;background:none;"
        )
        if is_active:
            # Active: brighter text + a bottom border underline (no box/background)
            return base + (
                "color:#ffffff;"
                "border-bottom:2px solid rgba(255,255,255,0.7) !important;"
                "border-radius:0;"
                "padding-bottom:3px;"
            )
        # Inactive: dimmed text, invisible border placeholder so spacing stays consistent
        return base + "color:rgba(255,255,255,0.55);border-bottom:2px solid transparent;"

    nav_links = "".join(
        f'<a href="{url}" target="_self" style="{link_style(label)}">{icon}&nbsp;{label}</a>'
        for icon, label, url in pages
    )

    st.markdown(f"""
    <div style="position:sticky;top:0;z-index:9999;
         background:rgba(255,255,255,0.02);
         border-bottom:1px solid rgba(255,255,255,0.08);
         backdrop-filter:blur(12px) saturate(150%);
         -webkit-backdrop-filter:blur(12px) saturate(150%);
         box-shadow:0 4px 30px rgba(0,0,0,0.5);
         padding:0 2rem;
         margin-bottom:0;">

      <!-- Row 1: Brand + Status -->
      <div style="display:flex;align-items:center;height:65px;gap:0;overflow:hidden;">
        <div style="display:flex;align-items:center;gap:12px;flex-shrink:0;margin-right:auto;">
          <span style="font-size:2.0rem;filter:drop-shadow(0 0 14px rgba(120,180,255,0.8));
                       animation:logoFloat 8s ease-in-out infinite;">🔭</span>
          <div>
            <div style="font-family:'Orbitron',sans-serif;font-size:1.4rem;font-weight:900;
                        color:#ffffff;letter-spacing:3px;line-height:1;
                        text-shadow:0 0 22px rgba(150,200,255,0.4);">CELESTIAL X</div>
            <div style="font-family:'Inter',sans-serif;font-size:0.5rem;font-weight:400;
                        color:#ffffff;letter-spacing:2.4px;text-transform:uppercase;margin-top:2px;
                        opacity:1.0;">
              Satellite Fire Intelligence &amp; Spatiotemporal Event Harmonization
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;
                    font-family:'JetBrains Mono',monospace;font-size:0.75rem;
                    color:#ffffff;opacity:0.5;letter-spacing:0.4px;white-space:nowrap;">
          <span style="width:6px;height:6px;border-radius:50%;background:#22c55e;
                       box-shadow:0 0 8px rgba(34,197,94,0.9);
                       display:inline-block;animation:blink 2.5s ease-in-out infinite;"></span>
          SYSTEM ONLINE &nbsp;|&nbsp; {now_utc}
        </div>
      </div>

      <!-- Row 2: Nav links -->
      <div style="display:flex;align-items:center;gap:2px;padding:5px 0 6px;
                  border-top:1px solid rgba(255,255,255,0.05);overflow-x:auto;
                  scrollbar-width:none;">
        {nav_links}
      </div>

    </div>
    """, unsafe_allow_html=True)



def nav_bar(active: str = "OVERVIEW") -> str:
    """Backwards-compat stub — call render_nav() instead."""
    return ""


def footer() -> str:
    return (
        '<div class="cx-footer">'
        'CELESTIAL X &nbsp;·&nbsp; NASA Space Apps Challenge 2026 &nbsp;·&nbsp; '
        'CELESTIAL X FIRE-FUSE Spatiotemporal Event Reconciliation Engine &nbsp;·&nbsp; '
        '<a href="https://firms.modaps.eosdis.nasa.gov" target="_blank">NASA FIRMS</a>'
        '</div>'
    )

import base64
import os
try:
    bg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "bg.png")
    with open(bg_path, "rb") as f:
        _bg_b64 = base64.b64encode(f.read()).decode("utf-8")
        GLOBAL_CSS = GLOBAL_CSS.replace("{_bg_b64}", _bg_b64)
except Exception as e:
    pass
