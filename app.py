import streamlit as st
import plotly.graph_objects as go
import pandas as pd

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
) -> dict:
    return run_predict(
        PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            seed=seed,
            grid_overrides=dict(grid_items),
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

    sims = st.sidebar.slider("# Simulations", min_value=1000, max_value=50000, value=10000, step=500)
    rain_pct = st.sidebar.slider("Rain probability (%)", min_value=0, max_value=100, value=10, step=1)

    return mode, circuit_ids, driver_options, clamp_int(sims, 1000, 50000), (rain_pct / 100.0)


def render_race_mode(circuit_ids: list[str], default_circuit: str | None, rain_probability: float, sims: int):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>Garage Inputs</div></div>",
        unsafe_allow_html=True,
    )

    circuit_id = st.selectbox(
        "Circuit",
        options=circuit_ids,
        index=circuit_ids.index(default_circuit) if default_circuit in circuit_ids else 0,
        format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
    )

    rain_choice = st.toggle("Use rain probability", value=True)
    rain_probability = rain_probability if rain_choice else None

    n_simulations = st.number_input("Monte Carlo simulations", min_value=100, max_value=50000, value=int(sims), step=500)

    seed = st.number_input("Seed", min_value=0, max_value=999999999, value=0, step=1)
    use_seed = st.checkbox("Use fixed seed", value=False)

    driver_records = load_driver_options()
    driver_lookup = {d["id"]: d for d in driver_records}

    grid_driver_ids = st.multiselect(
        "Known qualifying grid, P1 to P20",
        options=[d["id"] for d in driver_records],
        format_func=lambda driver_id: _driver_label(driver_lookup.get(driver_id, {"id": driver_id})),
        help="Optional. Add the known grid order after qualifying to improve race-day accuracy.",
    )
    grid_overrides = _parse_grid_overrides(grid_driver_ids)

    run = st.button("Run Race Prediction", type="primary", use_container_width=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--teal-primary); box-shadow: 0 0 0 6px rgba(0,229,204,.12);'></span>Pit Wall Results</div></div>",
        unsafe_allow_html=True,
    )

    if not run:
        st.info("Configure the inputs and run the race prediction.")
        return

    with st.spinner("Running the Monte Carlo engine with strategy and uncertainty outputs..."):
        try:
            result = cached_prediction(
                circuit_id=circuit_id,
                rain_probability=rain_probability,
                n_simulations=int(n_simulations),
                seed=int(seed) if use_seed else None,
                grid_items=tuple(sorted(grid_overrides.items())),
            )
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            return

    meta = result.get("meta", {})
    preds_sorted = sorted(
        result.get("predictions", []),
        key=lambda x: (x.get("expected_position") or x.get("predicted_position", 999), -x.get("win_pct", 0)),
    )
    for p_i, p in enumerate(preds_sorted, start=1):
        p["display_position"] = p_i

    podium = result.get("podium_predictions", [])
    favorite = podium[0] if podium else "-"

    win_sum = sum(float(p.get("win_pct", 0)) for p in preds_sorted)
    hierarchy_issues = sum(
        1
        for p in preds_sorted
        if float(p.get("win_pct", 0)) > float(p.get("top3_pct", 0))
        or float(p.get("top3_pct", 0)) > float(p.get("top10_pct", 0))
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Likely Winner", str(favorite))
    c2.metric("Model Confidence", f"{meta.get('overall_model_confidence', 0) * 100:.0f}%")
    c3.metric("Safety Car Risk", f"{meta.get('safety_car_probability', 0) * 100:.0f}%")
    c4.metric("Win Sum Audit", f"{win_sum:.1f}%", delta=f"{hierarchy_issues} hierarchy issues")

    if grid_overrides:
        st.caption(f"Grid override applied to {len(grid_overrides)} drivers. Forecast is more race-day specific.")

    overview_tab, uncertainty_tab, value_tab, table_tab = st.tabs(["Overview", "Uncertainty", "Value Board", "Full Table"])

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
            use_container_width=True,
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
            use_container_width=True,
        )

    with uncertainty_tab:
        st.plotly_chart(make_uncertainty_chart(preds_sorted), use_container_width=True)
        driver_names = [p.get("driver") for p in preds_sorted if p.get("driver")]
        selected_driver = st.selectbox("Inspect finish distribution", options=driver_names)
        fig = make_position_distribution_chart(preds_sorted, selected_driver)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with value_tab:
        st.dataframe(build_forecast_edges(preds_sorted), use_container_width=True, hide_index=True)

    with table_tab:
        st.dataframe(_build_predictions_table(preds_sorted), use_container_width=True, hide_index=True)

    likely_top_surprises = result.get("likely_top_surprises") or []
    if likely_top_surprises:
        st.info("Potential overperformers: " + ", ".join(map(str, likely_top_surprises)))


def render_h2h_mode(driver_options: list[str], circuit_ids: list[str], sims: int, rain_probability: float):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>Rivalry Tuner</div></div>",
        unsafe_allow_html=True,
    )

    d1 = st.selectbox("Driver 1", options=driver_options, index=0 if driver_options else None)
    d2 = st.selectbox(
        "Driver 2",
        options=driver_options,
        index=1 if len(driver_options) > 1 else 0 if driver_options else None,
    )

    circuit_id = st.selectbox(
        "Circuit",
        options=circuit_ids,
        index=0 if circuit_ids else None,
        format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
    )

    rain_choice = st.toggle("Rain enabled", value=True)
    rain_probability = rain_probability if rain_choice else None

    n_simulations = st.number_input("# Simulations", min_value=1000, max_value=50000, value=int(sims), step=500)

    run = st.button("⚔️ Run H2H", type="primary", use_container_width=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--red-f1); box-shadow: 0 0 0 6px rgba(232,0,45,.12);'></span>Head-to-Head Outcome</div></div>",
        unsafe_allow_html=True,
    )

    if not run:
        st.info("Pick two drivers, choose a circuit, then run the H2H simulation.")
        return

    with st.spinner("Simulating race outcomes for both drivers…"):
        try:
            sim_result = predict_race(
                circuit_id=circuit_id,
                rain_probability=rain_probability,
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

    m1, m2 = st.columns(2)
    with m1:
        st.metric(f"{d1_name} finishes ahead", f"{p_d1_ahead * 100:.1f}%")
    with m2:
        st.metric(f"{d2_name} finishes ahead", f"{(1 - p_d1_ahead) * 100:.1f}%")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[d1_name, d2_name],
            y=[p_d1_ahead * 100, (1 - p_d1_ahead) * 100],
            marker_color=["rgba(232,0,45,.95)", "rgba(0,229,204,.95)"],
            hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title="Finishes Ahead Probability",
        template=None,
        margin=dict(l=40, r=20, t=60, b=90),
    )
    fig.update_layout(**f1_plotly_layout(title="Finishes Ahead Probability"))
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"Avg position ({d1_name}): {p1.get('expected_position_float', p1.get('predicted_position', '-')):.1f}"
    )
    st.info(
        f"Avg position ({d2_name}): {p2.get('expected_position_float', p2.get('predicted_position', '-')):.1f}"
    )


def render_constructor_mode(circuit_ids: list[str], sims: int):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>Team Strategy</div></div>",
        unsafe_allow_html=True,
    )

    circuit_id = st.selectbox(
        "Circuit",
        options=circuit_ids,
        index=0 if circuit_ids else None,
        format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
    )

    n_simulations = st.number_input("# Simulations", min_value=1000, max_value=50000, value=int(sims), step=500)

    run = st.button("🏗️ Run Constructor Prediction", type="primary", use_container_width=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--purple-hyper); box-shadow: 0 0 0 6px rgba(170,0,255,.12);'></span>Constructor Standings (Sim)</div></div>",
        unsafe_allow_html=True,
    )

    if not run:
        st.info("Predicts aggregated constructor probabilities from simulated driver outcomes.")
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
    y = [
        (r["win_probability"] * 100 if r["win_probability"] <= 1.5 else r["win_probability"])
        for r in top
    ]

    # Build pseudo-predictions so we can reuse bar_colors_from_teams
    pseudo = [{"team": r["constructor"]} for r in top]
    colors = bar_colors_from_teams(pseudo)

    st.plotly_chart(
        make_bar_chart(
            {
                "x": x,
                "y": y,
                "color": colors,
            },
            "Constructor Win Probability (Top)",
            x_label="Constructor",
            y_label="Win %",
        ),
        use_container_width=True,
    )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_championship_mode(circuit_ids: list[str], sims: int, rain_probability: float):
    remaining = st.slider("Remaining races", min_value=3, max_value=24, value=10, step=1)
    n_simulations = st.number_input("# Season Simulations", min_value=500, max_value=50000, value=int(sims), step=500)

    run = st.button("📈 Simulate Championship", type="primary", use_container_width=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='bb-card'><div class='bb-section-title'><span class='dot' style='background:var(--gold-podium); box-shadow: 0 0 0 6px rgba(255,214,0,.12);'></span>Projected Standings</div></div>",
        unsafe_allow_html=True,
    )

    if not run:
        st.info("Uses Monte Carlo across remaining circuits to estimate champion probabilities.")
        return

    with st.spinner("Running season simulation…"):
        try:
            from src.data.calendar_2026 import get_upcoming_races

            remaining_races = get_upcoming_races()[: int(remaining)]

            points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

            driver_champ_wins = {}
            constructor_champ_wins = {}

            for _ in range(int(n_simulations)):
                driver_points = {}
                constructor_points = {}

                for race in remaining_races:
                    circuit_id = race.get("id")
                    if not circuit_id:
                        continue

                    sim_result = predict_race(circuit_id=circuit_id, rain_probability=None, n_simulations=500)
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

            driver_top = dict(
                sorted({k: v / int(n_simulations) * 100 for k, v in driver_champ_wins.items()}.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            constructor_top = dict(
                sorted({k: v / int(n_simulations) * 100 for k, v in constructor_champ_wins.items()}.items(), key=lambda x: x[1], reverse=True)[:10]
            )

        except Exception as e:
            st.error(f"Championship simulation failed: {e}")
            return

    st.subheader("Driver Champion Probabilities")
    st.dataframe(pd.DataFrame([{"Driver": k, "Prob %": v} for k, v in driver_top.items()]), hide_index=True, use_container_width=True)

    st.subheader("Constructor Champion Probabilities")
    st.dataframe(
        pd.DataFrame([{"Constructor": k.replace("_", " ").title(), "Prob %": v} for k, v in constructor_top.items()]),
        hide_index=True,
        use_container_width=True,
    )


def render_accuracy_mode():
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>Prediction Accuracy</div></div>",
        unsafe_allow_html=True,
    )
    run = st.button("🧪 Load Accuracy Report", type="primary", use_container_width=True)

    if not run:
        st.info("Displays stored calibration & Brier score metrics from the PredictionTracker.")
        return

    with st.spinner("Loading accuracy report…"):
        try:
            tracker = PredictionTracker()
            report = tracker.get_accuracy_report()
            tracker.close()
        except Exception as e:
            st.error(f"Failed to load accuracy report: {e}")
            return

    if not report:
        st.warning("No accuracy data found yet.")
        return

    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Predictions", report.get("total_predictions", 0))
    with cols[1]:
        st.metric("Evaluated", report.get("evaluated_predictions", 0))
    with cols[2]:
        st.metric("Avg Brier Score", report.get("avg_brier_score", "N/A"))

    st.json(report)


def render_download_mode(circuit_ids: list[str]):
    st.markdown(
        "<div class='bb-card-strong'><div class='bb-section-title'><span class='dot'></span>Report Generator</div></div>",
        unsafe_allow_html=True,
    )

    circuit_id = st.selectbox(
        "Circuit",
        options=circuit_ids,
        index=0 if circuit_ids else None,
        format_func=lambda x: _safe_get_circuit_meta(x).get("name") or x,
    )
    rain_choice = st.toggle("Rain enabled", value=False)
    rain_probability = 0.1 if rain_choice else None
    sims = st.number_input("# Simulations", min_value=1000, max_value=50000, value=10000, step=500)

    run = st.button("⬇️ Generate & Save HTML Report", type="primary", use_container_width=True)

    if not run:
        st.info("Generates a standalone HTML report to view in a browser.")
        return

    with st.spinner("Generating HTML report…"):
        try:
            report_path = generate_report(circuit_id, rain_probability=rain_probability, n_simulations=int(sims))
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            return

    st.success(f"Report saved: {report_path}")


def main():
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

