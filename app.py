import streamlit as st

from pages.predictions import show as show_predictions
from pages.live_data import show as show_live_data
from pages.driver_analytics import show as show_driver_analytics
from pages.circuit_analysis import show as show_circuit_analysis
from pages.comparisons import show as show_comparisons


def _inject_2026_theme() -> None:
    st.markdown(
        """
<style>
:root{
  --bg0:#050713;
  --bg1:#070a1a;
  --card: rgba(255,255,255,0.06);
  --card2: rgba(255,255,255,0.085);
  --stroke: rgba(255,255,255,0.12);
  --text: rgba(255,255,255,0.92);
  --muted: rgba(255,255,255,0.68);
  --hot:#FF1801;
  --violet:#15154e;
  --cyan:#22d3ee;
  --lime:#a3e635;
  --shadow: 0 18px 60px rgba(0,0,0,0.55);
}

html, body {
  background: radial-gradient(1200px 700px at 20% 10%, rgba(255,24,1,0.18), transparent 55%),
              radial-gradient(1000px 600px at 85% 20%, rgba(34,211,238,0.16), transparent 50%),
              radial-gradient(900px 600px at 50% 90%, rgba(21,21,78,0.22), transparent 45%),
              linear-gradient(180deg, var(--bg0), var(--bg1));
  color: var(--text);
}

.main .block-container {
  padding-top: 2.2rem;
  padding-bottom: 3rem;
}

.bb-header{
  position: relative;
  padding: 1.25rem 1.4rem;
  border: 1px solid var(--stroke);
  background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.03));
  border-radius: 18px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.bb-header:before{
  content:"";
  position:absolute;
  inset:-2px;
  background: radial-gradient(800px 180px at 20% 0%, rgba(255,24,1,0.35), transparent 55%),
              radial-gradient(700px 180px at 80% 0%, rgba(34,211,238,0.28), transparent 60%);
  opacity:.9;
  pointer-events:none;
}

.bb-header h1{
  margin:0;
  font-size: 2rem;
  letter-spacing: 0.3px;
}
.bb-sub{
  margin-top: .35rem;
  color: var(--muted);
  font-size: .98rem;
}

.bb-kbd{
  display:inline-flex;
  gap:.55rem;
  align-items:center;
  padding: .35rem .7rem;
  border-radius: 999px;
  border:1px solid rgba(255,255,255,0.14);
  background: rgba(0,0,0,0.18);
  color: rgba(255,255,255,0.86);
  font-weight: 600;
  font-size: .86rem;
}

.bb-card{
  border: 1px solid var(--stroke);
  background: var(--card);
  border-radius: 16px;
  padding: 1rem 1rem;
  box-shadow: 0 10px 35px rgba(0,0,0,0.35);
}

.bb-divider{
  height:1px;
  background: rgba(255,255,255,0.1);
  margin: 1rem 0;
}

.stRadio > div{
  gap: .5rem;
}

</style>
""",
        unsafe_allow_html=True,
    )


def _page_title(selected: str) -> None:
    st.markdown(
        f"""
<div class="bb-header">
  <div style="display:flex; align-items:flex-start; justify-content:space-between; gap: 1rem;">
    <div>
      <h1>F1MLpredictions <span style="color: var(--cyan);">/ 2026</span></h1>
      <div class="bb-sub">Monte Carlo race predictions + FastF1 live telemetry analytics.</div>
      <div style="margin-top:.7rem; display:flex; flex-wrap:wrap; gap:.6rem;">
        <span class="bb-kbd">⚡ FastF1 Data Layer</span>
        <span class="bb-kbd">🎛️ Streamlit UI</span>
        <span class="bb-kbd">🧠 Probabilistic Engine</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="color: rgba(255,255,255,0.85); font-weight:700; font-size:1.02rem;">
        Selected Module
      </div>
      <div style="margin-top:.4rem; color: white; font-weight:900; font-size:1.12rem;">
        {selected}
      </div>
    </div>
  </div>
</div>
<div class="bb-divider"></div>
""",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="F1MLpredictions 2026 — FastF1 Analytics",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_2026_theme()

    # Sidebar navigation
    st.sidebar.title("🛰️ Garage Console")
    module = st.sidebar.radio(
        "Navigate",
        options=[
            "Predictions (Monte Carlo)",
            "Live Race Data (FastF1)",
            "Driver Analytics",
            "Circuit Analysis",
            "Comparisons",
        ],
        index=0,
    )

    _page_title(module)

    # Slightly nicer container for page content
    with st.container():
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)

        if module.startswith("Predictions"):
            show_predictions()
        elif module.startswith("Live Race Data"):
            show_live_data()
        elif module.startswith("Driver Analytics"):
            show_driver_analytics()
        elif module.startswith("Circuit Analysis"):
            show_circuit_analysis()
        else:
            show_comparisons()

        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
