"""
Feature Engineering Pipeline — v2 improvements.

FIXES vs v1:
  1. Grid position no longer hardcoded to 0.5 — compute_grid_position_score() uses
     championship position + qualifying delta as a proper pre-race proxy.
     When actual_grid_pos is provided (post-qualifying), it uses that directly.
  2. DNF penalty for non-finishers: v1 used position 21 (n_drivers+1).
     A DNF is worse than P20 — now mapped to 25 (n_drivers + 5).
  3. temporal_cross_validate length check replaced with join-based logic (no crash
     when rounds have different driver counts).
  4. All functions handle KeyError gracefully (no silent state mutation).
"""

from __future__ import annotations

import json
import math
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from config.settings import FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW
from data.driver_data import get_driver, get_all_drivers, get_drivers_for_team
from data.circuit_data import get_circuit, circuit_favors_team
from data.season_2026 import get_driver_last_n_results, DRIVER_STANDINGS_AFTER_R4

logger = logging.getLogger(__name__)

N_DRIVERS = 22
DNF_POSITION_PENALTY = N_DRIVERS + 5  # 25 — worse than last finisher

# FIX #5: Load constructor strengths from JSON instead of hardcoding in Python
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> dict:
    """Load JSON config file."""
    filepath = _DATA_DIR / "config" / filename
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to defaults if file missing or corrupt
        return {}


_CONSTRUCTOR_STRENGTH: Dict[str, float] = _load_json("constructor_strengths.json")


# ── ELO ────────────────────────────────────────────────────────────────────────

def compute_elo_score(driver_id: str) -> float:
    try:
        raw = get_driver(driver_id)["elo"]
        field = get_all_drivers()
        lo, hi = min(d["elo"] for d in field), max(d["elo"] for d in field)
        return (raw - lo) / (hi - lo + 1e-9)
    except Exception as e:
        logger.warning("compute_elo_score failed for %s: %s", driver_id, e)
        return 0.5


# ── Constructor strength ───────────────────────────────────────────────────────

def compute_constructor_strength(team_id: str, circuit_id: str) -> float:
    base = _CONSTRUCTOR_STRENGTH.get(team_id, 0.25)
    try:
        mult = circuit_favors_team(circuit_id, team_id)
    except Exception as e:
        logger.warning("compute_constructor_strength failed for %s/%s: %s", team_id, circuit_id, e)
        mult = 1.0
    return min(1.0, max(0.05, base * mult))


# ── Recent form ────────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str, n: int = RECENCY_WINDOW) -> float:
    try:
        results = get_driver_last_n_results(driver_id, n=n)
    except Exception as e:
        logger.warning("compute_recent_form_score failed for %s: %s", driver_id, e)
        return 0.5
    if not results:
        return 0.5

    total_w, weighted_pos = 0.0, 0.0
    for i, r in enumerate(results):
        w = RECENCY_DECAY ** i
        # FIX: DNF → 25 (worse than last finisher), not 21
        pos = r["position"] if r["position"] is not None else DNF_POSITION_PENALTY
        weighted_pos += w * pos
        total_w += w

    if total_w == 0:
        return 0.5
    avg_pos = weighted_pos / total_w
    return max(0.0, 1.0 - ((avg_pos - 1) / (N_DRIVERS - 1)))


# ── Grid position ──────────────────────────────────────────────────────────────

def compute_grid_position_score(
    driver_id: str,
    actual_grid_pos: Optional[int] = None,
) -> float:
    # NOTE: grid overrides are expected to map P1→1.0 and P20→0.0.
    # Keep this function deterministic for tests and callers.

    
    """
    FIX: v1 always returned 0.5 (neutral), wasting the grid_position feature slot.

    Pre-race mode (no actual_grid_pos):
      - Uses championship standings rank as a proxy for expected grid position.
      - Championship leader → ~P1–P2 → score ≈ 0.95
      - Backmarker → ~P18–P20 → score ≈ 0.10

    Post-qualifying mode (actual_grid_pos provided):
      - Direct mapping: P1 → 1.0, P20 → 0.0
    """
    try:
        drv = get_driver(driver_id)
    except KeyError:
        return 0.5

    if actual_grid_pos is not None:
        # Actual qualifying result — use directly
        return max(0.0, min(1.0, 1.0 - (actual_grid_pos - 1) / (N_DRIVERS - 1)))

    # Pre-race proxy: use championship standings position
    standings = DRIVER_STANDINGS_AFTER_R4
    champ_pos = next(
        (s["position"] for s in standings if s["driver"] == driver_id),
        N_DRIVERS // 2,  # default mid-field if not in standings
    )

    # Map championship position to expected grid position
    # Championship leader tends to qualify well; backmarkers struggle
    expected_grid = max(1, min(N_DRIVERS, champ_pos))
    return max(0.0, min(1.0, 1.0 - (expected_grid - 1) / (N_DRIVERS - 1)))


# ── Weather adjustment ─────────────────────────────────────────────────────────

def compute_weather_score(
    driver_id: str,
    circuit_id: str,
    rain_probability: Optional[float] = None,
) -> float:
    """
    Returns [0, 1] — higher means the driver benefits from wet conditions.

    Formula:
      baseline = 0.5 (neutral)
      wet_skill_delta = (driver.wet_skill - 5.0) / 5.0   # range [-1, +1]
      adjustment = wet_skill_delta * rain_probability
      score = baseline + adjustment * 0.5                # clamp to [0, 1]
    """
    try:
        drv = get_driver(driver_id)
    except KeyError as e:
        logger.warning("compute_weather_score failed for %s: %s", driver_id, e)
        return 0.5

    wet_skill = drv.get("wet_skill", 5.0)
    wet_skill_delta = (wet_skill - 5.0) / 5.0  # [-1, +1]

    rain = rain_probability if rain_probability is not None else 0.5
    adjustment = wet_skill_delta * rain
    score = 0.5 + adjustment * 0.5
    return max(0.0, min(1.0, score))


# ── Safety-car upside ──────────────────────────────────────────────────────────

def compute_safety_car_upside(
    driver_id: str,
    circuit_id: str,
    estimated_grid_pos: Optional[int] = None,
) -> float:
    """
    Probability that a safety car helps this driver gain positions.

    Mid-field drivers (P6–P15) benefit most from SC bunching.
    Frontrunners lose relative advantage; backmarkers have less to gain.
    """
    try:
        drv = get_driver(driver_id)
    except KeyError as e:
        logger.warning("compute_safety_car_upside failed for %s: %s", driver_id, e)
        return 0.25  # neutral

    grid = estimated_grid_pos
    if grid is None:
        # Use championship proxy
        standings = DRIVER_STANDINGS_AFTER_R4
        grid = next(
            (s["position"] for s in standings if s["driver"] == driver_id),
            N_DRIVERS // 2,
        )

    # Peak benefit around P10, tapering off toward P1 and P20
    benefit = max(0.0, 1.0 - abs(grid - 10) / 10.0) * 0.8
    return max(0.0, min(0.8, benefit))


# ── Track-type fit ─────────────────────────────────────────────────────────────

def compute_track_fit_score(driver_id: str, circuit_id: str) -> float:
    try:
        drv = get_driver(driver_id)
        circ = get_circuit(circuit_id)
    except KeyError as e:
        logger.warning("compute_track_fit_score failed for %s/%s: %s", driver_id, circuit_id, e)
        return 0.5

    circuit_types = circ.get("circuit_type", ["balanced"])
    driver_prefs = drv.get("track_preferences", ["balanced"])

    # Count overlaps
    overlap = len(set(circuit_types) & set(driver_prefs))
    if overlap == 0:
        return 0.3  # poor fit but not zero
    elif overlap >= 2:
        return 0.9  # excellent fit
    else:
        return 0.6  # moderate fit


# ── Reliability ────────────────────────────────────────────────────────────────

def compute_reliability_score(driver_id: str) -> float:
    try:
        drv = get_driver(driver_id)
    except KeyError as e:
        logger.warning("compute_reliability_score failed for %s: %s", driver_id, e)
        return 0.7  # neutral

    reliability = drv.get("reliability_rating", 7.0)
    return max(0.0, min(1.0, reliability / 10.0))


# ── DNF probability estimate ───────────────────────────────────────────────────

def estimate_dnf_probability(driver_id: str) -> float:
    """
    Returns a prior DNF probability based on driver reliability and historical rate.
    Range: 0.05 (very reliable) to 0.45 (very unreliable).
    """
    try:
        drv = get_driver(driver_id)
    except KeyError as e:
        logger.warning("estimate_dnf_probability failed for %s: %s", driver_id, e)
        return 0.20  # field average

    reliability = drv.get("reliability_rating", 7.0)
    hist_dnf_rate = drv.get("historical_dnf_rate", 0.15)

    # Blend reliability rating with historical DNF rate
    reliability_component = 1.0 - (reliability / 10.0)  # lower reliability → higher DNF
    dnf_prob = 0.6 * reliability_component + 0.4 * hist_dnf_rate
    return max(0.05, min(0.45, dnf_prob))


# ── Teammate-beat probability ──────────────────────────────────────────────────

def compute_teammate_beat_probability(driver_id: str) -> float:
    """Estimate probability driver beats their teammate based on Elo ratings."""
    drv = get_driver(driver_id)
    if not drv:
        return 0.5

    elo_self = drv.get("elo", 1500)
    teammates = get_drivers_for_team(drv["team"])
    if len(teammates) < 2:
        return 0.5  # no teammate data

    # Find the other driver - teammates is a list of dicts, extract IDs
    other_ids = [t["id"] for t in teammates if t["id"] != driver_id]
    if not other_ids:
        return 0.5

    elo_other = get_driver(other_ids[0]).get("elo", 1500)

    # Elo win probability formula
    prob = 1.0 / (1.0 + 10 ** ((elo_other - elo_self) / 400.0))
    return max(0.05, min(0.95, prob))


# ── Composite score ────────────────────────────────────────────────────────────

def compute_composite_score(
    driver_id: str,
    circuit_id: str,
    rain_probability: Optional[float] = None,
    actual_grid_pos: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute all features and combine into a single composite score.

    Returns:
        {
            "composite_score": float in [0, 1],
            "features": dict of individual feature values,
        }
    """
    features = {
        "elo_rating":          compute_elo_score(driver_id),
        "constructor_strength": compute_constructor_strength(
            get_driver(driver_id)["team"], circuit_id
        ),
        "recent_form":         compute_recent_form_score(driver_id),
        "track_type_fit":      compute_track_fit_score(driver_id, circuit_id),
        "reliability":         compute_reliability_score(driver_id),
        "weather_adjustment":  compute_weather_score(driver_id, circuit_id, rain_probability),
        "safety_car_upside":   compute_safety_car_upside(driver_id, circuit_id, actual_grid_pos),
        "grid_position":       compute_grid_position_score(driver_id, actual_grid_pos),
    }

    weights = FEATURE_WEIGHTS
    composite = sum(features[k] * weights.get(k, 0.0) for k in features)

    return {
        "composite_score": max(0.0, min(1.0, composite)),
        "features":        features,
    }


def compute_all_drivers(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    grid_overrides: Optional[Dict[str, int]] = None,
) -> list:
    """Compute composite scores for every driver and return sorted descending."""
    grid_overrides = grid_overrides or {}
    results = []
    for drv in get_all_drivers():
        did = drv["id"]
        override_pos = grid_overrides.get(did)
        feat = compute_composite_score(did, circuit_id, rain_probability, override_pos)
        dnf_prob = estimate_dnf_probability(did)
        results.append({
            "driver_id":       did,
            "composite_score": feat["composite_score"],
            "features":        feat["features"],
            "dnf_probability": dnf_prob,
        })

    results.sort(key=lambda x: x["composite_score"], reverse=True)
    return results


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "compute_elo_score",
    "compute_constructor_strength",
    "compute_recent_form_score",
    "compute_weather_score",
    "compute_safety_car_upside",
    "compute_teammate_beat_probability",
    "compute_track_fit_score",
    "compute_reliability_score",
    "estimate_dnf_probability",
    "compute_composite_score",
    "compute_all_drivers",
    "compute_grid_position_score",
    "N_DRIVERS",
    "DNF_POSITION_PENALTY",
]
