"""
theme.py — F1 Predictor 2026
============================

Modern F1 theme with racing-inspired telemetry, carbon fibre background,
track-map grids, and a contemporary contrast palette.
"""

from __future__ import annotations

COLORS = {
    "bg_void":       "#070A12",
    "bg_deep":       "#0D1120",
    "bg_surface":    "#141C2E",
    "bg_card":       "#192340",
    "bg_panel":      "#0F1728",
    "bg_overlay":    "#101B2D",
    "red_f1":        "#E10614",
    "red_glow":      "#FF2A4E",
    "amber_warn":    "#FF9B00",
    "gold_podium":   "#FFD400",
    "silver_p2":     "#C7C7C7",
    "bronze_p3":     "#C27C3B",
    "teal_primary":  "#19F0D3",
    "teal_dim":      "#2EA59C",
    "green_drs":     "#6EFFB3",
    "blue_kers":     "#4F7CFF",
    "purple_hyper":  "#B34EFF",
    "text_primary":  "#ECEFF4",
    "text_secondary":"#9BA8BB",
    "text_dim":      "#6F7E97",
    "border_fine":   "rgba(255,255,255,0.08)",
    "border_card":   "rgba(255,255,255,0.12)",
    "border_glow":   "rgba(225,0,26,0.24)",
}

TEAM_COLORS = {
    "mercedes":     "#00D2BE",
    "red_bull":     "#1E41FF",
    "ferrari":      "#E10614",
    "mclaren":      "#FF7A00",
    "alpine":       "#0090FF",
    "williams":     "#005AFF",
    "haas":         "#B6BABD",
    "rb":           "#6692FF",
    "audi":         "#C00110",
    "aston_martin": "#35A286",
    "cadillac":     "#BE3445",
}

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

GOOGLE_FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:wght@300;400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

BASE_CSS = f"""
<style>
:root {{
  color-scheme: dark;
  font-family: "Inter", system-ui, sans-serif;
  color: {COLORS["text_primary"]};
  background: {COLORS["bg_deep"]};
}}

html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {{
  background: radial-gradient(circle at top left, rgba(25,240,211,0.08), transparent 28%),
              radial-gradient(circle at bottom right, rgba(232,0,45,0.14), transparent 22%),
              {COLORS["bg_deep"]} !important;
  color: {COLORS["text_primary"]} !important;
}}

section.main, section.main > div {{
  background: transparent !important;
}}

section[data-testid="stSidebar"] {{
  background: linear-gradient(180deg,
      rgba(232,0,45,0.08) 0%,
      rgba(10,14,24,0.92) 34%,
      rgba(10,14,24,1) 100%) !important;
  border-right: 1px solid {COLORS["border_glow"]} !important;
}}

[data-testid="stSidebar"] .block-container {{
  padding: 18px 18px 20px !important;
}}

div.css-1lcbmhc.e1fqkh3o3 {{
  background: rgba(16,27,43,0.9) !important;
}}

.stButton>button {{
  background: linear-gradient(135deg, {COLORS["red_f1"]}, {COLORS["amber_warn"]}) !important;
  color: {COLORS["text_primary"]} !important;
  border-radius: 999px !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,0.22);
}}

.stButton>button:hover {{
  transform: translateY(-1px);
  box-shadow: 0 24px 58px rgba(0,0,0,0.28);
}}

div[data-testid="stMarkdownContainer"] {{
  color: {COLORS["text_secondary"]} !important;
}}

div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3,
div[data-testid="stMarkdownContainer"] h4 {{
  color: {COLORS["text_primary"]} !important;
  font-family: "Bebas Neue", system-ui, sans-serif !important;
  letter-spacing: 1px;
}}

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li {{
  font-family: "Inter", system-ui, sans-serif !important;
  line-height: 1.65;
}}

[data-testid="stMultiSelect"] button,
[data-testid="stSelectbox"] div[role="combobox"],
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {{
  background: {COLORS["bg_card"]} !important;
  border: 1px solid {COLORS["border_card"]} !important;
  color: {COLORS["text_primary"]} !important;
  border-radius: 14px !important;
}}

.css-1d391kg {{
  border-radius: 20px !important;
  background: rgba(16,27,43,0.9) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  box-shadow: 0 26px 48px rgba(0,0,0,0.22);
}}

.css-1oe6wyh {{
  background: {COLORS["bg_panel"]} !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
}}

.css-1v3fvcr {{
  background: {COLORS["bg_panel"]} !important;
}}

.bb-hero {{
  padding: 24px;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(16,27,43,0.96), rgba(10,14,24,0.88));
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03), 0 24px 60px rgba(0,0,0,0.25);
}}

.bb-title {{
  font-family: "Bebas Neue", system-ui, sans-serif;
  font-size: 3rem;
  color: {COLORS["text_primary"]};
  letter-spacing: 0.04em;
}}

.bb-sub {{
  margin-top: 14px;
  font-size: 1rem;
  color: {COLORS["text_secondary"]};
}}

.bb-badge {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  margin-top: 12px;
  border-radius: 999px;
  background: rgba(25,240,211,0.08);
  border: 1px solid rgba(25,240,211,0.14);
  color: {COLORS["green_drs"]};
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}}

.bb-telemetry {{
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(232,0,45,0.06), rgba(16,27,43,0.94));
  border: 1px solid rgba(232,0,45,0.14);
}}

.bb-telemetry span {{
  color: {COLORS["text_primary"]};
}}

.track-hero {{
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  margin-top: 24px;
}}

.track-hero::before {{
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, rgba(255,255,255,0.06), transparent 28%),
              repeating-linear-gradient(135deg, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 8px);
  pointer-events: none;
}}

.track-hero .track-label {{
  position: relative;
  z-index: 1;
  padding: 36px 28px;
}}

.track-card {{
  background: rgba(16,27,43,0.9);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 24px;
  padding: 22px;
}}

.track-chip {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(255,255,255,0.05);
  color: {COLORS["text_secondary"]};
  font-size: 0.82rem;
}}

.track-chip span {{
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: {COLORS["teal_primary"]};
}}

.speed-stripe {{
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(232,0,45,1), rgba(255,155,0,0.8));
  margin: 20px 0;
}}

</style>
"""

def f1_plotly_layout(title: str = "", height: int = 340) -> dict:
    return dict(
        title=dict(
            text=title,
            font=dict(family='"Bebas Neue", system-ui, sans-serif', size=16, color=COLORS["text_primary"]),
            x=0,
            xanchor="left",
        ),
        height=height,
        paper_bgcolor="rgba(16,27,43,0)",
        plot_bgcolor="rgba(16,27,43,0)",
        font=dict(family='"JetBrains Mono", monospace', color=COLORS["text_secondary"], size=11),
        margin=dict(l=44, r=20, t=44, b=72),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.08)",
            linecolor="rgba(255,255,255,0.12)",
            tickfont=dict(family='"JetBrains Mono", monospace', size=10),
            title=None,
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.08)",
            linecolor="rgba(255,255,255,0.12)",
            tickfont=dict(family='"JetBrains Mono", monospace', size=10),
            title=None,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10),
        ),
        hoverlabel=dict(
            bgcolor=COLORS["bg_card"],
            bordercolor=COLORS["border_glow"],
            font=dict(family='"JetBrains Mono", monospace', size=11, color=COLORS["text_primary"]),
        ),
        showlegend=False,
    )

def bar_colors_from_teams(predictions: list, team_colors: dict | None = None) -> list[str]:
    _tc = team_colors or TEAM_COLORS
    return [_tc.get(str(p.get("team", "")).lower().replace(" ", "_"), COLORS["text_dim"]) for p in predictions]

def apply_theme() -> None:
    import streamlit as st
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st.markdown(BASE_CSS, unsafe_allow_html=True)

def inject_theme(st_module) -> None:
    st_module.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st_module.markdown(BASE_CSS, unsafe_allow_html=True)