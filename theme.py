"""
theme.py — F1 Predictor 2026 Design System
===========================================
Central source of truth for all UI constants, CSS, and colour tokens.
Import this module in app.py instead of defining CSS inline.

Design concept: "Pit Wall at Night"
— Carbon-black base with phosphor-green telemetry accents,
  heat-map amber for data warnings, and Ferrari-grade scarlet for podium.
  Typography: Bebas Neue for hero numerics, JetBrains Mono for telemetry.
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# COLOUR TOKENS
# ──────────────────────────────────────────────────────────────────────────────

COLORS = {
    # Surface hierarchy
    "bg_void":      "#080A0F",   # True black void
    "bg_deep":      "#0B0E15",   # Primary background
    "bg_surface":   "#101520",   # Card surface
    "bg_raised":    "#151B28",   # Elevated card
    "bg_overlay":   "#1C2335",   # Tooltip / popover

    # Accent spectrum — F1 telemetry palette
    "red_f1":       "#E8002D",   # Ferrari scarlet / primary CTA
    "red_glow":     "#FF1744",   # Hot glow variant
    "amber_warn":   "#FF6D00",   # Safety car / warning
    "amber_light":  "#FFB300",   # Soft yellow
    "gold_podium":  "#FFD600",   # P1 gold
    "silver_p2":    "#C0C0C0",   # P2 silver
    "bronze_p3":    "#CD7F32",   # P3 bronze

    # Telemetry greens
    "teal_primary": "#00E5CC",   # Primary telemetry line
    "teal_dim":     "#00897B",   # Dimmed telemetry
    "green_drs":    "#00E676",   # DRS active indicator
    "green_valid":  "#69F0AE",   # Valid lap

    # Blues
    "blue_kers":    "#448AFF",   # ERS / overtake button
    "blue_dim":     "#1A237E",   # Dark blue fill
    "purple_hyper": "#AA00FF",   # Hypersoft / ultra-mode

    # Text
    "text_primary":  "#ECEFF4",  # Main readable text
    "text_secondary":"#90A4AE",  # Muted / secondary
    "text_dim":      "#546E7A",  # Very muted / disabled
    "text_bright":   "#FFFFFF",  # Forced white

    # Borders
    "border_fine":   "rgba(255,255,255,0.06)",
    "border_card":   "rgba(255,255,255,0.10)",
    "border_hot":    "rgba(232,0,45,0.40)",
    "border_teal":   "rgba(0,229,204,0.30)",
}

# Team colour map — used for chart markers
TEAM_COLORS = {
    "mercedes":     "#00D2BE",
    "red_bull":     "#1E41FF",
    "ferrari":      "#E8002D",
    "mclaren":      "#FF8000",
    "alpine":       "#0090FF",
    "williams":     "#005AFF",
    "haas":         "#B6BABD",
    "rb":           "#6692FF",
    "audi":         "#C00110",
    "aston_martin": "#358C75",
    "cadillac":     "#BE3445",
}

# Position medal map
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

# ──────────────────────────────────────────────────────────────────────────────
# CSS — FULL DESIGN SYSTEM
# ──────────────────────────────────────────────────────────────────────────────

GOOGLE_FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:wght@300;400;700&family=Syne:wght@400;500;600;700;800&display=swap" rel="stylesheet">
"""

BASE_CSS = """
<style>


/* ═══════════════════════════════════════════
   RESET & ROOT TOKENS
═══════════════════════════════════════════ */
:root {{
  --bg-void:       #080A0F;
  --bg-deep:       #0B0E15;
  --bg-surface:    #101520;
  --bg-raised:     #151B28;
  --bg-overlay:    #1C2335;

  --red-f1:        #E8002D;
  --red-glow:      #FF1744;
  --amber-warn:    #FF6D00;
  --gold-podium:   #FFD600;
  --silver-p2:     #C0C0C0;
  --bronze-p3:     #CD7F32;

  --teal-primary:  #00E5CC;
  --teal-dim:      #00897B;
  --green-drs:     #00E676;
  --blue-kers:     #448AFF;
  --purple-hyper:  #AA00FF;

  --text-primary:  #ECEFF4;
  --text-secondary:#90A4AE;
  --text-dim:      #546E7A;
  --text-bright:   #FFFFFF;

  --border-fine:   rgba(255,255,255,0.06);
  --border-card:   rgba(255,255,255,0.10);
  --border-hot:    rgba(232,0,45,0.40);
  --border-teal:   rgba(0,229,204,0.30);


  --font-display:  'Bebas Neue', 'Impact', sans-serif;
  --font-body:     'Syne', 'Segoe UI', system-ui, sans-serif;
  --font-mono:     'JetBrains Mono', 'Fira Code', monospace;


  --radius-sm:     6px;
  --radius-md:     12px;
  --radius-lg:     18px;
  --radius-xl:     24px;

  --shadow-card:   0 4px 24px rgba(0,0,0,0.55);
  --shadow-glow-red:   0 0 32px rgba(232,0,45,0.25), 0 0 8px rgba(232,0,45,0.12);
  --shadow-glow-teal:  0 0 32px rgba(0,229,204,0.20), 0 0 8px rgba(0,229,204,0.10);
}}

/* ═══════════════════════════════════════════
   GLOBAL BASE
═══════════════════════════════════════════ */
html, body {{
  background: var(--bg-deep) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-body) !important;
}}

/* Streamlit structural overrides */
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewBlockContainer"] {{
  background: var(--bg-deep) !important;
}}

section.main, section.main > div {{
  background: var(--bg-deep) !important;
  padding-top: 0 !important;
}}

/* Kill Streamlit's white flash */
div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"],
div[data-testid="block-container"] {{
  background: transparent !important;
}}

/* Markdown text colour */
div[data-testid="stMarkdownContainer"],
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li {{
  color: var(--text-secondary) !important;
  font-family: var(--font-body) !important;
}}

/* Headings */
div[data-testid="stHeading"],
h1, h2, h3, h4 {{
  font-family: var(--font-display) !important;
  color: var(--text-bright) !important;
  letter-spacing: 1px;
}}

/* ═══════════════════════════════════════════
   SIDEBAR — PIT WALL PANEL
═══════════════════════════════════════════ */
section[data-testid="stSidebar"] {{
  background:
    linear-gradient(180deg,
      rgba(232,0,45,0.08) 0%,
      rgba(8,10,15,0.98) 30%,
      rgba(8,10,15,1.0) 100%),
    var(--bg-void) !important;
  border-right: 1px solid var(--border-hot) !important;
}}

section[data-testid="stSidebar"] .block-container {{
  padding-top: 16px !important;
}}

section[data-testid="stSidebar"] label {{
  color: var(--text-secondary) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[role="combobox"],
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-card) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-sm) !important;
}}

/* ═══════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════ */
div[data-testid="stButton"] > button {{
  font-family: var(--font-display) !important;
  font-size: 1.1rem !important;
  letter-spacing: 1.5px !important;
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border-hot) !important;
  padding: 0.7rem 1.4rem !important;
  transition: all 0.2s ease !important;
  width: 100%;
}}

div[data-testid="stButton"] > button[kind="primary"] {{
  background: linear-gradient(135deg, var(--red-f1) 0%, #B71C1C 100%) !important;
  color: var(--text-bright) !important;
  box-shadow: var(--shadow-glow-red) !important;
}}

div[data-testid="stButton"] > button[kind="primary"]:hover {{
  background: linear-gradient(135deg, var(--red-glow) 0%, var(--red-f1) 100%) !important;
  box-shadow: 0 0 48px rgba(232,0,45,0.40), 0 0 16px rgba(232,0,45,0.20) !important;
  transform: translateY(-1px);
}}

div[data-testid="stButton"] > button[kind="secondary"] {{
  background: var(--bg-raised) !important;
  color: var(--text-secondary) !important;
}}

/* ═══════════════════════════════════════════
   METRICS
═══════════════════════════════════════════ */
div[data-testid="stMetricValue"] {{
  font-family: var(--font-display) !important;
  font-size: 2.2rem !important;
  color: var(--teal-primary) !important;
}}

div[data-testid="stMetricLabel"] {{
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-dim) !important;
}}

div[data-testid="stMetricDelta"] {{
  font-family: var(--font-mono) !important;
  font-size: 0.78rem !important;
}}

/* ═══════════════════════════════════════════
   INPUTS & SELECTS
═══════════════════════════════════════════ */
div[data-testid="stSelectbox"] div[role="combobox"],
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-card) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-sm) !important;
  font-family: var(--font-mono) !important;
}}

/* ═══════════════════════════════════════════
   TABS
═══════════════════════════════════════════ */
div[data-testid="stTabs"] [role="tablist"] {{
  background: var(--bg-surface) !important;
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border-card) !important;
  padding: 4px !important;
  gap: 2px !important;
}}

div[data-testid="stTabs"] [role="tab"] {{
  font-family: var(--font-mono) !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim) !important;
  border-radius: var(--radius-sm) !important;
  transition: all 0.15s ease !important;
}}

div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
  background: var(--red-f1) !important;
  color: var(--text-bright) !important;
  box-shadow: var(--shadow-glow-red) !important;
}}

/* ═══════════════════════════════════════════
   DATAFRAMES
═══════════════════════════════════════════ */
div[data-testid="stDataFrame"] {{
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border-card) !important;
  overflow: hidden;
}}

div[data-testid="stDataFrame"] thead th {{
  background: var(--bg-raised) !important;
  color: var(--text-dim) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border-hot) !important;
}}

div[data-testid="stDataFrame"] tbody tr:hover {{
  background: var(--bg-overlay) !important;
}}

/* ═══════════════════════════════════════════
   SPINNERS & PROGRESS
═══════════════════════════════════════════ */
div[data-testid="stSpinner"] > div {{
  border-top-color: var(--red-f1) !important;
}}

/* ═══════════════════════════════════════════
   SLIDERS
═══════════════════════════════════════════ */
div[data-testid="stSlider"] [role="slider"] {{
  background: var(--red-f1) !important;
  border: 2px solid var(--red-glow) !important;
  box-shadow: var(--shadow-glow-red) !important;
}}

div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]::after {{
  background: var(--red-f1) !important;
}}

/* ═══════════════════════════════════════════
   TOGGLE / CHECKBOX
═══════════════════════════════════════════ */
div[data-testid="stCheckbox"] input:checked + div,
div[data-testid="stToggle"] input:checked + div {{
  background: var(--red-f1) !important;
}}

/* ═══════════════════════════════════════════
   ALERT / INFO / SUCCESS BOXES
═══════════════════════════════════════════ */
div[data-testid="stAlert"][kind="info"] {{
  background: rgba(68,138,255,0.12) !important;
  border-left: 3px solid var(--blue-kers) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-secondary) !important;
}}

div[data-testid="stAlert"][kind="success"],
div[data-testid="stSuccess"] {{
  background: rgba(0,230,118,0.10) !important;
  border-left: 3px solid var(--green-drs) !important;
  border-radius: var(--radius-sm) !important;
}}

div[data-testid="stAlert"][kind="warning"] {{
  background: rgba(255,109,0,0.12) !important;
  border-left: 3px solid var(--amber-warn) !important;
  border-radius: var(--radius-sm) !important;
}}

div[data-testid="stAlert"][kind="error"] {{
  background: rgba(232,0,45,0.12) !important;
  border-left: 3px solid var(--red-f1) !important;
  border-radius: var(--radius-sm) !important;
}}

/* ═══════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════ */
::-webkit-scrollbar {{
  width: 6px;
  height: 6px;
}}
::-webkit-scrollbar-track {{
  background: var(--bg-void);
}}
::-webkit-scrollbar-thumb {{
  background: var(--bg-overlay);
  border-radius: 99px;
}}
::-webkit-scrollbar-thumb:hover {{
  background: var(--red-f1);
}}

/* ═══════════════════════════════════════════
   PLOTLY CHARTS — forced dark bg
═══════════════════════════════════════════ */
.plot-container .plotly .main-svg {{
  border-radius: var(--radius-md) !important;
}}

/* ═══════════════════════════════════════════
   MULTISELECT TAGS
═══════════════════════════════════════════ */
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
  background: rgba(232,0,45,0.20) !important;
  border: 1px solid var(--border-hot) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-sm) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.75rem !important;
}}

/* ═══════════════════════════════════════════
   APP-LEVEL HTML COMPONENT CLASSES (bb-*)
   These are referenced by app.py (unsafe HTML).
═══════════════════════════════════════════ */
/* bb-* class definitions are injected via Python f-string; ensure CSS braces do not break f-string formatting */
.bb-hero {
  position: relative;
}


.bb-title {
  font-family: var(--font-display);
  letter-spacing: 2px;
  font-size: 2.4rem;
  color: var(--text-bright);
  text-shadow: 0 0 40px rgba(232,0,45,0.25);
}

.bb-sub {
  font-family: var(--font-body);
  color: rgba(144,164,174,0.90);
  font-weight: 600;
  line-height: 1.55;
  margin-top: 4px;
}

.bb-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.bb-badge {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(232,0,45,0.12);
  border: 1px solid rgba(232,0,45,0.28);
  color: rgba(255,180,80,0.92);
  box-shadow: 0 0 28px rgba(232,0,45,0.08);
}

.bb-card {
  border: 1px solid var(--border-card) !important;
  background: linear-gradient(180deg, rgba(21,27,40,0.70) 0%, rgba(16,21,32,0.55) 100%);
  border-radius: 14px !important;
  box-shadow: var(--shadow-card);
}

.bb-card-strong {
  border: 1px solid rgba(0,229,204,0.20) !important;
  background:
    repeating-linear-gradient(90deg, rgba(0,229,204,0.05) 0px, rgba(0,229,204,0.05) 1px, transparent 1px, transparent 16px),
    radial-gradient(ellipse 120% 80% at 10% -20%, rgba(232,0,45,0.18) 0%, transparent 55%),
    linear-gradient(180deg, rgba(21,27,40,0.78) 0%, rgba(11,14,21,0.55) 100%);
  border-radius: 14px !important;
  box-shadow: 0 10px 46px rgba(0,0,0,0.45);
}

.bb-section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.bb-telemetry {
  border-radius: 12px;
  border: 1px solid rgba(0,229,204,0.18);
  background:
    repeating-linear-gradient(90deg, rgba(0,229,204,0.04) 0px, rgba(0,229,204,0.04) 1px, transparent 1px, transparent 18px),
    rgba(0,229,204,0.04);
  padding: 14px 18px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--red-f1);
  box-shadow: 0 0 0 6px rgba(232,0,45,0.12);
}

.bb-ghost-divider {
  height: 1px;
  background: rgba(255,255,255,0.06);
  margin: 12px 0;
}
</style>
"""

# ──────────────────────────────────────────────────────────────────────────────
# COMPONENT HTML TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────

def hero_banner(circuit_name: str = "Monaco", race_date: str = "2026-06-07") -> str:
    """Full-width cinematic hero banner with animated scan-line effect."""
    return f"""
<div style="
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  border: 1px solid rgba(232,0,45,0.25);
  background:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,229,204,0.015) 2px,
      rgba(0,229,204,0.015) 4px
    ),
    radial-gradient(ellipse 140% 80% at 10% -20%, rgba(232,0,45,0.30) 0%, transparent 55%),
    radial-gradient(ellipse 100% 60% at 90% 110%, rgba(0,229,204,0.18) 0%, transparent 50%),
    linear-gradient(180deg, #0F1520 0%, #080A0F 100%);
  padding: 28px 32px 22px;
  margin-bottom: 20px;
  box-shadow:
    0 0 60px rgba(232,0,45,0.15),
    0 20px 60px rgba(0,0,0,0.50),
    inset 0 1px 0 rgba(255,255,255,0.06);
">
  <!-- Decorative top stripe -->
  <div style="
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg,
      transparent 0%,
      #E8002D 20%,
      #FF6D00 45%,
      #FFD600 60%,
      #00E5CC 80%,
      transparent 100%
    );
  "></div>

  <!-- Decorative corner element -->
  <div style="
    position: absolute;
    top: 12px; right: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    color: rgba(0,229,204,0.55);
    text-transform: uppercase;
  ">◈ LIVE PREDICTION</div>

  <!-- Main content -->
  <div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; flex-wrap: wrap;">
    <div>
      <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.70rem;
        letter-spacing: 0.18em;
        color: rgba(232,0,45,0.80);
        text-transform: uppercase;
        margin-bottom: 6px;
      ">F1 PREDICTOR 2026 · MONTE CARLO ENGINE</div>

      <div style="
        font-family: 'Bebas Neue', Impact, sans-serif;
        font-size: clamp(2.4rem, 5vw, 3.6rem);
        line-height: 0.92;
        letter-spacing: 2px;
        color: #FFFFFF;
        text-shadow: 0 0 40px rgba(232,0,45,0.25);
        margin-bottom: 10px;
      ">{circuit_name.upper()} <span style="color: var(--red-f1, #E8002D);">GP</span></div>

      <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: rgba(144,164,174,0.85);
        margin-bottom: 14px;
      ">{race_date} · Probabilistic race-day forecasting</div>

      <!-- Badges -->
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <span style="
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.68rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 4px 12px;
          border-radius: 99px;
          background: rgba(232,0,45,0.15);
          border: 1px solid rgba(232,0,45,0.30);
          color: rgba(255,100,100,0.90);
        ">⬡ Monte Carlo</span>
        <span style="
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.68rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 4px 12px;
          border-radius: 99px;
          background: rgba(0,229,204,0.12);
          border: 1px solid rgba(0,229,204,0.25);
          color: rgba(0,229,204,0.90);
        ">◈ 4D ELO</span>
        <span style="
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.68rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 4px 12px;
          border-radius: 99px;
          background: rgba(255,109,0,0.12);
          border: 1px solid rgba(255,109,0,0.25);
          color: rgba(255,180,80,0.90);
        ">△ Tire Strategy</span>
        <span style="
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.68rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 4px 12px;
          border-radius: 99px;
          background: rgba(68,138,255,0.12);
          border: 1px solid rgba(68,138,255,0.25);
          color: rgba(120,170,255,0.90);
        ">◇ Wilson CI</span>
      </div>
    </div>

    <!-- Right: Telemetry mini-panel -->
    <div style="
      min-width: 200px;
      background:
        repeating-linear-gradient(
          90deg,
          rgba(0,229,204,0.04) 0px,
          rgba(0,229,204,0.04) 1px,
          transparent 1px,
          transparent 14px
        ),
        repeating-linear-gradient(
          0deg,
          rgba(0,229,204,0.04) 0px,
          rgba(0,229,204,0.04) 1px,
          transparent 1px,
          transparent 14px
        ),
        rgba(0,229,204,0.05);
      border: 1px solid rgba(0,229,204,0.18);
      border-radius: 12px;
      padding: 14px 18px;
    ">
      <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgba(0,229,204,0.60);
        margin-bottom: 8px;
      ">◈ PIT WALL BRIEF</div>
      <div style="
        font-family: 'Syne', system-ui, sans-serif;
        font-size: 0.82rem;
        font-weight: 600;
        color: rgba(236,239,244,0.88);
        line-height: 1.55;
      ">Select circuit → set conditions<br>→ run simulation → inspect<br>win probability & risk map.</div>
    </div>
  </div>
</div>
"""


def section_header(label: str, accent: str = "red", icon: str = "◈") -> str:
    """Styled section divider with accent dot."""
    accent_map = {
        "red":  ("rgba(232,0,45,0.90)",   "0 0 0 5px rgba(232,0,45,0.12)"),
        "teal": ("rgba(0,229,204,0.90)",  "0 0 0 5px rgba(0,229,204,0.12)"),
        "amber":("rgba(255,109,0,0.90)",  "0 0 0 5px rgba(255,109,0,0.12)"),
        "blue": ("rgba(68,138,255,0.90)", "0 0 0 5px rgba(68,138,255,0.12)"),
        "gold": ("rgba(255,214,0,0.90)",  "0 0 0 5px rgba(255,214,0,0.12)"),
    }
    color, ring = accent_map.get(accent, accent_map["red"])
    return f"""
<div style="
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 18px 0 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
">
  <span style="
    display: inline-block;
    width: 9px; height: 9px;
    border-radius: 50%;
    background: {color};
    box-shadow: {ring};
    flex-shrink: 0;
  "></span>
  <span style="
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(144,164,174,0.85);
    font-weight: 700;
  ">{icon} {label}</span>
</div>
"""


def driver_card(
    pos: int,
    name: str,
    team: str,
    win_pct: float,
    top3_pct: float,
    dnf_pct: float,
    confidence: str,
    team_colors: dict | None = None,
) -> str:
    """Single driver result card with probability bar."""
    _tc = team_colors or TEAM_COLORS
    team_color = _tc.get(team.lower().replace(" ", "_"), "#546E7A")

    medal_html = ""
    if pos == 1:
        medal_html = '<span style="font-size:1.1rem;">🥇</span>'
    elif pos == 2:
        medal_html = '<span style="font-size:1.1rem;">🥈</span>'
    elif pos == 3:
        medal_html = '<span style="font-size:1.1rem;">🥉</span>'
    else:
        medal_html = f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.85rem;color:rgba(144,164,174,0.55);">P{pos:02d}</span>'

    conf_color = {"High": "#00E676", "Medium": "#FFB300", "Low": "#FF5252"}.get(confidence, "#546E7A")
    bar_width = min(win_pct * 3, 100)  # scale for visual

    return f"""
<div style="
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(21,27,40,0.65);
  margin-bottom: 6px;
  transition: background 0.15s ease;
">
  <!-- Position -->
  <div style="width: 32px; text-align: center; flex-shrink: 0;">{medal_html}</div>

  <!-- Team color bar -->
  <div style="
    width: 3px;
    height: 36px;
    border-radius: 2px;
    background: {team_color};
    flex-shrink: 0;
    box-shadow: 0 0 8px {team_color}55;
  "></div>

  <!-- Driver info -->
  <div style="flex: 1; min-width: 0;">
    <div style="
      font-family: 'Syne', system-ui, sans-serif;
      font-weight: 700;
      font-size: 0.92rem;
      color: #ECEFF4;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    ">{name.title()}</div>
    <div style="
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      color: rgba(144,164,174,0.60);
      letter-spacing: 0.06em;
      text-transform: uppercase;
    ">{team.replace("_"," ").upper()}</div>
  </div>

  <!-- Win prob bar -->
  <div style="width: 80px; flex-shrink: 0;">
    <div style="
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      color: rgba(144,164,174,0.55);
      letter-spacing: 0.08em;
      margin-bottom: 3px;
    ">WIN</div>
    <div style="
      height: 4px;
      background: rgba(255,255,255,0.08);
      border-radius: 2px;
      overflow: hidden;
    ">
      <div style="
        height: 100%;
        width: {bar_width}%;
        background: linear-gradient(90deg, {team_color} 0%, #E8002D 100%);
        border-radius: 2px;
      "></div>
    </div>
    <div style="
      font-family: 'Bebas Neue', Impact, sans-serif;
      font-size: 1.0rem;
      color: #ECEFF4;
      margin-top: 2px;
    ">{win_pct:.1f}%</div>
  </div>

  <!-- Top 3 -->
  <div style="width: 52px; text-align: right; flex-shrink: 0;">
    <div style="
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      color: rgba(144,164,174,0.45);
      letter-spacing: 0.08em;
    ">POD</div>
    <div style="
      font-family: 'Bebas Neue', Impact, sans-serif;
      font-size: 1.0rem;
      color: {COLORS["gold_podium"]};
    ">{top3_pct:.1f}%</div>
  </div>

  <!-- DNF -->
  <div style="width: 48px; text-align: right; flex-shrink: 0;">
    <div style="
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      color: rgba(144,164,174,0.45);
      letter-spacing: 0.08em;
    ">DNF</div>
    <div style="
      font-family: 'Bebas Neue', Impact, sans-serif;
      font-size: 1.0rem;
      color: {'#FF5252' if dnf_pct > 15 else '#FFB300' if dnf_pct > 10 else '#69F0AE'};
    ">{dnf_pct:.1f}%</div>
  </div>

  <!-- Confidence dot -->
  <div style="
    width: 8px; height: 8px;
    border-radius: 50%;
    background: {conf_color};
    box-shadow: 0 0 6px {conf_color}88;
    flex-shrink: 0;
  " title="Confidence: {confidence}"></div>
</div>
"""


def podium_display(p1: str, p2: str, p3: str, w1: float, w2: float, w3: float) -> str:
    """Three-step podium HTML component."""
    def _card(pos, name, win_pct, height, color, medal, delay):
        return f"""
<div style="
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: podium-rise 0.6s ease {delay}s both;
">
  <div style="
    font-size: 1.6rem;
    margin-bottom: 4px;
  ">{medal}</div>
  <div style="
    font-family: 'Syne', system-ui, sans-serif;
    font-weight: 800;
    font-size: 0.92rem;
    color: #ECEFF4;
    text-align: center;
    margin-bottom: 2px;
  ">{name.upper().split()[-1]}</div>
  <div style="
    font-family: 'Bebas Neue', Impact, sans-serif;
    font-size: 1.3rem;
    color: {color};
    margin-bottom: 8px;
  ">{win_pct:.1f}%</div>
  <div style="
    width: 100%;
    height: {height}px;
    background: linear-gradient(180deg, {color}22 0%, {color}08 100%);
    border: 1px solid {color}44;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    display: flex;
    align-items: center;
    justify-content: center;
  ">
    <span style="
      font-family: 'Bebas Neue', Impact, sans-serif;
      font-size: 2.8rem;
      color: {color}66;
    ">P{pos}</span>
  </div>
</div>"""

    return f"""
<style>
@keyframes podium-rise {{
  from {{ transform: translateY(20px); opacity: 0; }}
  to   {{ transform: translateY(0);    opacity: 1; }}
}}
</style>
<div style="
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 16px 16px 0;
  border-radius: 14px;
  background: rgba(16,21,32,0.60);
  border: 1px solid rgba(255,255,255,0.06);
">
  {_card(2, p2, w2, 80,  COLORS["silver_p2"], "🥈", 0.15)}
  {_card(1, p1, w1, 110, COLORS["gold_podium"],"🥇", 0.0)}
  {_card(3, p3, w3, 60,  COLORS["bronze_p3"], "🥉", 0.30)}
</div>
"""


def race_meta_strip(
    circuit_name: str,
    sc_prob: float,
    rain_prob: float,
    n_sims: int,
    model_confidence: float,
    is_sprint: bool = False,
) -> str:
    """Compact status bar with race metadata."""
    sprint_badge = '<span style="color:#FFD600;font-size:0.80rem;">⚡ SPRINT</span>' if is_sprint else ""
    return f"""
<div style="
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  padding: 10px 16px;
  background: rgba(16,21,32,0.70);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  margin-bottom: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  color: rgba(144,164,174,0.75);
">
  <span style="color:#ECEFF4;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;">{circuit_name.upper()}</span>
  <span style="color:rgba(255,255,255,0.15)">│</span>
  <span>🚗 SC <span style="color:{'#FF6D00' if sc_prob>0.35 else '#69F0AE'}">{sc_prob*100:.0f}%</span></span>
  <span style="color:rgba(255,255,255,0.15)">│</span>
  <span>🌧 RAIN <span style="color:{'#448AFF' if rain_prob>0.3 else '#69F0AE'}">{rain_prob*100:.0f}%</span></span>
  <span style="color:rgba(255,255,255,0.15)">│</span>
  <span>∑ <span style="color:#00E5CC">{n_sims:,}</span> SIMS</span>
  <span style="color:rgba(255,255,255,0.15)">│</span>
  <span>CONF <span style="color:{'#69F0AE' if model_confidence>0.7 else '#FFB300'}">{model_confidence*100:.0f}%</span></span>
  {"<span style='color:rgba(255,255,255,0.15)'>│</span>" + sprint_badge if is_sprint else ""}
</div>
"""


def stat_box(label: str, value: str, accent: str = "teal", sublabel: str = "") -> str:
    """Individual metric box for grid layouts."""
    accent_map = {
        "teal":  ("#00E5CC", "rgba(0,229,204,0.12)", "rgba(0,229,204,0.20)"),
        "red":   ("#E8002D", "rgba(232,0,45,0.12)",  "rgba(232,0,45,0.20)"),
        "amber": ("#FF6D00", "rgba(255,109,0,0.12)", "rgba(255,109,0,0.20)"),
        "gold":  ("#FFD600", "rgba(255,214,0,0.12)", "rgba(255,214,0,0.20)"),
        "blue":  ("#448AFF", "rgba(68,138,255,0.12)","rgba(68,138,255,0.20)"),
        "green": ("#00E676", "rgba(0,230,118,0.12)", "rgba(0,230,118,0.20)"),
    }
    color, bg, border = accent_map.get(accent, accent_map["teal"])
    sub_html = f'<div style="font-size:0.65rem;color:rgba(144,164,174,0.55);margin-top:2px;">{sublabel}</div>' if sublabel else ""
    return f"""
<div style="
  padding: 16px 18px;
  background: {bg};
  border: 1px solid {border};
  border-radius: 12px;
  text-align: center;
">
  <div style="
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(144,164,174,0.55);
    margin-bottom: 6px;
  ">{label}</div>
  <div style="
    font-family: 'Bebas Neue', Impact, sans-serif;
    font-size: 2.0rem;
    color: {color};
    line-height: 1.0;
  ">{value}</div>
  {sub_html}
</div>
"""


def surprise_alert(drivers: list[str]) -> str:
    if not drivers:
        return ""
    names = " · ".join(d.upper() for d in drivers)
    return f"""
<div style="
  padding: 10px 16px;
  background: rgba(255,109,0,0.10);
  border: 1px solid rgba(255,109,0,0.25);
  border-radius: 10px;
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
">
  <span style="font-size:1.1rem;">⬆</span>
  <span style="
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.10em;
    color: rgba(255,180,80,0.90);
    text-transform: uppercase;
  ">POTENTIAL OVERPERFORMERS: {names}</span>
</div>
"""


def h2h_result_bar(d1_name: str, d2_name: str, p1_ahead: float, color1: str, color2: str) -> str:
    """Horizontal split bar for head-to-head comparison."""
    p1 = round(p1_ahead * 100, 1)
    p2 = round(100 - p1, 1)
    return f"""
<div style="margin: 16px 0;">
  <div style="
    display: flex;
    justify-content: space-between;
    font-family: 'Syne', system-ui, sans-serif;
    font-weight: 700;
    font-size: 0.88rem;
    margin-bottom: 8px;
  ">
    <span style="color:#ECEFF4;">{d1_name.upper()}</span>
    <span style="color:#ECEFF4;">{d2_name.upper()}</span>
  </div>
  <div style="
    height: 12px;
    border-radius: 6px;
    overflow: hidden;
    display: flex;
    border: 1px solid rgba(255,255,255,0.08);
  ">
    <div style="width:{p1}%;background:{color1};"></div>
    <div style="width:{p2}%;background:{color2};"></div>
  </div>
  <div style="
    display: flex;
    justify-content: space-between;
    font-family: 'Bebas Neue', Impact, sans-serif;
    font-size: 1.3rem;
    margin-top: 4px;
  ">
    <span style="color:{color1};">{p1}%</span>
    <span style="color:{color2};">{p2}%</span>
  </div>
</div>
"""


# ──────────────────────────────────────────────────────────────────────────────
# PLOTLY LAYOUT FACTORY
# ──────────────────────────────────────────────────────────────────────────────

def f1_plotly_layout(title: str = "", height: int = 340) -> dict:
    """Return a Plotly layout dict matching the F1 dark theme."""
    return dict(
        title=dict(
            text=title,
            font=dict(family="Bebas Neue, Impact, sans-serif", size=16, color="#ECEFF4"),
            x=0,
            xanchor="left",
            pad=dict(l=4),
        ),
        height=height,
        paper_bgcolor="rgba(16,21,32,0.0)",
        plot_bgcolor="rgba(16,21,32,0.0)",
        font=dict(family="JetBrains Mono, monospace", color="#90A4AE", size=11),
        margin=dict(l=48, r=16, t=44, b=80),
        xaxis=dict(
            tickangle=-42,
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.06)",
            tickfont=dict(family="JetBrains Mono, monospace", size=10),
            title=None,
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.06)",
            tickfont=dict(family="JetBrains Mono, monospace", size=10),
            title=None,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10),
        ),
        hoverlabel=dict(
            bgcolor="#151B28",
            bordercolor="rgba(232,0,45,0.40)",
            font=dict(family="JetBrains Mono, monospace", size=11, color="#ECEFF4"),
        ),
        showlegend=False,
    )


def bar_colors_from_teams(predictions: list, team_colors: dict | None = None) -> list[str]:
    """Map a list of predictions to their team hex colour."""
    _tc = team_colors or TEAM_COLORS
    return [
        _tc.get(p.get("team", "").lower().replace(" ", "_"), "#546E7A")
        for p in predictions
    ]


# ──────────────────────────────────────────────────────────────────────────────
# INJECT HELPER
# ──────────────────────────────────────────────────────────────────────────────

def apply_theme() -> None:
    """
    Apply the F1 theme to Streamlit app.
    
    Usage in app.py:
        from theme import apply_theme
        apply_theme()
    """
    import streamlit as st
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st.markdown(BASE_CSS,     unsafe_allow_html=True)


def inject_theme(st_module) -> None:
    """
    Call this once at app startup to inject fonts + CSS into Streamlit.

    Usage in app.py:
        from theme import inject_theme
        inject_theme(st)
    """
    st_module.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st_module.markdown(BASE_CSS,     unsafe_allow_html=True)
