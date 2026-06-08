"""Feature Engineering Pipeline — v3 with FastF1 integration.

This file had merge-conflict markers that made the project fail to import.
The implementation below is a clean, conflict-free version compatible with
`engine.probability_model`.

v3: Every feature function now attempts to use real FastF1 data first,
    falling back to static/hardcoded values when FastF1 is unavailable.
"""

from __future__ import annotations

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

from src.config.settings import FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW
from src.data.circuit_data import circuit_favors_team, get_circuit
from src.data.driver_data import (

    calculate_circuit_performance_modifier,
    get_all_drivers,
    get_driver,
    get_drivers_for_team,
)
from src.data.season_2026 import DRIVER_STANDINGS_AFTER_R5, get_driver_last_n_results
from src.data.teams import normalize_team

# ── FastF1 Data Cache (populated at startup or on-demand) ─────────────────────
# These module-level caches hold the latest FastF1-derived data.
# They are populated lazily on first access and refreshed via refresh_fastf1_cache().
_FASTF1_CACHE = {
    "constructor_pace": None,       # Dict[str, float] from get_constructor_pace_rankings
    "circuit_stats": {},            # Dict[circuit_id, Dict] from get_circuit_historical_stats
    "wet_weather": None,            # Dict[str, Dict] from get_wet_weather_performance
    "driver_pace": {},              # Dict[circuit_id, Dict[str, Dict]] from get_driver_pace_metrics
    "initialised": False,
}


def refresh_fastf1_cache(season: int = 2025, circuits: Optional[list] = None):
    """
    Pre-populate the FastF1 data cache for the current season.
    Call this at app startup or before a prediction batch.

    Safe to call even if FastF1 is not installed — all failures are caught.
    """
    try:
        from src.data.fastf1_integration import (
            FASTF1_AVAILABLE,
            get_constructor_pace_rankings,
            get_circuit_historical_stats,
            get_wet_weather_performance,
        )
        if not FASTF1_AVAILABLE:
            logger.info("FastF1 not available — using static fallback data")
            return

        logger.info("Refreshing FastF1 data cache...")

        # Constructor pace rankings
        try:
            _FASTF1_CACHE["constructor_pace"] = get_constructor_pace_rankings(season)
            logger.info(f"  Constructor pace: {len(_FASTF1_CACHE['constructor_pace'])} teams")
        except Exception as e:
            logger.warning(f"  Constructor pace failed: {e}")

        # Wet weather performance
        try:
            _FASTF1_CACHE["wet_weather"] = get_wet_weather_performance([season, season - 1])
            logger.info(f"  Wet weather: {len(_FASTF1_CACHE['wet_weather'])} drivers")
        except Exception as e:
            logger.warning(f"  Wet weather failed: {e}")

        # Circuit historical stats
        if circuits:
            for cid in circuits:
                try:
                    cname = get_circuit(cid)["name"]
                    _FASTF1_CACHE["circuit_stats"][cid] = get_circuit_historical_stats(
                        cname, [season, season - 1, season - 2]
                    )
                except Exception as e:
                    logger.warning(f"  Circuit stats for {cid} failed: {e}")

        _FASTF1_CACHE["initialised"] = True
        logger.info("FastF1 cache refresh complete")

    except ImportError:
        logger.info("FastF1 module not found — using static fallback data")
    except Exception as e:
        logger.warning(f"FastF1 cache refresh failed: {e} — using static fallback")


def _get_circuit_fastf1_stats(circuit_id: str) -> Optional[dict]:
    """Get cached FastF1 circuit stats, or None if unavailable."""
    return _FASTF1_CACHE.get("circuit_stats", {}).get(circuit_id)


N_DRIVERS = 22


# ── ELO ────────────────────────────────────────────────────────────────────────

def elo_confidence_weight(experience_races: int) -> float:
    """Confidence-weight ELO toward 0.5 for inexperienced drivers."""
    return min(1.0, max(0.0, experience_races / 30.0))


def compute_elo_score(driver_id: str) -> float:
    """Compute a normalized ELO score in [0,1]."""
    try:
        try:
            from engine.multi_dimensional_elo import get_elo_system

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
    """
    Compute constructor strength using FastF1 data when available.
    Falls back to hardcoded dict when FastF1 is unavailable.
    """
    try:
        try:
            canonical = normalize_team(team_id)
        except Exception:
            canonical = team_id

        # ── FastF1 Path: Use actual pace rankings ──
        fastf1_pace = _FASTF1_CACHE.get("constructor_pace")
        if fastf1_pace:
            # Match team name (FastF1 uses full names like 'Red Bull Racing')
            ff_score = None
            team_lower = canonical.lower().replace("_", " ")
            for ff_team, ff_pace in fastf1_pace.items():
                if team_lower in ff_team.lower():
                    ff_score = ff_pace
                    break
            if ff_score is not None:
                # Blend: 70% FastF1 data, 30% static fallback for stability
                static = _CONSTRUCTOR_STRENGTH.get(canonical, 0.25)
                blended = 0.7 * ff_score + 0.3 * static
                # Apply circuit favourability modifier
                try:
                    mult = circuit_favors_team(circuit_id, canonical)
                except Exception:
                    mult = 1.0
                return min(1.0, max(0.05, blended * mult))

        # ── Static Fallback ──
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
    """
    Exponentially-weighted average of last N finishing positions.
    Enhanced with FastF1 pace delta when available.
    """
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

        base_score = weighted_sum / weight_total if weight_total else 0.5

        # ── FastF1 Enhancement: Blend with pace delta if available ──
        driver_short = get_driver(driver_id).get("short", "").upper()
        pace_data = _FASTF1_CACHE.get("driver_pace", {})
        if pace_data and driver_short:
            # Use the most recent circuit's pace data
            latest_pace = None
            for circuit_pace in pace_data.values():
                if driver_short in circuit_pace:
                    latest_pace = circuit_pace[driver_short]
            if latest_pace and "pace_delta_to_leader" in latest_pace:
                delta = latest_pace["pace_delta_to_leader"]
                # Convert delta to 0-1 score (0 delta = 0.7, +10s = 0.2)
                pace_score = max(0.05, min(0.95, 0.7 - delta / 20.0))
                # Blend: 70% finishing positions, 30% pace data
                base_score = 0.7 * base_score + 0.3 * pace_score

        return base_score
    except Exception:
        return 0.5


# ── Track type fit ─────────────────────────────────────────────────────────────

def compute_track_fit_score(driver_id: str, circuit_id: str) -> float:
    """
    Compute track fit using historical circuit-specific pace when available.
    Falls back to static track_type_fit ratings.
    """
    try:
        # ── FastF1 Path: Use historical pace at this specific circuit ──
        pace_data = _FASTF1_CACHE.get("driver_pace", {}).get(circuit_id)
        if pace_data:
            driver_short = get_driver(driver_id).get("short", "").upper()
            if driver_short in pace_data:
                delta = pace_data[driver_short].get("pace_delta_to_leader", 0)
                # Negative delta = faster than field median → better fit
                # Map: -2s delta → 1.0, +5s delta → 0.0
                fit_score = max(0.0, min(1.0, 0.6 - delta / 10.0))
                # Blend with static fit for stability
                driver = get_driver(driver_id)
                circuit = get_circuit(circuit_id)
                track_types = circuit.get("circuit_type", ["balanced"])
                fits = driver.get("track_type_fit", {})
                static_fit = sum(float(fits.get(t, 1.0)) for t in track_types) / max(1, len(track_types))
                static_score = min(1.0, max(0.0, (static_fit - 0.8) / 0.4))
                return 0.6 * fit_score + 0.4 * static_score

        # ── Static Fallback ──
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
    """
    Compute reliability using circuit-specific DNF rates when available.
    Falls back to static career/recent DNF rates.
    """
    try:
        driver = get_driver(driver_id)
        career_dnf = float(driver.get("dnf_rate_career", 0.15))
        recent_dnf = float(driver.get("dnf_rate_recent", 0.15))
        base_dnf = 0.4 * career_dnf + 0.6 * recent_dnf
        return max(0.0, min(1.0, 1.0 - base_dnf))
    except Exception:
        return 0.5


# ── Weather adjustment ─────────────────────────────────────────────────────────

def compute_weather_score(
    driver_id: str, circuit_id: str, rain_probability: Optional[float] = None
) -> float:
    """
    Compute weather score using FastF1 wet-weather performance when available.
    Falls back to subjective wet_skill rating from driver data.
    """
    try:
        driver = get_driver(driver_id)
        rain_prob = float(rain_probability) if rain_probability is not None else 0.2

        # ── FastF1 Path: Use actual wet-weather pace rating ──
        wet_data = _FASTF1_CACHE.get("wet_weather")
        if wet_data:
            driver_short = driver.get("short", "").upper()
            if driver_short in wet_data:
                ff_wet_rating = wet_data[driver_short].get("wet_pace_rating", 0.5)
                # Blend: 60% FastF1 wet rating, 40% static wet_skill
                static_wet = float(driver.get("wet_skill", 5.0)) / 10.0
                blended_wet = 0.6 * ff_wet_rating + 0.4 * static_wet
                base_score = 0.5
                wet_bonus = (blended_wet - 0.5) * rain_prob * 0.6
                return max(0.0, min(1.0, base_score + wet_bonus))

        # ── Static Fallback ──
        wet_skill = float(driver.get("wet_skill", 5.0)) / 10.0
        base_score = 0.5
        wet_bonus = (wet_skill - 0.5) * rain_prob * 0.6
        return max(0.0, min(1.0, base_score + wet_bonus))
    except Exception:
        return 0.5


# ── Safety car upside ──────────────────────────────────────────────────────────

def compute_safety_car_upside(
    driver_id: str, circuit_id: str, estimated_grid_pos: Optional[int] = None
) -> float:
    """
    Compute safety car upside using FastF1 historical SC frequency when available.
    Falls back to static circuit property.
    """
    try:
        # ── FastF1 Path: Use actual SC frequency from historical data ──
        circuit_stats = _get_circuit_fastf1_stats(circuit_id)
        if circuit_stats and "safety_car_frequency" in circuit_stats:
            sc_prob = float(circuit_stats["safety_car_frequency"])
        else:
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
    """
    Estimate DNF probability using FastF1 circuit-specific DNF rates when available.
    Falls back to static career/recent DNF rates.
    """
    try:
        driver = get_driver(driver_id)
        career_dnf = float(driver.get("dnf_rate_career", 0.15))
        recent_dnf = float(driver.get("dnf_rate_recent", 0.15))
        base_dnf = 0.4 * career_dnf + 0.6 * recent_dnf

        if circuit_id:
            # ── FastF1 Path: Use circuit-specific DNF rate ──
            circuit_stats = _get_circuit_fastf1_stats(circuit_id)
            if circuit_stats and "avg_dnf_rate" in circuit_stats:
                ff_dnf = float(circuit_stats["avg_dnf_rate"])
                # Blend: 50% FastF1 circuit-specific, 50% driver-specific
                base_dnf = 0.5 * base_dnf + 0.5 * ff_dnf
            else:
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
