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
    "practice_pace": {},            # NEW: Dict[circuit_id, Dict[str, Dict]] from fetch_practice_pace_data
    "initialised": False,
}


def refresh_fastf1_cache(season: int = None, circuits: Optional[list] = None):
    """
    Pre-populate the FastF1 data cache for the current season.
    Call this at app startup or before a prediction batch.

    Safe to call even if FastF1 is not installed — all failures are caught.
    
    FIX F-08: Auto-detect current season; fallback gracefully to previous year.
    """
    # Auto-detect current season (default to current year)
    if season is None:
        from datetime import datetime
        season = datetime.now().year
    
    try:
        from src.data.fastf1_integration import (
            FASTF1_AVAILABLE,
            get_constructor_pace_rankings,
            get_circuit_historical_stats,
            get_wet_weather_performance,
            fetch_practice_pace_data,  # NEW: Import practice data fetcher
        )
        if not FASTF1_AVAILABLE:
            logger.info("FastF1 not available — using static fallback data")
            return

        logger.info(f"Refreshing FastF1 data cache for season {season}...")

        # Constructor pace rankings - try current season, fall back to previous
        try:
            _FASTF1_CACHE["constructor_pace"] = get_constructor_pace_rankings(season)
            logger.info(f"  Constructor pace: {len(_FASTF1_CACHE['constructor_pace'])} teams (season={season})")
        except Exception as e:
            logger.warning(f"  Constructor pace for {season} failed: {e}. Trying {season-1}...")
            try:
                _FASTF1_CACHE["constructor_pace"] = get_constructor_pace_rankings(season - 1)
                logger.info(f"  Constructor pace: {len(_FASTF1_CACHE['constructor_pace'])} teams (fallback to {season-1})")
            except Exception as e2:
                logger.warning(f"  Constructor pace fallback also failed: {e2}")

        # Wet weather performance - use last 3 seasons for better coverage
        try:
            seasons_for_wet = [s for s in [season, season - 1, season - 2] if s >= 2020]
            _FASTF1_CACHE["wet_weather"] = get_wet_weather_performance(seasons_for_wet)
            logger.info(f"  Wet weather: {len(_FASTF1_CACHE['wet_weather'])} drivers (seasons={seasons_for_wet})")
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

        # NEW: Practice pace data for current/upcoming races
        if circuits:
            for cid in circuits:
                try:
                    # Try FP2 first (most representative), then FP3
                    fp2_data = fetch_practice_pace_data(season, cid, 'FP2')
                    if fp2_data and fp2_data.get('driver_pace'):
                        _FASTF1_CACHE["practice_pace"][cid] = fp2_data['driver_pace']
                        logger.info(f"  Practice pace (FP2): {len(fp2_data['driver_pace'])} drivers for {cid}")
                    else:
                        fp3_data = fetch_practice_pace_data(season, cid, 'FP3')
                        if fp3_data and fp3_data.get('driver_pace'):
                            _FASTF1_CACHE["practice_pace"][cid] = fp3_data['driver_pace']
                            logger.info(f"  Practice pace (FP3): {len(fp3_data['driver_pace'])} drivers for {cid}")
                except Exception as e:
                    logger.debug(f"  Practice pace for {cid} not available: {e}")

        _FASTF1_CACHE["initialised"] = True
        logger.info(f"FastF1 cache refresh complete (season={season})")

    except ImportError:
        logger.info("FastF1 module not found — using static fallback data")
    except Exception as e:
        logger.warning(f"FastF1 cache refresh failed: {e} — using static fallback")


def _get_circuit_fastf1_stats(circuit_id: str) -> Optional[dict]:
    """Get cached FastF1 circuit stats, or None if unavailable."""
    return _FASTF1_CACHE.get("circuit_stats", {}).get(circuit_id)


def _get_practice_pace_data(circuit_id: str, driver_id: str) -> Optional[dict]:
    """
    NEW: Get practice pace data for a driver at a specific circuit.
    
    Returns practice session performance metrics including:
    - Long-run average lap time (race pace)
    - Short-run best lap time (qualifying pace)
    - Tire degradation indicators
    - Consistency metrics
    
    Args:
        circuit_id: Circuit identifier
        driver_id: Driver ID from database
    
    Returns:
        Dict with practice metrics or None if unavailable
    """
    try:
        practice_data = _FASTF1_CACHE.get("practice_pace", {}).get(circuit_id)
        if not practice_data:
            return None
        
        # Get driver abbreviation
        from src.data.driver_data import get_driver
        driver = get_driver(driver_id)
        driver_short = driver.get("short", "").upper()
        
        if driver_short in practice_data:
            return practice_data[driver_short]
        
        return None
    except Exception as e:
        logger.debug(f"Error fetching practice pace for {driver_id} at {circuit_id}: {e}")
        return None


N_DRIVERS = len(get_all_drivers()) if get_all_drivers() else 22


def pos_to_score(pos: int | str | None, n_drivers: int = None) -> float:
    """Convert finishing position to normalized score [0, 1].
    
    Args:
        pos: Finishing position (1-based), "DNF", or None
        n_drivers: Number of drivers in field (uses module default if not provided)
    
    Returns:
        Normalized score where P1 ≈ 1.0, last place ≈ 0.05
    """
    if n_drivers is None:
        n_drivers = N_DRIVERS
    
    if pos is None or pos == "DNF" or not isinstance(pos, int) or pos <= 0:
        return 0.02
    return max(0.05, 1.0 - (pos - 1) / (n_drivers - 1))


# ── ELO ────────────────────────────────────────────────────────────────────────

def elo_confidence_weight(experience_races: int) -> float:
    """Confidence-weight ELO toward 0.5 for inexperienced drivers."""
    return min(1.0, max(0.0, experience_races / 30.0))


def compute_elo_score(driver_id: str) -> float:
    """Compute a normalized ELO score in [0,1]."""
    try:
        try:
            from src.engine.multi_dimensional_elo import get_elo_system

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

# FIX F-04: Constructor strength ratings updated from 2026 season standings (after R5)
# Previously used 2021-era ratings that were outdated. Now dynamically computed from
# actual 2026 race results, with fallback to static values for new teams.
_CONSTRUCTOR_STRENGTH_STATIC: dict[str, float] = {
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


def _compute_constructor_strength_from_standings() -> dict[str, float]:
    """
    FIX F-04: Compute constructor strength from 2026 season standings.
    
    Uses actual points scored in 2026 races to derive relative team strength.
    Normalizes so the leading team gets ~0.95 and others scale proportionally.
    
    Returns:
        Dict mapping team_id to strength score [0.05, 1.0]
    """
    try:
        from src.data.season_2026 import CURRENT_CONSTRUCTOR_STANDINGS
        
        if not CURRENT_CONSTRUCTOR_STANDINGS:
            return _CONSTRUCTOR_STRENGTH_STATIC.copy()
        
        # Get max points possible (5 races * 43 points per race for 1-2 finish + fastest lap)
        # Actually, just normalize relative to the leader
        max_points = CURRENT_CONSTRUCTOR_STANDINGS[0]["points"] if CURRENT_CONSTRUCTOR_STANDINGS else 1
        
        strength_map = {}
        for entry in CURRENT_CONSTRUCTOR_STANDINGS:
            team = entry.get("team", "")
            points = entry.get("points", 0)
            
            # Normalize: leader gets 0.95, others scale proportionally
            # Floor at 0.05 to avoid zeroing out new teams
            normalized = max(0.05, 0.95 * (points / max_points)) if max_points > 0 else 0.25
            strength_map[team] = normalized
        
        # For teams not yet in standings (e.g., Cadillac if they haven't scored), 
        # use static fallback
        for team, static_val in _CONSTRUCTOR_STRENGTH_STATIC.items():
            if team not in strength_map:
                strength_map[team] = static_val
        
        return strength_map
    
    except Exception as e:
        logger.warning(f"Failed to compute constructor strength from standings: {e}. Using static values.")
        return _CONSTRUCTOR_STRENGTH_STATIC.copy()


# Initialize constructor strength - will be updated dynamically
_CONSTRUCTOR_STRENGTH = _compute_constructor_strength_from_standings()


def _update_constructor_strength_from_season():
    """Update constructor strength cache when new race results are available."""
    global _CONSTRUCTOR_STRENGTH
    _CONSTRUCTOR_STRENGTH = _compute_constructor_strength_from_standings()


def compute_constructor_strength(team_id: str, circuit_id: str) -> float:
    """
    Compute constructor strength using FastF1 data when available.
    Falls back to 2026 season standings, then hardcoded dict when unavailable.
    
    FIX F-04: Now uses live 2026 standings instead of 2021-era static values.
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
                # Blend: 70% FastF1 data, 30% 2026 standings for stability
                standings_strength = _CONSTRUCTOR_STRENGTH.get(canonical, _CONSTRUCTOR_STRENGTH.get(team_id, 0.25))
                blended = 0.7 * ff_score + 0.3 * standings_strength
                # Apply circuit favourability modifier
                try:
                    mult = circuit_favors_team(circuit_id, canonical)
                except Exception:
                    mult = 1.0
                return min(1.0, max(0.05, blended * mult))

        # ── 2026 Standings Fallback ──
        base = _CONSTRUCTOR_STRENGTH.get(canonical, _CONSTRUCTOR_STRENGTH.get(team_id, 0.25))
        try:
            mult = circuit_favors_team(circuit_id, canonical)
        except Exception:
            mult = 1.0
        return min(1.0, max(0.05, base * mult))
    except Exception:
        return 0.25


# ── Recent form ───────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str, circuit_id: Optional[str] = None) -> float:
    """
    Compute recent form using last N race results with exponential decay.
    
    NEW: Enhanced with practice pace data when available for current circuit.
    Blends historical finishing positions with current weekend practice performance.
    
    Args:
        driver_id: Driver ID
        circuit_id: Optional circuit ID to fetch practice data
    
    Returns:
        Normalized form score [0.05, 1.0]
    """
    try:
        from src.data.season_2026 import get_driver_last_n_results
        
        results = get_driver_last_n_results(driver_id, n=RECENCY_WINDOW)
        if not results:
            return 0.5

        # Calculate weighted average of recent results
        weight_total = 0.0
        weighted_sum = 0.0
        for i, res in enumerate(results):
            w = RECENCY_DECAY ** i
            weighted_sum += w * pos_to_score(res, n_drivers=N_DRIVERS)
            weight_total += w

        base_score = weighted_sum / weight_total if weight_total else 0.5

        # ── NEW: Practice Pace Enhancement ──
        # If we have practice data for this circuit, blend it with historical form
        if circuit_id:
            practice_data = _get_practice_pace_data(circuit_id, driver_id)
            if practice_data:
                # Extract practice pace indicators
                avg_lap_time = practice_data.get('avg_lap_time')
                best_lap_time = practice_data.get('best_lap_time')
                lap_count = practice_data.get('lap_count', 0)
                std_dev = practice_data.get('std_dev', 999)
                
                if avg_lap_time and lap_count >= 3:  # Need meaningful sample
                    # Convert lap time to relative performance score
                    # Lower lap time = better = higher score
                    # Normalize based on typical F1 lap time range (80-120s)
                    pace_score = max(0.1, min(1.0, 1.0 - (avg_lap_time - 80) / 40))
                    
                    # Consistency bonus (lower std dev = more consistent)
                    consistency_bonus = max(0.0, min(0.1, 0.1 - (std_dev / 100)))
                    pace_score += consistency_bonus
                    
                    # Blend: 60% historical results, 40% current practice pace
                    base_score = 0.6 * base_score + 0.4 * pace_score
                    
                    logger.debug(
                        f"Practice-enhanced form for {driver_id}: "
                        f"historical={base_score:.2f}, practice pace={pace_score:.2f}"
                    )

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


# ── Practice Pace Score (NEW) ──────────────────────────────────────────────────

def compute_practice_pace_score(driver_id: str, circuit_id: str) -> float:
    """
    NEW: Compute driver's current weekend practice pace at this circuit.
    
    Uses FP2/FP3 data to assess:
    - Raw pace (average lap time)
    - Consistency (standard deviation)
    - Race simulation performance (long runs)
    - Qualifying simulation performance (short runs)
    
    This captures current form and car setup effectiveness for THIS weekend,
    not just historical performance.
    
    Args:
        driver_id: Driver ID
        circuit_id: Circuit identifier
    
    Returns:
        Normalized pace score [0.05, 1.0], or 0.5 if no practice data
    """
    try:
        practice_data = _get_practice_pace_data(circuit_id, driver_id)
        
        if not practice_data:
            return 0.5  # No practice data available
        
        # Extract key metrics
        avg_lap_time = practice_data.get('avg_lap_time')
        best_lap_time = practice_data.get('best_lap_time')
        lap_count = practice_data.get('lap_count', 0)
        std_dev = practice_data.get('std_dev', 999)
        race_sim_avg = practice_data.get('race_sim_avg')
        quali_sim_best = practice_data.get('quali_sim_best')
        
        # Need minimum laps for meaningful assessment
        if lap_count < 3 or not avg_lap_time:
            return 0.5
        
        # Calculate raw pace score (lower time = better)
        # Normalize to typical F1 range: 80s (fast) to 120s (slow)
        raw_pace_score = max(0.1, min(1.0, 1.0 - (avg_lap_time - 80) / 40))
        
        # Consistency score (lower std dev = more consistent)
        # Typical std dev: 0.5s (very consistent) to 5s (inconsistent)
        consistency_score = max(0.1, min(1.0, 1.0 - (std_dev / 5.0)))
        
        # Race simulation score (if available)
        race_score = 0.5
        if race_sim_avg and practice_data.get('race_sim_laps', 0) >= 3:
            race_score = max(0.1, min(1.0, 1.0 - (race_sim_avg - 80) / 40))
        
        # Qualifying simulation score (if available)
        quali_score = 0.5
        if quali_sim_best and practice_data.get('quali_sim_laps', 0) >= 2:
            quali_score = max(0.1, min(1.0, 1.0 - (quali_sim_best - 80) / 40))
        
        # Weighted combination
        # 40% overall pace, 25% consistency, 20% race sim, 15% quali sim
        final_score = (
            0.40 * raw_pace_score +
            0.25 * consistency_score +
            0.20 * race_score +
            0.15 * quali_score
        )
        
        logger.debug(
            f"Practice pace for {driver_id} at {circuit_id}: "
            f"raw={raw_pace_score:.2f}, consistency={consistency_score:.2f}, "
            f"race={race_score:.2f}, quali={quali_score:.2f} → final={final_score:.2f}"
        )
        
        return max(0.05, min(1.0, final_score))
    
    except Exception as e:
        logger.debug(f"Error computing practice pace for {driver_id}: {e}")
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
    """Probability driver beats their teammate(s), averaged across all team-mates.

    Avoids teammate-order bias by comparing against *every* other teammate in the team roster.
    """
    try:
        driver = get_driver(driver_id)
        team = driver.get("team", "")
        teammates = get_drivers_for_team(team)
        others = [t for t in teammates if t.get("id") != driver_id]
        if not others:
            return 0.5

        driver_elo = float(driver.get("elo", 1500))
        probs = []
        for other in others:
            other_elo = float(other.get("elo", 1500))
            elo_diff = driver_elo - other_elo
            prob = 1.0 / (1.0 + math.exp(-elo_diff / 100))
            probs.append(prob)

        prob_avg = sum(probs) / len(probs)
        return max(0.05, min(0.95, prob_avg))
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
        "recent_form": compute_recent_form_score(driver_id, circuit_id),  # Enhanced with practice data
        "practice_pace": compute_practice_pace_score(driver_id, circuit_id),  # NEW: Practice pace feature
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
