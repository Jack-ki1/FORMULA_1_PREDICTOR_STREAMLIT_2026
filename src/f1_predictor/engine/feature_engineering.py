"""Feature Engineering Pipeline — v2 improvements.

This file had merge-conflict markers that made the project fail to import.
The implementation below is a clean, conflict-free version compatible with
`f1_predictor.engine.probability_model`.
"""

from __future__ import annotations

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

from f1_predictor.config.settings import FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW
from f1_predictor.data.circuit_data import circuit_favors_team, get_circuit
from f1_predictor.data.driver_data import (
    calculate_circuit_performance_modifier,
    get_all_drivers,
    get_driver,
    get_drivers_for_team,
)
from f1_predictor.data.season_2026 import DRIVER_STANDINGS_AFTER_R5, get_driver_last_n_results
from f1_predictor.data.teams import normalize_team


N_DRIVERS = 22


# ── ELO ────────────────────────────────────────────────────────────────────────

def elo_confidence_weight(experience_races: int) -> float:
    """Confidence-weight ELO toward 0.5 for inexperienced drivers."""
    return min(1.0, max(0.0, experience_races / 30.0))


def compute_elo_score(driver_id: str) -> float:
    """Compute a normalized ELO score in [0,1]."""
    try:
        try:
            from f1_predictor.engine.multi_dimensional_elo import get_elo_system

            elo_system = get_elo_system()
            raw_elo = elo_system.drivers.get(driver_id, {}).get("race", {}).get("rating", 1500.0)
            all_race_ratings = [
                d.get("race", {}).get("rating", 1500.0) for d in elo_system.drivers.values()
            ]
            lo, hi = min(all_race_ratings), max(all_race_ratings)
            normalized_elo = (raw_elo - lo) / (hi - lo + 1e-9)
        except Exception:
            field = get_all_drivers()
            lo, hi = min(d["elo"] for d in field), max(d["elo"] for d in field)
            raw_elo = get_driver(driver_id)["elo"]
            normalized_elo = (raw_elo - lo) / (hi - lo + 1e-9)

        driver = get_driver(driver_id)
        experience = driver.get("experience_races", 0)
        confidence = elo_confidence_weight(experience)
        return 0.5 * (1 - confidence) + normalized_elo * confidence
    except Exception:
        return 0.5


# ── Constructor strength ───────────────────────────────────────────────────────

_CONSTRUCTOR_STRENGTH: dict[str, float] = {
    "mercedes": 0.96,
    "red_bull": 0.85,
    "mclaren": 0.82,
    "ferrari": 0.78,
    "williams": 0.45,
    "alpine": 0.42,
    "haas": 0.38,
    "rb": 0.35,
    "audi": 0.22,
    "aston_martin": 0.15,
    "cadillac": 0.10,
}


def compute_constructor_strength(team_id: str, circuit_id: str) -> float:
    try:
        try:
            canonical = normalize_team(team_id)
        except Exception:
            canonical = team_id

        base = _CONSTRUCTOR_STRENGTH.get(canonical, _CONSTRUCTOR_STRENGTH.get(team_id, 0.25))
        try:
            mult = circuit_favors_team(circuit_id, canonical)
        except Exception:
            mult = 1.0
        return min(1.0, max(0.05, base * mult))
    except Exception:
        return 0.25


# ── Recent form ───────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str) -> float:
    """Exponentially-weighted average of last N finishing positions."""
    try:
        results = get_driver_last_n_results(driver_id, n=RECENCY_WINDOW)
        if not results:
            return 0.5

        def pos_to_score(pos: int | str | None) -> float:
            if pos is None or pos == "DNF" or not isinstance(pos, int) or pos <= 0:
                return 0.02
            return max(0.05, 1.0 - (pos - 1) / (N_DRIVERS - 1))

        weighted_sum = 0.0
        weight_total = 0.0
        for i, res in enumerate(results):
            w = RECENCY_DECAY ** i
            weighted_sum += w * pos_to_score(res)
            weight_total += w

        return weighted_sum / weight_total if weight_total else 0.5
    except Exception:
        return 0.5


# ── Track type fit ─────────────────────────────────────────────────────────────

def compute_track_fit_score(driver_id: str, circuit_id: str) -> float:
    try:
        driver = get_driver(driver_id)
        circuit = get_circuit(circuit_id)
        track_types = circuit.get("circuit_type", ["balanced"])
        fits = driver.get("track_type_fit", {})
        total_fit = sum(float(fits.get(t, 1.0)) for t in track_types)
        avg_fit = total_fit / max(1, len(track_types))
        return min(1.0, max(0.0, (avg_fit - 0.8) / 0.4))
    except Exception:
        return 0.5


# ── Reliability ───────────────────────────────────────────────────────────────

def compute_reliability_score(driver_id: str) -> float:
    try:
        driver = get_driver(driver_id)
        career_dnf = float(driver.get("dnf_rate_career", 0.15))
        recent_dnf = float(driver.get("dnf_rate_recent", 0.15))
        blended_dnf = 0.4 * career_dnf + 0.6 * recent_dnf
        return max(0.0, min(1.0, 1.0 - blended_dnf))
    except Exception:
        return 0.5


# ── Weather adjustment ─────────────────────────────────────────────────────────

def compute_weather_score(
    driver_id: str, circuit_id: str, rain_probability: Optional[float] = None
) -> float:
    try:
        driver = get_driver(driver_id)
        wet_skill = float(driver.get("wet_skill", 5.0)) / 10.0
        rain_prob = float(rain_probability) if rain_probability is not None else 0.2
        base_score = 0.5
        wet_bonus = (wet_skill - 0.5) * rain_prob * 0.6
        return max(0.0, min(1.0, base_score + wet_bonus))
    except Exception:
        return 0.5


# ── Safety car upside ──────────────────────────────────────────────────────────

def compute_safety_car_upside(
    driver_id: str, circuit_id: str, estimated_grid_pos: Optional[int] = None
) -> float:
    try:
        circuit = get_circuit(circuit_id)
        sc_prob = float(circuit.get("safety_car_probability", 0.5))

        if estimated_grid_pos is None:
            driver = get_driver(driver_id)
            points = float(driver.get("championship_points_2026", 50))
            estimated_grid_pos = max(1, min(20, round(1 + 19 * (1 - min(points, 150) / 150))))

        grid_factor = (estimated_grid_pos - 1) / (N_DRIVERS - 1)
        upside = sc_prob * grid_factor * 0.8
        return max(0.0, min(0.8, upside))
    except Exception:
        return 0.25


# ── Grid position score ───────────────────────────────────────────────────────

def compute_grid_position_score(driver_id: str, actual_grid_pos: Optional[int] = None) -> float:
    """Map grid position to [0.05..1.0]. If actual is missing, use proxy from points."""
    try:
        if actual_grid_pos is not None:
            return max(0.05, 1.0 - (actual_grid_pos - 1) / (N_DRIVERS - 1))

        driver = get_driver(driver_id)
        points = float(driver.get("championship_points_2026", 50))
        estimated_pos = max(1, min(20, round(1 + 19 * (1 - min(points, 150) / 150))))
        return max(0.05, 1.0 - (estimated_pos - 1) / (N_DRIVERS - 1))
    except Exception:
        return 0.5


# ── Teammate beat probability ──────────────────────────────────────────────────

def compute_teammate_beat_probability(driver_id: str) -> float:
    try:
        driver = get_driver(driver_id)
        team = driver.get("team", "")
        teammates = get_drivers_for_team(team)
        if len(teammates) < 2:
            return 0.5

        other = [t for t in teammates if t.get("id") != driver_id][0]
        elo_diff = float(driver.get("elo", 1500)) - float(other.get("elo", 1500))
        prob = 1.0 / (1.0 + math.exp(-elo_diff / 100))
        return max(0.05, min(0.95, prob))
    except Exception:
        return 0.5


# ── DNF probability estimation ─────────────────────────────────────────────────

def estimate_dnf_probability(driver_id: str, circuit_id: Optional[str] = None) -> float:
    try:
        driver = get_driver(driver_id)
        career_dnf = float(driver.get("dnf_rate_career", 0.15))
        recent_dnf = float(driver.get("dnf_rate_recent", 0.15))
        base_dnf = 0.4 * career_dnf + 0.6 * recent_dnf

        if circuit_id:
            circuit = get_circuit(circuit_id)
            wall_crash_prob = float(circuit.get("wall_crash_probability_per_lap", 0.002))
            lap_count = int(circuit.get("lap_count", 60))
            circuit_risk = wall_crash_prob * lap_count * 3
            base_dnf = 0.7 * base_dnf + 0.3 * min(0.3, circuit_risk)

        return max(0.05, min(0.45, base_dnf))
    except Exception:
        return 0.15


# ── Composite score ────────────────────────────────────────────────────────────

def compute_composite_score(
    driver_id: str,
    circuit_id: str,
    rain_probability: Optional[float] = None,
    actual_grid_pos: Optional[int] = None,
) -> dict:
    driver = get_driver(driver_id)

    features = {
        "elo_rating": compute_elo_score(driver_id),
        "constructor_strength": compute_constructor_strength(driver["team"], circuit_id),
        "recent_form": compute_recent_form_score(driver_id),
        "track_type_fit": compute_track_fit_score(driver_id, circuit_id),
        "reliability": compute_reliability_score(driver_id),
        "weather_adjustment": compute_weather_score(driver_id, circuit_id, rain_probability),
        "safety_car_upside": compute_safety_car_upside(driver_id, circuit_id),
        "grid_position": compute_grid_position_score(driver_id, actual_grid_pos),
    }

    non_finite = [k for k, v in features.items() if not math.isfinite(float(v))]
    if non_finite:
        raise ValueError(f"Non-finite features for {driver_id}: {non_finite}")

    composite = sum(float(FEATURE_WEIGHTS.get(k, 0.0)) * float(v) for k, v in features.items())

    circuit_modifier = calculate_circuit_performance_modifier(driver_id, circuit_id)
    composite *= circuit_modifier

    return {
        "driver_id": driver_id,
        "features": features,
        "composite_score": round(composite, 6),
        "dnf_probability": round(estimate_dnf_probability(driver_id, circuit_id), 4),
        "teammate_beat_probability": round(compute_teammate_beat_probability(driver_id), 4),
        "circuit_history_modifier": round(circuit_modifier, 4),
    }


def compute_all_drivers(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    grid_overrides: Optional[dict] = None,
) -> list:
    grid_overrides = grid_overrides or {}
    results = [
        compute_composite_score(
            d["id"],
            circuit_id,
            rain_probability,
            actual_grid_pos=grid_overrides.get(d["id"]),
        )
        for d in get_all_drivers()
    ]
    return sorted(results, key=lambda x: x["composite_score"], reverse=True)

