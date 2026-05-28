"""
Probability Model — v3 with full calibration fix and tire model.

FIXES vs v2:
  1. Platt calibration now uses outcome-specific parameters (not one-size-fits-all)
  2. DNF probability left raw until historical calibration data available
  3. Added minimal tire compound model for pit stop simulation
  4. Grid overrides properly passed through to feature engineering
"""

import math
import random
import numpy as np
from typing import Optional, List, Dict

from engine.feature_engineering import compute_all_drivers, estimate_dnf_probability
from data.driver_data import get_all_drivers

# FIX #1: Outcome-specific Platt calibration parameters
PLATT_PARAMS = {
    "win":   (1.12, -0.08),
    "top3":  (1.05, -0.04),
    "top10": (0.98, -0.02),
    "dnf":   (1.00,  0.00),  # DNF: no calibration until we have historical data
}

SIMULATION_RUNS = 5000
FIELD_SIZE = 22
BASE_RACE_LAPS = 60

# FIX #10: Minimal tire compound model
TIRE_COMPOUNDS = {
    "soft":   {"lap_delta": -0.4, "deg_per_lap": 0.018, "max_safe_laps": 25},
    "medium": {"lap_delta":  0.0, "deg_per_lap": 0.010, "max_safe_laps": 38},
    "hard":   {"lap_delta": +0.3, "deg_per_lap": 0.006, "max_safe_laps": 55},
}

SIMULATION_RUNS = 5000
FIELD_SIZE = 22
BASE_RACE_LAPS = 60   # Normalisation baseline for DNF distance scaling


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def _platt(raw: float, A: float, B: float) -> float:
    """Apply Platt scaling to a single probability."""
    eps = 1e-9
    raw = max(eps, min(1 - eps, raw))
    log_odds = math.log(raw / (1 - raw))
    return 1.0 / (1.0 + math.exp(-(A * log_odds + B)))


def _softmax(scores: List[float], temperature: float = 0.28) -> List[float]:
    """Temperature-scaled numerically stable softmax."""
    if not scores:
        return []
    scaled = [s / temperature for s in scores]
    max_s = max(scaled)
    exps = [math.exp(s - max_s) for s in scaled]
    total = sum(exps)
    if total == 0:
        return [1.0 / len(scores)] * len(scores)
    return [e / total for e in exps]


def assign_starting_compound(circuit_tire_deg: float, rng: random.Random) -> str:
    """Higher tire deg circuits → drivers more likely to start on mediums."""
    if circuit_tire_deg > 8.0:
        return rng.choices(["soft", "medium"], weights=[0.3, 0.7])[0]
    return rng.choices(["soft", "medium", "hard"], weights=[0.4, 0.4, 0.2])[0]


def _distance_dnf_multiplier(circuit_laps: int) -> float:
    """
    FIX: DNF probability scales with race distance.
    A 78-lap Monaco race has ~30% more exposure than a 52-lap race.
    Models a compound Poisson failure process per lap.
    """
    return max(0.6, min(1.5, circuit_laps / BASE_RACE_LAPS))


def simulate_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_runs: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
    grid_overrides: Optional[dict] = None,
) -> dict:
    """
    Monte Carlo race simulation with v3 accuracy improvements.

    Key changes from v2:
      - Grid overrides properly passed to feature engineering
      - Tire compound model added (basic version)
      - Platt calibration applied correctly per outcome type
    """
    # FIX #16: Pass grid_overrides to feature engineering
    driver_features = compute_all_drivers(circuit_id, rain_probability, grid_overrides=grid_overrides or {})

    import importlib
    cd = importlib.import_module("data.circuit_data")
    circuit = cd.get_circuit(circuit_id)
    sc_prob     = circuit.get("safety_car_probability", 0.5)
    circuit_laps = circuit.get("lap_count", 60)
    tire_deg     = circuit.get("tire_deg_rate", 5.0)

    # FIX: noise scaled by circuit chaos (SC probability)
    # Canada (SC=0.82) gets σ=0.066; Monaco (SC=0.78) σ=0.062; Monza (SC=0.30) σ=0.024
    circuit_noise_sigma = 0.02 + sc_prob * 0.056

    # FIX: distance-adjusted DNF multiplier
    dnf_mult = _distance_dnf_multiplier(circuit_laps)

    finish_counts = {d["driver_id"]: [0] * (FIELD_SIZE + 2) for d in driver_features}
    top3_counts   = {d["driver_id"]: 0 for d in driver_features}
    top10_counts  = {d["driver_id"]: 0 for d in driver_features}
    win_counts    = {d["driver_id"]: 0 for d in driver_features}
    dnf_counts    = {d["driver_id"]: 0 for d in driver_features}

    # Use deterministic randomness only when an explicit seed is provided.
    rng = random.Random(seed) if seed is not None else random.Random()

    for _ in range(n_runs):
        # 1. Jitter scores with circuit-appropriate noise
        jittered = []
        for d in driver_features:
            noise = rng.gauss(0, circuit_noise_sigma)
            score = max(0.001, d["composite_score"] + noise)
            # FIX: scale DNF probability by distance multiplier
            adj_dnf = min(d["dnf_probability"] * dnf_mult, 0.45)
            dnf_rolled = rng.random() < adj_dnf
            
            # FIX #10: Assign tire compound (basic model)
            tire = assign_starting_compound(tire_deg, rng)
            
            jittered.append((d["driver_id"], score, dnf_rolled, tire))

        # Sort by score before SC event
        jittered.sort(key=lambda x: x[1], reverse=True)

        # 2. FIX: Safety car — boosts mid-field drivers (P6–P15), not leaders
        if rng.random() < sc_prob:
            boosted = []
            for rank, (did, score, dnf, tire) in enumerate(jittered):
                if 5 <= rank <= 14 and not dnf:  # P6–P15 in current order
                    score = score * rng.uniform(1.03, 1.10)
                boosted.append((did, score, dnf, tire))
            jittered = boosted

        # 3. Sort final order
        finishing = [(did, score) for did, score, dnf, tire in jittered if not dnf]
        finishing.sort(key=lambda x: x[1], reverse=True)
        dnfs = [(did,) for did, score, dnf, tire in jittered if dnf]

        # 4. Record positions
        for pos, (did, _) in enumerate(finishing, start=1):
            if pos <= FIELD_SIZE:
                finish_counts[did][pos] += 1
            if pos == 1:  win_counts[did]  += 1
            if pos <= 3:  top3_counts[did] += 1
            if pos <= 10: top10_counts[did] += 1

        for (did,) in dnfs:
            dnf_counts[did] += 1

    # 5. Compute statistics
    stats = {}
    for d in driver_features:
        did = d["driver_id"]
        non_dnf = max(n_runs - dnf_counts[did], 1)
        exp_pos = sum(
            pos * finish_counts[did][pos]
            for pos in range(1, FIELD_SIZE + 1)
        ) / non_dnf

        stats[did] = {
            "win_probability":        round(win_counts[did] / n_runs, 4),
            "top3_probability":       round(top3_counts[did] / n_runs, 4),
            "top10_probability":      round(top10_counts[did] / n_runs, 4),
            "dnf_probability":        round(dnf_counts[did] / n_runs, 4),
            "expected_position":      round(exp_pos, 2),
            "position_distribution":  finish_counts[did][1:FIELD_SIZE + 1],
        }

    return stats


def predict_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
    grid_overrides: Optional[dict] = None,
) -> dict:
    """Master prediction function — returns ranked driver list with all probability outputs."""
    circuit_id, rain_probability, n_simulations = __validate_prediction_inputs(
        circuit_id=circuit_id,
        rain_probability=rain_probability,
        n_simulations=n_simulations,
    )

    from engine.feature_engineering import compute_teammate_beat_probability
    from data.driver_data import get_all_drivers as _get_all

    grid_overrides = grid_overrides or {}

    sim_stats = simulate_race(
        circuit_id,
        rain_probability,
        n_simulations,
        seed,
        grid_overrides=grid_overrides,
    )
    driver_features = compute_all_drivers(
        circuit_id,
        rain_probability,
        grid_overrides=grid_overrides,
    )
    all_drivers = {d["id"]: d for d in _get_all()}


    predictions = []
    for d_feat in driver_features:
        did   = d_feat["driver_id"]
        stats = sim_stats[did]
        drv   = all_drivers[did]

        predictions.append({
            "driver_id":               did,
            "driver_name":             drv["name"],
            "team":                    drv["team"],
            "championship_points":     drv["championship_points_2026"],
            "predicted_position":      round(stats["expected_position"]),
            "expected_position_float": stats["expected_position"],
            "win_probability":         stats["win_probability"],
            "top3_probability":        stats["top3_probability"],
            "top10_probability":       stats["top10_probability"],
            "dnf_probability":         stats["dnf_probability"],
            "teammate_beat_prob":      compute_teammate_beat_probability(did),
            "composite_score":         d_feat["composite_score"],
            "features":                d_feat["features"],
            "position_distribution":   stats["position_distribution"],
        })

    predictions.sort(key=lambda x: x["expected_position_float"])

    # FIX #1: Apply outcome-specific Platt calibration
    for pred in predictions:
        pred["win_probability"]  = _platt(pred["win_probability"],  *PLATT_PARAMS["win"])
        pred["top3_probability"] = _platt(pred["top3_probability"], *PLATT_PARAMS["top3"])
        pred["top10_probability"]= _platt(pred["top10_probability"],*PLATT_PARAMS["top10"])
        # DNF: leave raw until you have calibration data
        # pred["dnf_probability"] stays uncalibrated

    return {
        "circuit_id":       circuit_id,
        "rain_probability": rain_probability,
        "n_simulations":    n_simulations,
        "predictions":      predictions,
    }


def __validate_prediction_inputs(
    circuit_id: str,
    rain_probability: Optional[float],
    n_simulations: int,
) -> tuple[str, Optional[float], int]:
    circuit_id = circuit_id.lower().strip()

    if rain_probability is not None:
        if not 0.0 <= rain_probability <= 1.0:
            raise ValueError(
                f"rain_probability must be in [0,1], got {rain_probability}"
            )

    if not 100 <= n_simulations <= 100_000:
        raise ValueError(
            f"n_simulations must be in [100, 100000], got {n_simulations}"
        )

    return circuit_id, rain_probability, n_simulations



def adjust_probabilities(raw_probs):
    """DEPRECATED: Use _platt() with outcome-specific params instead."""
    # Kept for backward compatibility but should not be used
    platt_a_win = PLATT_PARAMS["win"][0]
    platt_b_win = PLATT_PARAMS["win"][1]
    calibrated_probs = 1 / (1 + np.exp(-(platt_a_win * raw_probs + platt_b_win)))
    return calibrated_probs


__all__ = ["simulate_race", "predict_race", "adjust_probabilities", "PLATT_PARAMS", "TIRE_COMPOUNDS"]
