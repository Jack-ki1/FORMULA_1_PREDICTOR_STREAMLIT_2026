import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import random
import logging

# Setup logger
logger = logging.getLogger(__name__)

from theme import (
    apply_theme,
    COLORS,
    f1_plotly_layout,
    bar_colors_from_teams,
)

from src.engine.predictor import predict as run_predict, PredictionRequest
from src.engine.probability_model import predict_race
from src.engine.prediction_tracker import PredictionTracker
from src.data.circuit_data import get_all_circuits, CIRCUITS
from src.data.driver_data import get_all_drivers
from src.reports.html_report import generate_report
from src.services.accuracy_service import get_accuracy_service

st.set_page_config(
    page_title="F1 Predictor 2026",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()


def clamp_int(x: int, lo: int, hi: int) -> int:
    try:
        x = int(x)
    except Exception:
        x = lo
    return max(lo, min(x, hi))


# FIX #8: Cache model instance with st.cache_resource for thread-safety and performance
@st.cache_resource(show_spinner=False)
def load_prediction_model():
    """Load prediction model once and cache across sessions."""
    from src.engine.predictor import predict as run_predict_fn

    return run_predict_fn


@st.cache_data(ttl=600, show_spinner=False)
def load_circuit_ids() -> list[str]:
    circuit_ids = [c.get("id") for c in get_all_circuits()] if callable(get_all_circuits) else list(CIRCUITS.keys())
    return sorted({c for c in circuit_ids if c})


@st.cache_data(ttl=600, show_spinner=False)
def load_driver_options() -> list[dict]:
    drivers = get_all_drivers() if callable(get_all_drivers) else []
    return [
        {
            "id": d.get("id"),
            "name": d.get("name", d.get("id", "")).replace("_", " ").title(),
            "team": d.get("team", ""),
        }
        for d in drivers
        if isinstance(d, dict) and d.get("id")
    ]


@st.cache_data(ttl=300, show_spinner=False)
def cached_prediction(
    circuit_id: str,
    rain_probability: float | None,
    n_simulations: int,
    seed: int | None,
    grid_items: tuple[tuple[str, int], ...],
    sprint_weekend: bool = False,
) -> dict:
    return run_predict(
        PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            seed=seed,
            grid_overrides=dict(grid_items),
            use_live_data=sprint_weekend,  # Use live data for sprint weekends for better accuracy
        )
    )


def _driver_label(driver: dict) -> str:
    team = driver.get("team")
    suffix = f" - {team.replace('_', ' ').title()}" if team else ""
    return f"{driver.get('name') or driver.get('id')}{suffix}"


def _parse_grid_overrides(selected_driver_ids: list[str]) -> dict[str, int]:
    return {driver_id: pos for pos, driver_id in enumerate(selected_driver_ids, start=1)}


def make_bar_chart(values, title, x_label="Driver", y_label="%"):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(values["x"]),
            y=list(values["y"]),
            marker_color=values.get("color"),
            hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS["text_primary"], size=16)),
        margin=dict(l=40, r=20, t=60, b=120),
        xaxis=dict(title=x_label, tickangle=-45, color=COLORS["text_primary"], gridcolor="rgba(233,239,255,.10)"),
        yaxis=dict(title=y_label, color=COLORS["text_primary"], gridcolor="rgba(233,239,255,.10)"),
        template=None,
        showlegend=False,
    )
    # theme.f1_plotly_layout returns a layout dict; apply it to the existing figure
    fig.update_layout(**f1_plotly_layout(title=title))
    return fig


def _safe_get_circuit_meta(circuit_id: str) -> dict:
    try:
        if isinstance(CIRCUITS, dict) and circuit_id in CIRCUITS:
            return CIRCUITS[circuit_id]
    except Exception:
        pass

    try:
        all_c = get_all_circuits()
        for c in all_c:
            if c.get("id") == circuit_id:
                return c
    except Exception:
        pass

    return {"id": circuit_id, "name": circuit_id.title(), "city": "", "race_date": ""}


def _top_n_drivers(predictions: list[dict], key: str, n: int = 6):
    try:
        return sorted(predictions, key=lambda x: x.get(key, 0), reverse=True)[:n]
    except Exception:
        return predictions[:n]


def make_uncertainty_chart(predictions: list[dict]):
    top = _top_n_drivers(predictions, "win_pct", 8)
    x = [p.get("driver") for p in top]
    y = [float(p.get("win_pct", 0)) for p in top]
    lower = [max(0.0, float(p.get("win_pct", 0)) - float(p.get("win_ci_lower", 0))) for p in top]
    upper = [max(0.0, float(p.get("win_ci_upper", 0)) - float(p.get("win_pct", 0))) for p in top]
    colors = bar_colors_from_teams(top)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=x,
            y=y,
            error_y=dict(type="data", symmetric=False, array=upper, arrayminus=lower),
            marker_color=colors,
            hovertemplate="%{x}<br>Win %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(title="Win Probability With 95% Simulation Uncertainty")
    fig.update_layout(**f1_plotly_layout(title="Win Probability With 95% Simulation Uncertainty"))
    return fig


def make_position_distribution_chart(predictions: list[dict], driver_name: str):
    pred = next((p for p in predictions if p.get("driver") == driver_name), None)
    if not pred:
        return None

    dist = pred.get("position_distribution") or []
    total = sum(dist) or 1

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(range(1, len(dist) + 1)),
            y=[count / total * 100 for count in dist],
            marker_color="rgba(0,229,255,.9)",
            hovertemplate="P%{x}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(title=f"{driver_name} Finish Distribution")
    fig.update_layout(**f1_plotly_layout(title=f"{driver_name} Finish Distribution"))
    return fig


def build_forecast_edges(predictions: list[dict]) -> pd.DataFrame:
    rows = []
    for p in predictions:
        rows.append(
            {
                "Driver": p.get("driver"),
                "Team": p.get("team"),
                "Expected Points": p.get("expected_points", 0),
                "Volatility": p.get("position_std", 0),
                "Top 10 %": p.get("top10_pct", 0),
                "DNF %": p.get("dnf_pct", 0),
                "Edge Score": round(
                    float(p.get("expected_points", 0)) + float(p.get("top10_pct", 0)) / 20 - float(p.get("dnf_pct", 0)) / 10,
                    2,
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("Edge Score", ascending=False)


def _build_predictions_table(predictions: list[dict]) -> pd.DataFrame:
    rows = []
    for idx, p in enumerate(predictions, start=1):
        pos_display = p.get("display_position", idx)
        rows.append(
            {
                "Pos": pos_display,
                "Driver": p.get("driver"),
                "Team": p.get("team"),
                "Exp Pos": p.get("expected_position"),
                "Volatility": p.get("position_std"),
                "Exp Pts": p.get("expected_points"),
                "Win %": p.get("win_pct"),
                "Win 95%": f"{p.get('win_ci_lower', 0)}-{p.get('win_ci_upper', 0)}",
                "Top 3 %": p.get("top3_pct"),
                "Top 10 %": p.get("top10_pct"),
                "DNF %": p.get("dnf_pct"),
                "T/M %": p.get("teammate_beat_pct"),
                "Confidence": p.get("confidence"),
            }
        )

    df = pd.DataFrame(rows)
    if "Pos" in df.columns:
        df = df.sort_values("Pos", ascending=True)
    return df


def render_hero():
    st.markdown(
        """
<div class="bb-hero">
  <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px; flex-wrap:wrap;">
    <div>
      <div class="bb-title">F1 Predictor 2026 🏎️</div>
      <div class="bb-sub">Race-night probabilistic forecasting — honest simulations, F1 energy.</div>
      <div class="bb-badges">
        <div class="bb-badge">Telemetry-grade visuals</div>
        <div class="bb-badge">Monte Carlo Engine</div>
        <div class="bb-badge">Strategy-aware probabilities</div>
      </div>
    </div>
    <div style="min-width:260px; max-width:360px;">
      <div class="bb-telemetry">
        <div style="font-weight:1000; letter-spacing:.3px; margin-bottom:6px;">🏁 Today’s Brief</div>
        <div style="color:rgba(233,239,255,.86); font-weight:800; font-size:.95rem; line-height:1.5;">
          Pick a circuit • dial the rain • set simulations • see win/podium/risk in the pit-wall.
        </div>
      </div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_mode_sidebar():
    st.sidebar.markdown(
        """
<div style="font-weight:1000; letter-spacing:.4px; margin:8px 0 4px; color:rgba(233,239,255,.95);">
  🏎️ Race Control
</div>
<div style="color:rgba(233,239,255,.78); font-weight:700; font-size:.92rem; line-height:1.4;">
  Choose a mode then tune the garage.
</div>
""",
        unsafe_allow_html=True,
    )

    circuit_ids = load_circuit_ids()
    driver_options = [d["id"] for d in load_driver_options()]

    mode = st.sidebar.radio(
        "Mode",
        ["Race", "H2H", "Constructor", "Championship", "Accuracy", "Download"],
        index=0,
        format_func=lambda x: x,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Simulation settings")

    return mode, circuit_ids, driver_options, 10000, 0.10


def render_race_mode(circuit_ids: list[str], default_circuit: str | None, rain_probability: float, sims: int):
    """Render race mode with Friday-Saturday-Sunday tabs, each with independent simulations."""
    
    # Main configuration panel
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>Race Weekend Configuration</div></div>",
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        default_circuit_id = default_circuit if default_circuit in circuit_ids else (circuit_ids[0] if circuit_ids else None)
        selected_circuit = st.selectbox(
            "🏁 Circuit",
            options=circuit_ids,
            index=circuit_ids.index(default_circuit_id) if default_circuit_id else 0,
            format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
            key="main_circuit_selector",
        )
    
    # ── PHASE 5: DATA AVAILABILITY INDICATOR ──
    try:
        from src.data.fastf1_integration import get_prediction_data_availability
        
        data_status = get_prediction_data_availability(selected_circuit)
        
        # Display smart data availability badge
        strategy_colors = {
            "historical_only": "gray",
            "practice_partial": "blue",
            "practice_enhanced": "orange",
            "full_data": "green",
            "post_race_analysis": "purple",
        }
        
        color = strategy_colors.get(data_status['recommended_strategy'], "gray")
        
        # Map colors to RGB values
        color_map = {
            "gray": ("128,128,128", "808080", "666666"),
            "blue": ("0,123,255", "007BFF", "0056B3"),
            "orange": ("255,165,0", "FFA500", "CC8400"),
            "green": ("40,167,69", "28A745", "1E7E34"),
            "purple": ("128,0,128", "800080", "600060"),
        }
        
        rgb, hex_bg, hex_text = color_map.get(color, color_map["gray"])
        
        data_sources_str = ', '.join([s.replace('_', ' ').title() for s in data_status['data_sources']])
        confidence_str = f" | Confidence boost: +{data_status['confidence_boost']*100:.0f}%" if data_status['confidence_boost'] > 0 else ""
        
        st.markdown(
            f"""
            <div style='
                padding: 12px;
                margin: 8px 0;
                border-radius: 8px;
                background-color: rgba({rgb}, 0.1);
                border-left: 4px solid #{hex_bg};
            '>
                <strong style='color: #{hex_text};'>
                    {data_status['message']}
                </strong><br>
                <small style='color: #666;'>
                    Data sources: {data_sources_str}{confidence_str}
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        logger.debug(f"Data availability check failed: {e}")
    
    with col2:
        rain_pct = st.slider("🌧️ Rain Probability (%)", min_value=0, max_value=100, value=int(rain_probability * 100), step=5, key="main_rain_slider")
        rain_probability_main = rain_pct / 100.0
    
    with col3:
        n_simulations = st.number_input("🎲 Simulations", min_value=1000, max_value=50000, value=int(sims), step=1000, key="main_sims_input")
    
    # Sprint weekend toggle
    circuit_meta = _safe_get_circuit_meta(selected_circuit)
    is_sprint_default = circuit_meta.get("sprint_weekend", False)
    sprint_weekend = st.toggle(
        "🏁 Sprint Weekend Format",
        value=is_sprint_default,
        help="Sprint weekends: Saturday has Sprint Shootout + Sprint Race. Standard: Saturday has Qualifying only."
    )
    
    # Load data needed for sub-sessions
    driver_options_data = load_driver_options()
    driver_records = [d for d in driver_options_data] # Using the full dict objects
    driver_lookup = {d["id"]: d for d in driver_options_data}
    
    # Initialize grid overrides for session contexts
    grid_overrides = {}
    
    # FIX F-03: Load qualifying grid from session state if available (persisted from Saturday)
    if "qualifying_grid" in st.session_state:
        grid_overrides = st.session_state["qualifying_grid"].copy()
    
    # RACE WEEKEND TABS - Each with independent controls
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    
    friday_tab, saturday_tab, sunday_tab = st.tabs([
        "🔧 Friday - Practice Sessions",
        "⏱️ Saturday - Qualifying & Sprint",
        "🏆 Sunday - Grand Prix",
    ])
    
    with friday_tab:
        _render_friday_session(circuit_ids, selected_circuit, driver_records, driver_lookup, grid_overrides, rain_probability_main, n_simulations)
    
    with saturday_tab:
        _render_saturday_session(circuit_ids, selected_circuit, driver_records, driver_lookup, grid_overrides, sprint_weekend)
    
    with sunday_tab:
        _render_sunday_session(circuit_ids, selected_circuit, driver_records, driver_lookup, grid_overrides, rain_probability_main, n_simulations)


def _render_friday_session(circuit_ids: list, default_circuit: str | None, driver_records: list, driver_lookup: dict, grid_overrides: dict, rain_probability: float, n_simulations: int):
    """Friday Practice Sessions - Independent simulation controls."""
    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--blue-secondary);'></span>Friday Practice Analysis</div></div>",
        unsafe_allow_html=True,
    )
    
    st.info(
        "🔧 **Friday Practice**: Three sessions (FP1, FP2, FP3) where teams gather baseline data, test setups, "
        "and evaluate tire compounds. No points awarded, but critical for race weekend strategy."
    )
    
    # Session selector only (circuit/rain/sims already at top)
    fp_session_type = st.selectbox("Practice Session", options=["FP1", "FP2", "FP3"], index=1, key="fp_session")
    
    # Session description
    session_info = {
        "FP1": "First practice (60min). Teams explore basic setup with heavy fuel loads. Least representative of true pace.",
        "FP2": "Second practice (60-90min). Most important! Race simulations + qualifying prep. Best pace indicator.",
        "FP3": "Third practice (60min). Final tune-up before qualifying. Focused on qualifying simulation runs.",
    }
    st.caption(session_info[fp_session_type])
    
    # Run button
    run_fp = st.button("🔧 Run Practice Simulation", type="primary", width='stretch', key="run_fp")
    
    if not run_fp:
        st.info("Configure race weekend settings at top and run practice simulation.")
        return
    
    with st.spinner(f"Simulating {fp_session_type} at {_safe_get_circuit_meta(default_circuit)['name']}..."):
        try:
            # FIX F-01: Route Friday through real prediction engine instead of random.seed(42)
            from src.engine.predictor import predict as run_predict_fn, PredictionRequest
            
            # Session-specific noise levels for practice sessions
            # FP1: High noise (exploration, heavy fuel, setup testing)
            # FP2: Medium noise (race simulations, most representative)
            # FP3: Low noise (qualifying prep, focused runs)
            session_noise_multiplier = {
                "FP1": 1.5,   # Highest variance
                "FP2": 1.0,   # Baseline
                "FP3": 0.8,   # Lowest variance
            }
            
            # Use fewer simulations for practice (faster, less critical than race)
            practice_sims = max(1000, int(n_simulations * 0.2))
            
            result = run_predict_fn(
                PredictionRequest(
                    circuit_id=default_circuit,
                    rain_probability=rain_probability,
                    n_simulations=practice_sims,
                    seed=None,  # No fixed seed for realistic variance
                    grid_overrides={},  # No grid overrides for practice
                )
            )
            
            predictions = result.get("predictions", [])
            
            # Generate practice-specific lap times from composite scores
            # Higher composite score → faster expected lap time
            practice_results = []
            base_lap_time = 90.0  # Base lap time in seconds (will vary by circuit)
            
            # Get circuit-specific base time
            circuit_meta = _safe_get_circuit_meta(default_circuit)
            if "typical_lap_time" in circuit_meta:
                base_lap_time = float(circuit_meta["typical_lap_time"])
            
            for pred in predictions[:15]:  # Top 15 drivers for practice
                driver_id = pred.get("driver_id")
                driver_data = next((d for d in driver_records if d["id"] == driver_id), None)
                
                if not driver_data:
                    continue
                
                # Composite score drives base pace (higher = faster)
                composite = pred.get("composite_score", 0.5)
                
                # Convert composite to lap time offset (0.5 → 0s, 1.0 → -2s, 0.0 → +2s)
                pace_offset = (0.5 - composite) * 4.0
                
                # Apply session-specific noise
                import random
                noise_sigma = 0.15 * session_noise_multiplier[fp_session_type]
                noise = random.gauss(0, noise_sigma)
                
                predicted_lap = base_lap_time + pace_offset + noise
                
                # Simulate laps completed (varies by session)
                laps_by_session = {"FP1": (18, 28), "FP2": (25, 35), "FP3": (20, 30)}
                min_laps, max_laps = laps_by_session[fp_session_type]
                laps_completed = random.randint(min_laps, max_laps)
                
                # Reliability based on team/driver experience
                reliability_roll = random.random()
                if reliability_roll < 0.70:
                    reliability = "✅ Clean Run"
                elif reliability_roll < 0.90:
                    reliability = "⚠️ Minor Issue"
                else:
                    reliability = "❌ Early Stop"
                
                # Tire compound tested (weighted toward session focus)
                tire_weights = {
                    "FP1": {"Hard": 0.5, "Medium": 0.35, "Soft": 0.15},  # Long runs
                    "FP2": {"Medium": 0.4, "Hard": 0.35, "Soft": 0.25},  # Race sim + quali prep
                    "FP3": {"Soft": 0.45, "Medium": 0.40, "Hard": 0.15},  # Quali focus
                }
                tire_choices = list(tire_weights[fp_session_type].keys())
                tire_probs = list(tire_weights[fp_session_type].values())
                primary_compound = random.choices(tire_choices, weights=tire_probs, k=1)[0]
                
                practice_results.append({
                    "Pos": 0,  # Will be set after sorting
                    "Driver": _driver_label(driver_data),
                    "Team": driver_data.get("team", "").replace("_", " ").title(),
                    "Best Lap": f"{predicted_lap:.3f}s",
                    "Gap": "",  # Will calculate after sorting
                    "Laps": laps_completed,
                    "Primary Tire": primary_compound,
                    "Reliability": reliability,
                    "Pace Rating": min(10.0, max(5.0, 7.5 + (composite - 0.5) * 5)),
                })
            
            # Sort by best lap time
            practice_results.sort(key=lambda x: float(x["Best Lap"].replace('s', '')))
            
            # Calculate gaps
            leader_time = float(practice_results[0]["Best Lap"].replace('s', ''))
            for i, result in enumerate(practice_results):
                current_time = float(result["Best Lap"].replace('s', ''))
                gap = current_time - leader_time
                result["Gap"] = f"+{gap:.3f}s" if gap > 0 else "LEADER"
                result["Pos"] = i + 1
            
            # Display results
            st.markdown(f"### {fp_session_type} Results - {_safe_get_circuit_meta(default_circuit)['name']}")
            
            df_practice = pd.DataFrame([
                {
                    "Pos": r["Pos"],
                    "Driver": r["Driver"],
                    "Team": r["Team"],
                    "Best Lap": r["Best Lap"],
                    "Gap": r["Gap"],
                    "Laps": r["Laps"],
                    "Tire": r["Primary Tire"],
                    "Status": r["Reliability"],
                    "Pace": f"{r['Pace Rating']:.1f}/10",
                }
                for r in practice_results[:12]
            ])
            
            st.dataframe(df_practice, hide_index=True, width='stretch')
            
            # Key insights
            st.markdown("### 🔍 Key Insights")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Fastest Driver", practice_results[0]["Driver"])
            with col_b:
                avg_laps = sum(r["Laps"] for r in practice_results) / len(practice_results)
                st.metric("Avg Laps Completed", f"{avg_laps:.0f}")
            with col_c:
                clean_runs = sum(1 for r in practice_results if "Clean" in r["Reliability"])
                st.metric("Clean Runs", f"{clean_runs}/{len(practice_results)}")
            
            # Tire analysis
            st.markdown("### 🛞 Tire Compound Analysis")
            tire_counts = {}
            for r in practice_results:
                tire = r["Primary Tire"]
                tire_counts[tire] = tire_counts.get(tire, 0) + 1
            
            tire_df = pd.DataFrame([
                {"Compound": k, "Teams Testing": v, "Percentage": f"{v/len(practice_results)*100:.0f}%"}
                for k, v in sorted(tire_counts.items())
            ])
            st.dataframe(tire_df, hide_index=True, width='stretch')
            
            # Practice-to-race correlation
            st.divider()
            st.markdown(
                "**📊 Practice-to-Race Correlation:**\n"
                f"- FP1: ~60% predictive of race pace\n"
                f"- FP2: ~75-80% predictive (most reliable)\n"
                f"- FP3: ~70% predictive (qualifying-focused)\n\n"
                f"**Weather Impact**: {'⚠️ HIGH - Wet track reduces practice relevance' if rain_probability > 0.3 else '✅ LOW - Dry conditions ideal for data collection'}"
            )
            
        except Exception as e:
            st.error(f"Practice simulation failed: {e}")
            import traceback
            st.code(traceback.format_exc())


def _render_saturday_session(circuit_ids: list, default_circuit: str | None, driver_records: list, driver_lookup: dict, grid_overrides: dict, sprint_weekend: bool):
    """Saturday Qualifying & Sprint - Independent simulation controls."""
    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--purple-hyper);'></span>Saturday Qualifying & Sprint</div></div>",
        unsafe_allow_html=True,
    )
    
    if sprint_weekend:
        st.info(
            "🏁 **Sprint Weekend Saturday**: Sprint Shootout (short qualifying) determines Sprint grid, "
            "then ~100km Sprint Race awards championship points (8-7-6-5-4-3-2-1 for top 8)."
        )
    else:
        st.info(
            "⏱️ **Standard Saturday**: Traditional 3-session knockout qualifying (Q1/Q2/Q3) determines Sunday's starting grid. "
            "No points awarded, but pole position crucial for race advantage."
        )
    
    # Seed input only (circuit/rain/sims already at top)
    sat_seed = st.number_input("Seed", min_value=0, max_value=999999, value=42, step=1, key="sat_seed")
    
    # Run button
    run_sat = st.button("⏱️ Run Saturday Simulation", type="primary", width='stretch', key="run_sat")
    
    if not run_sat:
        st.info("Configure race weekend settings at top and run Saturday simulation.")
        return
    
    with st.spinner(f"Simulating Saturday at {_safe_get_circuit_meta(default_circuit)['name']}..."):
        try:
            import random
            random.seed(sat_seed)
            
            if sprint_weekend:
                # SPRINT WEEKEND FORMAT
                sprint_tab, shootout_tab = st.tabs(["🏃 Sprint Race", "⏱️ Sprint Shootout"])
                
                with shootout_tab:
                    st.subheader("Sprint Shootout Qualifying Results")
                    st.caption("SQ1 (12min, all drivers) → SQ2 (10min, top 10) → SQ3 (8min, top 8)")
                    
                    # Generate qualifying predictions
                    quali_results = []
                    for idx, driver in enumerate(driver_records[:20]):
                        # Qualifying performance factors
                        single_lap_pace = random.uniform(-0.4, 0.4)
                        driver_quali_skill = random.uniform(-0.2, 0.2)
                        
                        predicted_pos = max(1, min(20, idx + 1 + int(single_lap_pace * 3)))
                        makes_q3 = predicted_pos <= 10
                        
                        quali_results.append({
                            "Pos": predicted_pos,
                            "Driver": _driver_label(driver),
                            "Team": driver.get("team", "").replace("_", " ").title(),
                            "Session": "SQ3" if predicted_pos <= 8 else "SQ2" if predicted_pos <= 10 else "SQ1",
                            "Pole Chance": f"{max(1, 20 - idx*2):.0f}%" if idx < 5 else "<1%",
                            "Top 8": "✅" if predicted_pos <= 8 else "❌",
                        })
                    
                    quali_results.sort(key=lambda x: x["Pos"])
                    df_quali = pd.DataFrame(quali_results[:10])
                    st.dataframe(df_quali, hide_index=True, width='stretch')
                    
                    # Pole prediction
                    st.markdown(f"**🏆 Pole Favorite**: {quali_results[0]['Driver']} ({quali_results[0]['Pole Chance']})")
                
                with sprint_tab:
                    st.subheader("Sprint Race Predictions")
                    st.caption("~100km race, no pit stops required. Points: 8-7-6-5-4-3-2-1 for top 8.")
                    
                    # Generate sprint race predictions
                    sprint_results = []
                    for idx, driver in enumerate(driver_records[:12]):
                        sprint_win_prob = max(2, 18 - idx*2)
                        points = max(0, 8 - idx) if idx < 8 else 0
                        
                        sprint_results.append({
                            "Pos": idx + 1,
                            "Driver": _driver_label(driver),
                            "Win Probability": f"{sprint_win_prob}%",
                            "Points Expected": f"{points} pts" if points > 0 else "0",
                            "Overtaking Risk": random.choice(["Low", "Medium", "High"]),
                        })
                    
                    df_sprint = pd.DataFrame(sprint_results[:8])
                    st.dataframe(df_sprint, hide_index=True, width='stretch')
                    
                    st.markdown(
                        "**Sprint Strategy Notes:**\n"
                        "- Aggressive starts critical\n"
                        "- DRS trains likely on tight circuits\n"
                        "- No tire degradation concerns (short race)\n"
                        "- Championship points at stake!"
                    )
            
            else:
                # STANDARD QUALIFYING FORMAT
                st.subheader("Qualifying Predictions")
                st.caption("Q1 (18min, eliminate P16-P20) → Q2 (15min, eliminate P11-P15) → Q3 (12min, battle for pole)")
                
                # Generate qualifying predictions
                quali_results = []
                for idx, driver in enumerate(driver_records[:20]):
                    quali_bias = random.uniform(-0.3, 0.3)
                    predicted_pos = max(1, min(20, idx + 1 + int(quali_bias * 2)))
                    
                    quali_results.append({
                        "Pos": predicted_pos,
                        "Driver": _driver_label(driver),
                        "Team": driver.get("team", "").replace("_", " ").title(),
                        "Progression": "Q3" if predicted_pos <= 10 else "Q2" if predicted_pos <= 15 else "Q1",
                        "Pole Chance": f"{max(1, 15 - idx*1.5):.1f}%" if idx < 5 else "<1%",
                        "Q3 Lock": "✅" if predicted_pos <= 10 else "❌",
                    })
                
                quali_results.sort(key=lambda x: x["Pos"])
                
                # Show Q3 participants prominently
                q3_drivers = [r for r in quali_results if r["Progression"] == "Q3"]
                st.markdown(f"### 🔥 Q3 Participants (Top 10)")
                df_q3 = pd.DataFrame(q3_drivers)
                st.dataframe(df_q3, hide_index=True, width='stretch')
                
                # Pole spotlight
                st.divider()
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Pole Favorite", quali_results[0]["Driver"])
                with col_b:
                    st.metric("Pole Probability", quali_results[0]["Pole Chance"])
                with col_c:
                    pole_pct = float(quali_results[0]["Pole Chance"].replace('%',''))
                    st.metric("Front Row Lock", "✅ Likely" if pole_pct > 20 else "⚠️ Competitive")
                
                st.caption("📊 Historical: Pole wins ~40% of races (Monaco: ~60%, Spa: ~25%)")
        
        except Exception as e:
            st.error(f"Saturday simulation failed: {e}")
            import traceback
            st.code(traceback.format_exc())


def _render_sunday_session(circuit_ids: list, default_circuit: str | None, driver_records: list, driver_lookup: dict, grid_overrides: dict, rain_probability: float, n_simulations: int):
    """Sunday Grand Prix - Full race prediction with Monte Carlo simulation."""
    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--red-f1);'></span>Sunday Grand Prix Prediction</div></div>",
        unsafe_allow_html=True,
    )
    
    st.info(
        "🏆 **Sunday Grand Prix**: The main event! ~305km race distance. Championship points: "
        "25-18-15-12-10-8-6-4-2-1 for top 10, plus 1pt for fastest lap (if finishing in top 10)."
    )
    
    # Seed toggle and value only (circuit/rain/sims already at top)
    sun_seed_toggle = st.checkbox("Use Fixed Seed", value=False, key="sun_seed_toggle")
    sun_seed = st.number_input("Seed Value", min_value=0, max_value=999999, value=0, key="sun_seed_val") if sun_seed_toggle else None
    
    # Grid selection for Sunday race
    st.markdown(
        "<div style='margin-top:20px; font-weight:800; color:var(--text-primary);'>🔧 Known Starting Grid (P1–P10)</div>",
        unsafe_allow_html=True,
    )
    st.caption("Specify grid positions after qualifying to improve race prediction accuracy. Leave empty for model-based predictions.")
    
    grid_cols = st.columns(5)
    sun_grid_overrides = {}
    
    for i, pos in enumerate([1, 2, 3, 4, 5]):
        with grid_cols[i]:
            selected = st.selectbox(
                f"P{pos}",
                options=[""] + [d["id"] for d in driver_records],
                format_func=lambda x: _driver_label(driver_lookup.get(x, {"id": x})) if x else "— Auto —",
                key=f"sun_grid_p{pos}",
                index=0,
            )
            if selected:
                sun_grid_overrides[selected] = pos
    
    grid_cols2 = st.columns(5)
    for i, pos in enumerate([6, 7, 8, 9, 10]):
        with grid_cols2[i]:
            selected = st.selectbox(
                f"P{pos}",
                options=[""] + [d["id"] for d in driver_records],
                format_func=lambda x: _driver_label(driver_lookup.get(x, {"id": x})) if x else "— Auto —",
                key=f"sun_grid_p{pos}",
                index=0,
            )
            if selected:
                sun_grid_overrides[selected] = pos
    
    if sun_grid_overrides:
        st.success(f"✓ Grid override applied: {len(sun_grid_overrides)} positions specified")
    
    # Merge with any existing grid_overrides
    final_grid_overrides = {**grid_overrides, **sun_grid_overrides}
    
    # Run button
    run_sun = st.button("🏆 Run Grand Prix Simulation", type="primary", width='stretch', key="run_sun")
    
    if not run_sun:
        st.info("Configure race weekend settings at top and run Grand Prix simulation.")
        return
    
    with st.spinner(f"Running Monte Carlo simulation ({n_simulations:,} races) at {_safe_get_circuit_meta(default_circuit)['name']}..."):
        try:
            from src.engine.predictor import predict as run_predict_fn, PredictionRequest
            
            # Use final_grid_overrides which includes Sunday-specific selections
            result = run_predict_fn(
                PredictionRequest(
                    circuit_id=default_circuit,
                    rain_probability=rain_probability,
                    n_simulations=int(n_simulations),
                    seed=int(sun_seed) if sun_seed else None,
                    grid_overrides=final_grid_overrides,
                )
            )
            
            # Extract meta first (needed for accuracy tracking)
            meta = result.get("meta", {})
            
            # Track prediction for accuracy monitoring
            try:
                import uuid
                from datetime import datetime
                prediction_id = str(uuid.uuid4())[:8]
                
                accuracy_service = get_accuracy_service()
                accuracy_service.log_prediction(
                    prediction_id=prediction_id,
                    circuit_id=default_circuit,
                    predictions=result.get("predictions", []),
                    metadata={
                        "rain_probability": rain_probability,
                        "n_simulations": n_simulations,
                        "timestamp": datetime.now().isoformat(),
                        "qualifying_used": meta.get("qualifying_data_used", False),
                    }
                )
                
                # Store prediction_id in session state for later evaluation
                st.session_state["last_prediction_id"] = prediction_id
                logger.info(f"Logged prediction {prediction_id} for accuracy tracking")
            except Exception as e:
                logger.warning(f"Failed to log prediction for accuracy tracking: {e}")
            
            preds_sorted = sorted(
                result.get("predictions", []),
                key=lambda x: (x.get("expected_position") or x.get("predicted_position", 999), -x.get("win_pct", 0)),
            )
            for p_i, p in enumerate(preds_sorted, start=1):
                p["display_position"] = p_i
            
            podium = result.get("podium_predictions", [])
            favorite = podium[0] if podium else "-"
            
            # ── SHOW QUALIFYING DATA STATUS (NEW) ──
            qualifying_used = meta.get("qualifying_data_used", False)
            grid_count = meta.get("grid_positions_count", 0)
            
            if qualifying_used and grid_count > 0:
                st.success(
                    f"✅ **Using Actual Qualifying Results**\n\n"
                    f"Grid positions from Saturday's qualifying session ({grid_count} drivers). "
                    "This significantly improves prediction accuracy by eliminating grid uncertainty."
                )
                
                # Show top 5 grid positions as quick reference
                with st.expander("📋 View Qualifying Grid (Top 10)", expanded=False):
                    try:
                        from src.data.fastf1_integration import fetch_qualifying_grid
                        from src.data.calendar_2026 import CALENDAR_2026
                        
                        race_info = next((r for r in CALENDAR_2026 if r['circuit'] == default_circuit), None)
                        if race_info:
                            season = int(race_info['date'][:4])
                            qual_data = fetch_qualifying_grid(season, default_circuit)
                            
                            if qual_data and qual_data.get('grid'):
                                grid_df = pd.DataFrame([
                                    {
                                        "Pos": g['position'],
                                        "Driver": g['driver_id'],
                                        "Team": g.get('team', 'N/A'),
                                        "Q3 Time": f"{g['q3_time']:.3f}s" if g.get('q3_time') else "N/A",
                                        "Gap to Pole": f"+{g['gap_to_pole']:.3f}s" if g.get('gap_to_pole') else "POLE",
                                    }
                                    for g in qual_data['grid'][:10]
                                ])
                                st.dataframe(grid_df, hide_index=True, use_container_width=True)
                                
                                st.caption(f"Pole Position: {qual_data.get('pole_position', 'N/A')}")
                    except Exception as e:
                        st.warning(f"Could not display qualifying grid: {e}")
            
            elif grid_count > 0:
                st.info(f"ℹ️ Using custom grid overrides: {grid_count} positions specified")
            else:
                st.info(
                    "ℹ️ **Predicted Grid**: Qualifying results not yet available. "
                    "Predictions based on historical performance and season form. "
                    "Check back after Saturday qualifying for improved accuracy!"
                )
            
            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Predicted Winner", str(favorite))
            c2.metric("Model Confidence", f"{meta.get('overall_model_confidence', 0) * 100:.0f}%")
            c3.metric("Safety Car Risk", f"{meta.get('safety_car_probability', 0) * 100:.0f}%")
            c4.metric("Circuit", _safe_get_circuit_meta(default_circuit)['name'])
            
            # Data source info
            data_source = meta.get("data_source", "static_fallback")
            if data_source == "fastf1_with_qualifying":
                st.caption(f"📡 Data Source: FastF1 Live + Qualifying Results | Updated: {meta.get('data_freshness', 'N/A')[:16]}")
            elif data_source == "fastf1_live":
                st.caption(f"📡 Data Source: FastF1 Live Data | Updated: {meta.get('data_freshness', 'N/A')[:16]}")
            else:
                st.caption("📡 Data Source: Historical Database & Season Trends")
            
            if grid_overrides:
                st.caption(f"✓ Grid override applied: {len(grid_overrides)} positions")
            
            # Race results tabs
            overview_tab, uncertainty_tab, value_tab, table_tab = st.tabs([
                "📊 Overview",
                "📈 Uncertainty",
                "💰 Value Board",
                "📋 Full Results",
            ])
            
            with overview_tab:
                t_win = _top_n_drivers(preds_sorted, "win_pct", 6)
                st.plotly_chart(
                    make_bar_chart(
                        {
                            "x": [p.get("driver") for p in t_win],
                            "y": [float(p.get("win_pct", 0)) for p in t_win],
                            "color": bar_colors_from_teams(t_win),
                        },
                        "Win Probability (Top 6)",
                    ),
                    width='stretch',
                )
                
                dnf_sorted = sorted(preds_sorted, key=lambda x: x.get("dnf_pct", 0), reverse=True)[:6]
                st.plotly_chart(
                    make_bar_chart(
                        {
                            "x": [p.get("driver") for p in dnf_sorted],
                            "y": [float(p.get("dnf_pct", 0)) for p in dnf_sorted],
                            "color": ["rgba(255,75,92,.9)" for _ in dnf_sorted],
                        },
                        "DNF Risk (Top 6)",
                        y_label="DNF %",
                    ),
                    width='stretch',
                )
            
            with uncertainty_tab:
                st.plotly_chart(make_uncertainty_chart(preds_sorted), width='stretch')
                driver_names = [p.get("driver") for p in preds_sorted if p.get("driver")]
                selected_driver = st.selectbox("Select Driver", options=driver_names, key="sun_driver_select")
                fig = make_position_distribution_chart(preds_sorted, selected_driver)
                if fig:
                    st.plotly_chart(fig, width='stretch')
            
            with value_tab:
                st.dataframe(build_forecast_edges(preds_sorted), width='stretch', hide_index=True)
            
            with table_tab:
                st.dataframe(_build_predictions_table(preds_sorted), width='stretch', hide_index=True)
            
            likely_top_surprises = result.get("likely_top_surprises") or []
            if likely_top_surprises:
                st.info("⭐ Potential overperformers: " + ", ".join(map(str, likely_top_surprises)))
            
        except Exception as e:
            st.error(f"Race simulation failed: {e}")
            import traceback
            st.code(traceback.format_exc())


def render_h2h_mode(driver_options: list[str], circuit_ids: list[str], sims: int, rain_probability: float):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>🥊 Enhanced Rivalry Analysis</div></div>",
        unsafe_allow_html=True,
    )
    
    st.info(
        "🔍 **Head-to-Head Battle Simulator**: Compare two drivers across multiple dimensions including "
        "qualifying pace, race craft, tire management, and circuit-specific performance."
    )
    
    # Load driver lookup for teammate detection and labels
    driver_lookup = {d["id"]: d for d in load_driver_options()}
    
    # Driver selection with team indicators
    col1, col2 = st.columns(2)
    with col1:
        d1 = st.selectbox(
            "🚗 Driver 1",
            options=driver_options,
            index=0 if driver_options else None,
            format_func=lambda x: _driver_label(driver_lookup.get(x, {"id": x})),
            key="h2h_d1"
        )
    with col2:
        d2 = st.selectbox(
            "🚗 Driver 2",
            options=driver_options,
            index=1 if len(driver_options) > 1 else 0 if driver_options else None,
            format_func=lambda x: _driver_label(driver_lookup.get(x, {"id": x})),
            key="h2h_d2",
        )
    
    if not d1 or not d2:
        st.warning("⚠️ Please select two drivers for comparison!")
        return

    if d1 == d2:
        st.warning("⚠️ Please select two different drivers for comparison!")
        return
    
    d1_data = driver_lookup.get(d1, {})
    d2_data = driver_lookup.get(d2, {})
    
    are_teammates = d1_data.get("team") == d2_data.get("team") and d1_data.get("team")
    
    if are_teammates:
        st.success(f"🤝 **Teammate Battle**: Both drivers race for {d1_data['team'].replace('_', ' ').title()}")
    else:
        st.info(f"⚔️ **Rivalry**: {d1_data.get('team', 'Unknown').replace('_', ' ').title()} vs {d2_data.get('team', 'Unknown').replace('_', ' ').title()}")
    
    circuit_id = st.selectbox(
        "🏁 Circuit",
        options=circuit_ids,
        index=0 if circuit_ids else None,
        format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
        key="h2h_circuit",
    )
    
    with st.expander("⚙️ Advanced Settings"):
        rain_choice = st.toggle("🌧️ Rain enabled", value=True, key="h2h_rain_toggle")
        rain_prob = rain_probability if rain_choice else None
        
        n_simulations = st.number_input("# Simulations", min_value=1000, max_value=50000, value=int(sims), step=1000, key="h2h_sims")
        
        qualifying_weight = st.slider(
            "Qualifying Performance Weight",
            min_value=0,
            max_value=100,
            value=40,
            step=5,
            help="How much qualifying position affects race outcome"
        )
    
    run = st.button("⚔️ Run H2H Battle Simulation", type="primary", width='stretch', key="h2h_run")
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    
    if not run:
        st.info("Select two drivers and configure settings above to start the rivalry analysis.")
        return
    
    with st.spinner(f"Simulating {n_simulations:,} races at {_safe_get_circuit_meta(circuit_id)['name']}…"):
        try:
            sim_result = predict_race(
                circuit_id=circuit_id,
                rain_probability=rain_prob,
                n_simulations=int(n_simulations),
            )
        except Exception as e:
            st.error(f"H2H prediction failed: {e}")
            return
    
    predictions = {p["driver_id"]: p for p in sim_result.get("predictions", [])}
    if d1 not in predictions or d2 not in predictions:
        st.error("One or both drivers were not found in the simulation output.")
        return
    
    p1 = predictions[d1]
    p2 = predictions[d2]
    
    dist1 = p1.get("position_distribution", [])
    dist2 = p2.get("position_distribution", [])
    
    if dist1 and dist2:
        total1 = sum(dist1) or 1
        total2 = sum(dist2) or 1
        prob_dist1 = [c / total1 for c in dist1]
        prob_dist2 = [c / total2 for c in dist2]
        
        p_d1_ahead = 0.0
        for pos1 in range(len(prob_dist1)):
            for pos2 in range(len(prob_dist2)):
                if pos1 < pos2:
                    p_d1_ahead += prob_dist1[pos1] * prob_dist2[pos2]
        p_d1_ahead = max(0.0, min(1.0, p_d1_ahead))
    else:
        p_d1_ahead = 0.5
    
    d1_name = p1.get("driver_name") or p1.get("driver_id")
    d2_name = p2.get("driver_name") or p2.get("driver_id")
    
    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--red-f1); box-shadow: 0 0 0 6px rgba(232,0,45,.12);'></span>Battle Outcome</div></div>",
        unsafe_allow_html=True,
    )
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(f"{d1_name} Finishes Ahead", f"{p_d1_ahead * 100:.1f}%")
    with col_b:
        st.metric("Tie Probability", f"{abs(p_d1_ahead - 0.5) * 20:.1f}%")
    with col_c:
        st.metric(f"{d2_name} Finishes Ahead", f"{(1 - p_d1_ahead) * 100:.1f}%")
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[d1_name, d2_name],
            y=[p_d1_ahead * 100, (1 - p_d1_ahead) * 100],
            marker_color=["rgba(232,0,45,.95)", "rgba(0,229,204,.95)"],
            hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(**f1_plotly_layout(title="Finishes Ahead Probability"))
    st.plotly_chart(fig, width='stretch')
    
    h2h_overview, h2h_positions, h2h_scenarios = st.tabs([
        "📊 Performance Overview",
        "📍 Position Distribution",
        "🎯 Race Scenarios"
    ])
    
    with h2h_overview:
        st.subheader("Driver Comparison Metrics")
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            st.markdown(f"**{d1_name}**")
            st.metric("Expected Position", f"{p1.get('expected_position_float', p1.get('predicted_position', '-')):.1f}")
            st.metric("Win Probability", f"{p1.get('win_pct', 0):.1f}%")
            st.metric("Podium Probability", f"{p1.get('top3_pct', 0):.1f}%")
            st.metric("Points Finish", f"{p1.get('top10_pct', 0):.1f}%")
            st.metric("DNF Risk", f"{p1.get('dnf_pct', 0):.1f}%")
        
        with comp_col2:
            st.markdown(f"**{d2_name}**")
            st.metric("Expected Position", f"{p2.get('expected_position_float', p2.get('predicted_position', '-')):.1f}")
            st.metric("Win Probability", f"{p2.get('win_pct', 0):.1f}%")
            st.metric("Podium Probability", f"{p2.get('top3_pct', 0):.1f}%")
            st.metric("Points Finish", f"{p2.get('top10_pct', 0):.1f}%")
            st.metric("DNF Risk", f"{p2.get('dnf_pct', 0):.1f}%")
    
    with h2h_positions:
        st.subheader("Position Probability Distributions")
        
        positions = list(range(1, 21))
        
        fig_pos = go.Figure()
        fig_pos.add_trace(
            go.Bar(
                name=d1_name,
                x=positions,
                y=[dist1[i-1] if i-1 < len(dist1) else 0 for i in positions],
                marker_color="rgba(232,0,45,.7)",
            )
        )
        fig_pos.add_trace(
            go.Bar(
                name=d2_name,
                x=positions,
                y=[dist2[i-1] if i-1 < len(dist2) else 0 for i in positions],
                marker_color="rgba(0,229,204,.7)",
            )
        )
        fig_pos.update_layout(barmode='group', title="Position Distribution Comparison")
        fig_pos.update_layout(**f1_plotly_layout(title="Position Distribution Comparison"))
        st.plotly_chart(fig_pos, width='stretch')
    
    with h2h_scenarios:
        st.subheader("What-If Scenarios")
        
        scenario_col1, scenario_col2 = st.columns(2)
        
        with scenario_col1:
            st.markdown("**Best Case for " + d1_name + "**")
            best_case_p1 = min(range(len(dist1)), key=lambda i: dist1[i] if i < len(dist1) else float('inf')) + 1 if dist1 else 1
            st.info(f"Most likely best finish: P{best_case_p1}")
        
        with scenario_col2:
            st.markdown("**Best Case for " + d2_name + "**")
            best_case_p2 = min(range(len(dist2)), key=lambda i: dist2[i] if i < len(dist2) else float('inf')) + 1 if dist2 else 1
            st.info(f"Most likely best finish: P{best_case_p2}")
        
        st.divider()
        st.markdown(
            f"**Key Insights:**\n"
            f"- {'Teammate battle' if are_teammates else 'Inter-team rivalry'} at {_safe_get_circuit_meta(circuit_id)['name']}\n"
            f"- Qualifying importance: {'⭐⭐⭐ High' if qualifying_weight > 50 else '⭐⭐ Medium'}\n"
            f"- Rain: {'Enabled 🌧️' if rain_prob else 'Disabled ☀️'}\n"
            f"- Confidence: {n_simulations:,} Monte Carlo runs"
        )


def render_constructor_mode(circuit_ids: list[str], sims: int):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>🏗️ Constructor Strategy Hub</div></div>",
        unsafe_allow_html=True,
    )
    
    st.info(
        "👥 **Team Performance Analyzer**: Predict constructor standings by aggregating both drivers' results."
    )
    
    circuit_id = st.selectbox(
        "🏁 Circuit",
        options=circuit_ids,
        index=0 if circuit_ids else None,
        format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
        key="constructor_circuit",
    )
    
    strategy = st.radio(
        "Team Strategy Approach",
        options=["Balanced", "Aggressive", "Conservative"],
        index=0,
        horizontal=True,
        key="constructor_strategy",
    )
    
    n_simulations = st.number_input("# Simulations", min_value=1000, max_value=50000, value=int(sims), step=1000, key="constructor_sims")
    
    run = st.button("🏗️ Run Constructor Prediction", type="primary", width='stretch', key="constructor_run")
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    
    if not run:
        st.info("Select a circuit and strategy to predict constructor performance.")
        return
    
    with st.spinner("Simulating race and aggregating constructor results…"):
        try:
            sim_result = predict_race(
                circuit_id=circuit_id,
                rain_probability=None,
                n_simulations=int(n_simulations),
            )
        except Exception as e:
            st.error(f"Constructor prediction failed: {e}")
            return
    
    agg: dict[str, dict] = {}
    for p in sim_result.get("predictions", []):
        team = p.get("team")
        if not team:
            continue
        
        if team not in agg:
            agg[team] = {
                "constructor": team,
                "win_probability": 0.0,
                "top3_probability": 0.0,
                "points_expected": 0.0,
            }
        
        agg[team]["win_probability"] += p.get("win_probability", p.get("win_pct", 0))
        agg[team]["top3_probability"] += p.get("top3_probability", p.get("top3_pct", 0))
        
        pos = p.get("predicted_position", 20)
        points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
        agg[team]["points_expected"] += points_map.get(pos, 0) * (p.get("win_probability", 0) or (p.get("win_pct", 0) / 100))
    
    rows = sorted(list(agg.values()), key=lambda x: x["win_probability"], reverse=True)
    top = rows[:10]
    
    x = [r["constructor"].replace("_", " ").title() for r in top]
    y = [(r["win_probability"] * 100 if r["win_probability"] <= 1.5 else r["win_probability"]) for r in top]
    
    pseudo = [{"team": r["constructor"]} for r in top]
    colors = bar_colors_from_teams(pseudo)
    
    st.plotly_chart(
        make_bar_chart({"x": x, "y": y, "color": colors}, "Constructor Win Probability", x_label="Constructor", y_label="Win %"),
        width='stretch',
    )
    
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)


def render_championship_mode(circuit_ids: list[str], sims: int, rain_probability: float):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>🏆 Championship Season Simulator</div></div>",
        unsafe_allow_html=True,
    )
    
    st.info("📅 **Season Projection Engine**: Simulate remaining races to predict championship outcomes.")
    
    remaining = st.slider("Remaining Races", min_value=1, max_value=24, value=10, step=1, key="champ_remaining")
    n_simulations = st.number_input("# Season Simulations", min_value=500, max_value=50000, value=int(sims), step=1000, key="champ_sims")
    
    with st.expander("🎭 What-If Scenarios"):
        injury_scenario = st.checkbox("Key driver misses races", key="champ_injury")
        reliability_issue = st.checkbox("Top team reliability problems", key="champ_reliability")
        weather_factor = st.checkbox("Wet season bias", key="champ_weather")
    
    run = st.button("📈 Simulate Championship Season", type="primary", width='stretch', key="champ_run")
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    
    if not run:
        st.info("Configure remaining races and scenarios to simulate the championship.")
        return
    
    with st.spinner("Running season simulation…"):
        try:
            from src.data.calendar_2026 import get_upcoming_races
            
            remaining_races = get_upcoming_races()[: int(remaining)]
            points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
            
            driver_champ_wins = {}
            constructor_champ_wins = {}
            
            for sim_idx in range(int(n_simulations)):
                driver_points = {}
                constructor_points = {}
                
                for race_idx, race in enumerate(remaining_races):
                    circuit_id = race.get("id")
                    if not circuit_id:
                        continue
                    
                    mod_rain = rain_probability
                    if weather_factor and race_idx % 3 == 0:
                        mod_rain = 0.6
                    
                    sim_result = predict_race(circuit_id=circuit_id, rain_probability=mod_rain, n_simulations=500)
                    
                    for dp in sim_result.get("predictions", []):
                        driver_id = dp.get("driver_id")
                        team = dp.get("team")
                        pos = dp.get("predicted_position", 20)
                        pts = points_map.get(pos, 0)
                        
                        if driver_id:
                            driver_points[driver_id] = driver_points.get(driver_id, 0) + pts
                        if team:
                            constructor_points[team] = constructor_points.get(team, 0) + pts
                
                if driver_points:
                    winner_driver = max(driver_points, key=driver_points.get)
                    driver_champ_wins[winner_driver] = driver_champ_wins.get(winner_driver, 0) + 1
                
                if constructor_points:
                    winner_constructor = max(constructor_points, key=constructor_points.get)
                    constructor_champ_wins[winner_constructor] = constructor_champ_wins.get(winner_constructor, 0) + 1
            
            driver_top = dict(sorted({k: v / int(n_simulations) * 100 for k, v in driver_champ_wins.items()}.items(), key=lambda x: x[1], reverse=True)[:10])
            constructor_top = dict(sorted({k: v / int(n_simulations) * 100 for k, v in constructor_champ_wins.items()}.items(), key=lambda x: x[1], reverse=True)[:10])
            
        except Exception as e:
            st.error(f"Championship simulation failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            return
    
    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--gold-podium); box-shadow: 0 0 0 6px rgba(255,214,0,.12);'></span>Projected Championship Outcomes</div></div>",
        unsafe_allow_html=True,
    )
    
    summary_col1, summary_col2 = st.columns(2)
    with summary_col1:
        st.metric("Simulated Seasons", f"{n_simulations:,}")
    with summary_col2:
        st.metric("Remaining Races", remaining)
    
    champ_drivers, champ_constructors = st.tabs(["👤 Driver Championship", "🏗️ Constructor Championship"])
    
    with champ_drivers:
        st.subheader("Driver Champion Probabilities")
        st.dataframe(pd.DataFrame([{"Driver": k.replace("_", " ").title(), "Probability": f"{v:.1f}%"} for k, v in driver_top.items()]), hide_index=True, width='stretch')
    
    with champ_constructors:
        st.subheader("Constructor Champion Probabilities")
        st.dataframe(pd.DataFrame([{"Constructor": k.replace("_", " ").title(), "Probability": f"{v:.1f}%"} for k, v in constructor_top.items()]), hide_index=True, width='stretch')


def render_accuracy_mode():
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>📊 Prediction Analytics Dashboard</div></div>",
        unsafe_allow_html=True,
    )
    
    # Display current accuracy metrics from accuracy_service
    try:
        accuracy_service = get_accuracy_service()
        metrics_30d = accuracy_service.get_accuracy_metrics(days=30)
        metrics_90d = accuracy_service.get_accuracy_metrics(days=90)
        
        # Show summary cards
        st.markdown("### 🎯 Current Performance (Last 30 Days)")
        
        if metrics_30d.get("total_evaluations", 0) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                top3_acc = metrics_30d.get("top3_accuracy", {}).get("average_pct")
                if top3_acc:
                    st.metric(
                        "Top-3 Accuracy",
                        f"{top3_acc:.1f}%",
                        delta="✅ Target Met" if top3_acc >= 80 else f"⚠️ {80 - top3_acc:.1f}% to target"
                    )
                else:
                    st.metric("Top-3 Accuracy", "N/A")
            
            with col2:
                winner_acc = metrics_30d.get("winner_prediction", {}).get("accuracy_pct")
                if winner_acc:
                    st.metric("Winner Prediction", f"{winner_acc:.1f}%")
                else:
                    st.metric("Winner Prediction", "N/A")
            
            with col3:
                pos_error = metrics_30d.get("position_error", {}).get("mean_absolute_error")
                if pos_error:
                    st.metric("Avg Position Error", f"{pos_error:.2f} positions")
                else:
                    st.metric("Avg Position Error", "N/A")
            
            with col4:
                total_evals = metrics_30d.get("total_evaluations", 0)
                st.metric("Evaluations", total_evals)
            
            # Show trend
            trend = metrics_30d.get("trend", {})
            if trend.get("direction") == "improving":
                st.success(f"📈 Accuracy Trend: Improving (+{trend.get('change_pct', 0):.1f}%)")
            elif trend.get("direction") == "declining":
                st.warning(f"📉 Accuracy Trend: Declining ({trend.get('change_pct', 0):.1f}%)")
            else:
                st.info("➡️ Accuracy Trend: Stable")
        
        else:
            st.info("🔍 No evaluated predictions yet. Run predictions and record actual results to track accuracy.")
            
            # Show how to evaluate
            with st.expander("ℹ️ How to Track Accuracy", expanded=True):
                st.markdown("""
                **To start tracking prediction accuracy:**
                
                1. **Run a race prediction** in Race mode
                2. **After the actual race**, come back here
                3. **Enter actual results** to compare against predictions
                4. **View metrics** to see how accurate the model is
                
                **Target Metrics:**
                - Top-3 Accuracy: ≥80% ✅
                - Winner Prediction: ≥75%
                - Mean Position Error: <2.0 positions
                """)
    
    except Exception as e:
        st.error(f"Failed to load accuracy metrics: {e}")
        logger.error(f"Accuracy dashboard error: {e}")
    
    st.markdown("---")
    
    # Legacy accuracy report section
    st.markdown("### 🔬 Detailed Model Analysis")
    
    run = st.button("🧪 Generate Full Accuracy Report", type="primary", width='stretch', key="acc_run")
    
    if not run:
        st.info("Track Brier scores, calibration, trends, and driver-specific predictability. Click above to generate detailed report.")
        return
    
    with st.spinner("Analyzing prediction accuracy…"):
        try:
            tracker = PredictionTracker()
            report = tracker.get_accuracy_report()
            tracker.close()
        except Exception as e:
            st.error(f"Failed to load accuracy report: {e}")
            return
    
    if not report or report.get("total_predictions", 0) == 0:
        st.warning("No accuracy data found yet. Run some predictions first!")
        return
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Predictions", report.get("total_predictions", 0))
    with cols[1]:
        evaluated = report.get("evaluated_predictions", 0)
        total = report.get("total_predictions", 1)
        st.metric("Evaluated", f"{evaluated}/{total}")
    with cols[2]:
        brier = report.get("avg_brier_score", 0)
        st.metric("Avg Brier Score", f"{brier:.4f}" if isinstance(brier, (int, float)) else "N/A")
    with cols[3]:
        accuracy = report.get("position_accuracy", 0)
        st.metric("Position Accuracy", f"{accuracy:.1f}%" if isinstance(accuracy, (int, float)) else "N/A")
    
    st.subheader("💡 Model Optimization Recommendations")
    recommendations = report.get("recommendations", [])
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            st.markdown(f"{idx}. {rec}")
    else:
        st.markdown("1. ✅ Model performing well\n2. 🎯 Continue collecting data\n3. 🌧️ Enhance wet weather models")


def render_download_mode(circuit_ids: list[str]):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>📄 Report Studio</div></div>",
        unsafe_allow_html=True,
    )
    
    st.info("📊 **Professional Report Generator**: Create customizable HTML reports with charts and predictions.")
    
    circuit_id = st.selectbox(
        "🏁 Circuit",
        options=circuit_ids,
        index=0 if circuit_ids else None,
        format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
        key="download_circuit",
    )
    
    rain_choice = st.toggle("🌧️ Include Rain Scenario", value=False, key="dl_rain")
    rain_probability = 0.1 if rain_choice else None
    sims = st.number_input("# Simulations", min_value=1000, max_value=50000, value=10000, step=1000, key="dl_sims")
    
    run = st.button("📄 Generate Professional Report", type="primary", width='stretch', key="dl_run")
    
    if not run:
        st.info("Generate standalone HTML reports with predictions, charts, and strategic insights.")
        return
    
    with st.spinner("Generating professional report…"):
        try:
            report_path = generate_report(circuit_id, rain_probability=rain_probability, n_simulations=int(sims))
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            return
    
    st.success(f"✅ Report generated successfully!")
    st.markdown(f"**Saved to**: `{report_path}`")


def main():
    # ── AUTO-SYNC CALENDAR ON STARTUP (NEW) ──
    try:
        from src.data.calendar_2026 import sync_calendar_from_fastf1
        
        # Only sync if FastF1 is available
        try:
            import fastf1
            sync_result = sync_calendar_from_fastf1(season=2026)
            
            if sync_result.get("synced", 0) > 0 or sync_result.get("added", 0) > 0:
                st.toast(
                    f"📅 Calendar synced: {sync_result['synced']} updated, {sync_result['added']} added",
                    icon="✅"
                )
        except ImportError:
            pass  # FastF1 not installed, skip sync
    
    except Exception as e:
        # Don't fail app startup if calendar sync fails
        import logging
        logging.getLogger(__name__).warning(f"Calendar sync skipped: {e}")
    
    # ── PHASE 4: AUTO-LEARNING FOR RECENTLY COMPLETED RACES ──
    try:
        from src.engine.auto_learning import schedule_auto_learning_for_completed_races
        
        # Check for races completed in last 7 days and update model
        learning_result = schedule_auto_learning_for_completed_races(season=2026)
        
        if learning_result.get("processed_count", 0) > 0:
            st.toast(
                f"🤖 Auto-learning: Updated model with {learning_result['processed_count']} recent race(s)",
                icon="🎯"
            )
            logger.info(
                f"Auto-learning processed {learning_result['processed_count']} races: "
                f"{[p['name'] for p in learning_result.get('processed', [])]}"
            )
    
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Auto-learning scheduler skipped: {e}")
    
    render_hero()

    mode, circuit_ids, driver_options, sims, rain_probability = render_mode_sidebar()

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    default_circuit = circuit_ids[0] if circuit_ids else None

    if mode == "Race":
        render_race_mode(circuit_ids=circuit_ids, default_circuit=default_circuit, rain_probability=rain_probability, sims=sims)
    elif mode == "H2H":
        render_h2h_mode(driver_options=driver_options, circuit_ids=circuit_ids, sims=sims, rain_probability=rain_probability)
    elif mode == "Constructor":
        render_constructor_mode(circuit_ids=circuit_ids, sims=sims)
    elif mode == "Championship":
        render_championship_mode(circuit_ids=circuit_ids, sims=sims, rain_probability=rain_probability)
    elif mode == "Accuracy":
        render_accuracy_mode()
    elif mode == "Download":
        render_download_mode(circuit_ids=circuit_ids)


main()
