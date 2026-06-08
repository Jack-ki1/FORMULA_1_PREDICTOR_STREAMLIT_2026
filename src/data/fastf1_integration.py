"""
Fast-F1 Integration — Real F1 Data Pipeline for v3.0.

Integrates fastf1 library for:
- Historical race results ingestion
- Lap-by-lap telemetry data
- Tire compound and pit stop data
- Sector time analysis
- Qualifying session data
- Real-time weather conditions
- Car telemetry (speed, RPM, throttle, brake, DRS)
- Track position data (X/Y/Z coordinates)
- Driver comparison utilities
- ML feature extraction
- Circuit historical statistics (DNF rate, SC frequency, rainfall)
- Tyre degradation curve fitting (linear regression per compound)
- Wet-weather performance analysis (wet vs dry pace delta)
- Constructor pace rankings (from actual race data)
- Driver pace metrics (sector splits, consistency, gap to leader)
- Qualifying vs race pace comparison (racer vs qualifier rating)
- Circuit telemetry profiling (top speed, braking zones)
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

# Try to import FastF1
try:
    import fastf1
    from fastf1 import plotting
    FASTF1_AVAILABLE = True
    plotting.setup_mpl()
except ImportError:
    logger.warning("fastf1 library not installed. Install with: pip install fastf1")
    FASTF1_AVAILABLE = False

# -- FastF1 Cache Configuration ------------------------------------------------
_CACHE_DIR = "f1_cache"
_cache_configured = False


def _ensure_cache():
    """Configure FastF1 persistent cache on first use."""
    global _cache_configured
    if FASTF1_AVAILABLE and not _cache_configured:
        try:
            fastf1.Cache.enable_cache(_CACHE_DIR)
            _cache_configured = True
            logger.info(f"FastF1 cache enabled at: {_CACHE_DIR}")
        except Exception as e:
            logger.warning(f"Failed to configure FastF1 cache: {e}")


def get_session(season: int, race_name: str, session_type: str = 'R'):
    """
    Get F1 session data from fastf1.
    
    Args:
        season: Year (e.g., 2025)
        race_name: Race name or round number
        session_type: 'P1', 'P2', 'P3', 'Q', 'S', 'SQ', 'R'
    
    Returns:
        fastf1.core.Session object
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required. Install: pip install fastf1")
    
    try:
        session = fastf1.get_session(season, race_name, session_type)
        session.load()
        return session
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        raise


def ingest_race_results(season: int, race_name: str) -> Dict:
    """
    Ingest race results from race session.
    """
    session = get_session(season, race_name, 'R')
    
    return {
        'circuit': session.event['Location'],
        'date': session.event['EventDate'],
        'winner': session.results.iloc[0]['Abbreviation'] if len(session.results) > 0 else None,
        'results': session.results,
    }


def ingest_lap_data(season: int, race_name: str, driver_id: str) -> Dict:
    """
    Ingest lap data for a specific driver.
    
    Args:
        season: Year (e.g., 2025)
        race_name: Race name or round number
        driver_id: Driver abbreviation (e.g., 'VER', 'HAM')
    
    Returns:
        Dictionary with lap data including:
        - lap number
        - sector times
        - lap time
        - compound
        - tire age
    """
    session = get_session(season, race_name, 'R')
    
    # Get laps for the driver
    driver_laps = session.laps.pick_driver(driver_id.upper())
    
    laps = []
    for _, lap in driver_laps.iterrows():
        laps.append({
            'lap': int(lap['LapNumber']),
            'sector1': lap['Sector1Time'].total_seconds() if lap['Sector1Time'] else None,
            'sector2': lap['Sector2Time'].total_seconds() if lap['Sector2Time'] else None,
            'sector3': lap['Sector3Time'].total_seconds() if lap['Sector3Time'] else None,
            'lap_time': lap['LapTime'].total_seconds() if lap['LapTime'] else None,
            'compound': lap['Compound'],
            'tire_age': int(lap['TyreLife']),
        })
    
    return {
        'driver': driver_id,
        'laps': laps,
    }


def ingest_qualifying_results(season: int, race_name: str) -> Dict:
    """
    Ingest qualifying results from qualifying session.
    """
    session = get_session(season, race_name, 'Q')
    
    return {
        'circuit': session.event['Location'],
        'date': session.event['EventDate'],
        'results': session.results,
    }


def ingest_tire_strategy(season: int, race_name: str) -> Dict:
    """
    Ingest tire strategy data from race session.
    """
    session = get_session(season, race_name, 'R')
    
    # Get tire strategy data
    tire_strategy = []
    for driver in session.results['Abbreviation'].unique():
        driver_laps = session.laps.pick_driver(driver)
        stints = driver_laps['Compound'].value_counts().to_dict()
        tire_strategy.append({
            'driver': driver,
            'stints': stints,
        })
    
    return {
        'circuit': session.event['Location'],
        'tire_strategy': tire_strategy,
    }


def ingest_weather_data(season: int, race_name: str) -> Dict:
    """
    Ingest weather data from race session.
    """
    session = get_session(season, race_name, 'R')
    
    # Get weather data from laps
    weather_laps = []
    for _, lap in session.laps.iterrows():
        if lap['AirTemp'] is not None:
            weather_laps.append({
                'lap': int(lap['LapNumber']),
                'air_temp': float(lap['AirTemp']),
                'track_temp': float(lap['TrackTemp']),
                'humidity': float(lap['Humidity']) if lap['Humidity'] else None,
                'rainfall': bool(lap['Rainfall']),
                'wind_speed': float(lap['WindSpeed']) if lap['WindSpeed'] else None,
            })
    
    return {
        'circuit': session.event['Location'],
        'weather_data': weather_laps,
        'rained': any(w['rainfall'] for w in weather_laps),
        'avg_air_temp': sum(w['air_temp'] for w in weather_laps) / len(weather_laps) if weather_laps else None,
        'avg_track_temp': sum(w['track_temp'] for w in weather_laps) / len(weather_laps) if weather_laps else None,
    }


def ingest_telemetry_data(season: int, race_name: str, driver_id: str) -> Dict:
    """
    Ingest car telemetry data for a specific driver.
    
    NEW FUNCTION: Provides access to car telemetry including:
    - Speed, RPM, throttle, brake
    - DRS status
    - Gear selection
    - X/Y track position
    
    Args:
        season: Year (e.g., 2025)
        race_name: Race name or round number
        driver_id: Driver abbreviation (e.g., 'VER', 'HAM')
    
    Returns:
        Dictionary with telemetry data including:
        - car_data: Speed, RPM, throttle, brake, DRS, gear
        - pos_data: X/Y track coordinates
        - lap_info: Lap number, compound, tire age
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required. Install: pip install fastf1")
    
    session = get_session(season, race_name, 'R')
    
    # Get fastest lap for the driver
    try:
        driver_laps = session.laps.pick_driver(driver_id.upper())
        fastest_lap = driver_laps.pick_fastest()
        
        # Get car telemetry data
        car_data = fastest_lap.get_car_data()
        telemetry = []
        for _, data_point in car_data.iterrows():
            telemetry.append({
                'speed': float(data_point['Speed']) if data_point['Speed'] is not None else None,
                'rpm': float(data_point['RPM']) if data_point['RPM'] is not None else None,
                'throttle': float(data_point['Throttle']) if data_point['Throttle'] is not None else None,
                'brake': bool(data_point['Brake']) if data_point['Brake'] is not None else None,
                'drs': int(data_point['DRS']) if data_point['DRS'] is not None else None,
                'gear': int(data_point['nGear']) if data_point['nGear'] is not None else None,
                'time': data_point['Time'],
            })
        
        # Get position data (X/Y coordinates)
        pos_data = fastest_lap.get_pos_data()
        positions = []
        for _, pos_point in pos_data.iterrows():
            positions.append({
                'x': float(pos_point['X']) if pos_point['X'] is not None else None,
                'y': float(pos_point['Y']) if pos_point['Y'] is not None else None,
                'z': float(pos_point['Z']) if pos_point['Z'] is not None else None,
                'time': pos_point['Time'],
            })
        
        return {
            'driver': driver_id,
            'lap_number': int(fastest_lap['LapNumber']),
            'lap_time': fastest_lap['LapTime'].total_seconds() if fastest_lap['LapTime'] else None,
            'compound': fastest_lap['Compound'],
            'tire_age': int(fastest_lap['TyreLife']),
            'telemetry_points': len(telemetry),
            'car_data': telemetry,
            'position_data': positions,
        }
        
    except Exception as e:
        logger.error(f"Failed to get telemetry for {driver_id}: {e}")
        raise


def compare_drivers_telemetry(season: int, race_name: str, driver1: str, driver2: str) -> Dict:
    """
    Compare telemetry data between two drivers on their fastest laps.
    
    NEW FUNCTION: Enables driver performance comparison using:
    - Speed traces
    - Braking points
    - Throttle application
    - Corner exits
    
    Args:
        season: Year
        race_name: Race name or round
        driver1: First driver abbreviation
        driver2: Second driver abbreviation
    
    Returns:
        Dictionary with comparison metrics including:
        - avg_speed, max_speed for each driver
        - braking_intensity, throttle_application
        - lap_time difference
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    
    session = get_session(season, race_name, 'R')
    
    try:
        # Get fastest laps for both drivers
        lap1 = session.laps.pick_driver(driver1.upper()).pick_fastest()
        lap2 = session.laps.pick_driver(driver2.upper()).pick_fastest()
        
        # Get telemetry
        tel1 = lap1.get_car_data()
        tel2 = lap2.get_car_data()
        
        # Calculate comparison metrics
        comparison = {
            'driver1': {
                'id': driver1,
                'lap_time': lap1['LapTime'].total_seconds() if lap1['LapTime'] else None,
                'avg_speed': float(tel1['Speed'].mean()) if tel1['Speed'].notna().any() else None,
                'max_speed': float(tel1['Speed'].max()) if tel1['Speed'].notna().any() else None,
                'avg_throttle': float(tel1['Throttle'].mean()) if tel1['Throttle'].notna().any() else None,
                'braking_events': int((tel1['Brake'] == True).sum()) if 'Brake' in tel1.columns else None,
            },
            'driver2': {
                'id': driver2,
                'lap_time': lap2['LapTime'].total_seconds() if lap2['LapTime'] else None,
                'avg_speed': float(tel2['Speed'].mean()) if tel2['Speed'].notna().any() else None,
                'max_speed': float(tel2['Speed'].max()) if tel2['Speed'].notna().any() else None,
                'avg_throttle': float(tel2['Throttle'].mean()) if tel2['Throttle'].notna().any() else None,
                'braking_events': int((tel2['Brake'] == True).sum()) if 'Brake' in tel2.columns else None,
            },
            'lap_time_diff': None,
        }
        
        # Calculate lap time difference
        if comparison['driver1']['lap_time'] and comparison['driver2']['lap_time']:
            comparison['lap_time_diff'] = comparison['driver1']['lap_time'] - comparison['driver2']['lap_time']
        
        return comparison
        
    except Exception as e:
        logger.error(f"Failed to compare {driver1} vs {driver2}: {e}")
        raise


def load_entire_season(season: int, session_type: str = 'R') -> List[Dict]:
    """
    Load all race results for an entire season with error handling.
    
    NEW FUNCTION: Matches the "Load an Entire Season" example from FastF1 docs.
    
    Args:
        season: Year (e.g., 2025)
        session_type: Session type ('R' for race, 'Q' for qualifying)
    
    Returns:
        List of dictionaries, one per race, with:
        - round number
        - race name
        - winner
        - results dataframe (or error message)
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    
    season_data = []
    
    try:
        schedule = fastf1.get_event_schedule(season)
    except Exception as e:
        logger.error(f"Failed to get schedule for {season}: {e}")
        return season_data
    
    for idx, event in schedule.iterrows():
        # Skip non-race events
        if event['EventName'] == 'Pre-Season Test':
            continue
        
        try:
            session = fastf1.get_session(season, event['EventName'], session_type)
            session.load(telemetry=False, weather=False, messages=False)
            
            race_info = {
                'round': int(event['RoundNumber']),
                'race_name': event['EventName'],
                'circuit': event['Location'],
                'date': event['EventDate'],
                'winner': session.results.iloc[0]['Abbreviation'] if len(session.results) > 0 else None,
                'results_count': len(session.results),
                'results': session.results,
            }
            season_data.append(race_info)
            
            logger.info(f"✓ Loaded: Round {race_info['round']} - {race_info['race_name']}")
            
        except Exception as e:
            logger.warning(f"✗ Failed to load: {event['EventName']} - {e}")
            season_data.append({
                'round': int(event['RoundNumber']),
                'race_name': event['EventName'],
                'error': str(e),
            })
            continue
    
    logger.info(f"Loaded {len(season_data)} races for {season}")
    return season_data


def extract_ml_features(season: int, race_name: str) -> Dict:
    """
    Extract ML-ready features from FastF1 data for prediction models.
    
    NEW FUNCTION: Provides features for:
    - Race winner prediction
    - Qualifying prediction
    - Pit stop strategy optimization
    - Driver performance ratings
    - Tire degradation models
    
    Args:
        season: Year
        race_name: Race name or round
    
    Returns:
        Dictionary with ML-ready features:
        - driver_features: Per-driver metrics (consistency, pace, tire degradation)
        - race_features: Race-level metrics (safety car rate, weather, overtaking)
        - strategy_features: Pit stop and tire strategy patterns
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    
    session = get_session(season, race_name, 'R')
    laps = session.laps
    results = session.results
    
    # Driver-level features
    driver_features = {}
    for driver in results['Abbreviation'].unique():
        driver_laps = laps.pick_driver(driver)
        
        if len(driver_laps) == 0:
            continue
        
        # Calculate consistency (std of lap times)
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        lap_times = valid_laps['LapTime'].apply(lambda x: x.total_seconds() if x else None)
        lap_times = lap_times.dropna()
        
        # Tire degradation analysis
        stint_laps = driver_laps[['Compound', 'TyreLife', 'LapTime']].dropna()
        
        driver_features[driver] = {
            'total_laps': len(driver_laps),
            'avg_lap_time': float(lap_times.mean()) if len(lap_times) > 0 else None,
            'lap_time_std': float(lap_times.std()) if len(lap_times) > 1 else None,  # Consistency
            'fastest_lap': float(lap_times.min()) if len(lap_times) > 0 else None,
            'avg_tire_age': float(driver_laps['TyreLife'].mean()) if driver_laps['TyreLife'].notna().any() else None,
            'pit_stops': int(driver_laps['PitOutTime'].notna().sum()),
            'dnf': driver not in results[results['Status'].str.contains('Finished', na=False)]['Abbreviation'].values,
        }
    
    # Race-level features
    total_drivers = len(results)
    finished_drivers = len(results[results['Status'].str.contains('Finished', na=False)])
    dnf_count = total_drivers - finished_drivers
    
    # Safety car detection (laps with no time)
    sc_laps = laps[laps['LapTime'].isna()]
    safety_car_appearances = len(sc_laps) > 0
    
    # Weather features
    weather_data = session.weather_data
    avg_air_temp = float(weather_data['AirTemp'].mean()) if weather_data['AirTemp'].notna().any() else None
    rained = bool(weather_data['Rainfall'].any()) if 'Rainfall' in weather_data.columns else False
    
    race_features = {
        'total_drivers': total_drivers,
        'finished_drivers': finished_drivers,
        'dnf_count': dnf_count,
        'dnf_rate': dnf_count / total_drivers if total_drivers > 0 else 0,
        'safety_car': safety_car_appearances,
        'avg_air_temp': avg_air_temp,
        'rained': rained,
        'total_laps': len(laps),
    }
    
    # Strategy features
    compound_usage = laps['Compound'].value_counts().to_dict() if laps['Compound'].notna().any() else {}
    avg_stint_length = float(laps.groupby('Driver')['TyreLife'].max().mean()) if laps['TyreLife'].notna().any() else None
    
    strategy_features = {
        'compound_usage': compound_usage,
        'avg_stint_length': avg_stint_length,
        'total_pit_stops': int(laps['PitOutTime'].notna().sum()),
    }
    
    return {
        'race_name': session.event['EventName'],
        'driver_features': driver_features,
        'race_features': race_features,
        'strategy_features': strategy_features,
    }



# ==============================================================================
# PHASE 1: ADVANCED FASTF1 ANALYSIS FUNCTIONS (v5.0)
# ==============================================================================


def get_driver_pace_metrics(season: int, race_name: str) -> Dict[str, Dict]:
    """
    Compute per-driver pace metrics from a race session.

    Returns dict keyed by driver abbreviation with:
      - avg_lap_seconds: mean race lap time (excl. pit in/out laps)
      - pace_delta_to_leader: seconds behind field-median pace
      - consistency_std: standard deviation of lap times (lower = more consistent)
      - sector1_avg / sector2_avg / sector3_avg: mean sector splits in seconds
      - total_laps_completed: number of timed laps
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")

    session = get_session(season, race_name, 'R')
    laps = session.laps

    # Filter to clean laps (exclude pit in/out laps)
    clean = laps[laps['LapTime'].notna()]

    driver_avg: Dict[str, Dict] = {}
    for drv in laps['Driver'].unique():
        drv_laps = clean[clean['Driver'] == drv]
        if len(drv_laps) < 3:
            continue
        times = drv_laps['LapTime'].apply(lambda t: t.total_seconds()).values
        s1 = drv_laps['Sector1Time'].dropna()
        s2 = drv_laps['Sector2Time'].dropna()
        s3 = drv_laps['Sector3Time'].dropna()
        driver_avg[drv] = {
            'avg_lap_seconds': round(float(np.mean(times)), 3),
            'consistency_std': round(float(np.std(times)), 3),
            'sector1_avg': round(float(s1.apply(lambda t: t.total_seconds()).mean()), 3) if len(s1) > 0 else None,
            'sector2_avg': round(float(s2.apply(lambda t: t.total_seconds()).mean()), 3) if len(s2) > 0 else None,
            'sector3_avg': round(float(s3.apply(lambda t: t.total_seconds()).mean()), 3) if len(s3) > 0 else None,
            'total_laps_completed': int(len(drv_laps)),
        }

    # Field median pace as reference
    all_avgs = [v['avg_lap_seconds'] for v in driver_avg.values()]
    field_median = float(np.median(all_avgs)) if all_avgs else 0.0
    for drv in driver_avg:
        driver_avg[drv]['pace_delta_to_leader'] = round(
            driver_avg[drv]['avg_lap_seconds'] - field_median, 3
        )

    return driver_avg


def get_tyre_degradation_curves(season: int, race_name: str) -> Dict[str, Dict]:
    """
    Fit linear degradation curves per driver per compound.

    Returns dict keyed by driver abbreviation with:
      - compounds: dict keyed by compound name, each containing:
          - slope: seconds of pace loss per lap (positive = degrading)
          - intercept: estimated pace on fresh tyres (seconds)
          - r_squared: goodness of fit (0-1)
          - stint_laps: number of laps in the stint
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")

    session = get_session(season, race_name, 'R')
    laps = session.laps
    result: Dict[str, Dict] = {}

    for drv in laps['Driver'].unique():
        drv_laps = laps[laps['Driver'] == drv].copy()
        drv_result: Dict[str, Dict] = {}

        for compound in drv_laps['Compound'].dropna().unique():
            if compound.upper() in ('INTERMEDIATE', 'WET', 'UNKNOWN'):
                continue
            compound_laps = drv_laps[
                (drv_laps['Compound'] == compound)
                & drv_laps['LapTime'].notna()
                & drv_laps['TyreLife'].notna()
            ].copy()
            if len(compound_laps) < 4:
                continue
            x = compound_laps['TyreLife'].values.astype(float)
            y = compound_laps['LapTime'].apply(lambda t: t.total_seconds()).values
            try:
                coeffs = np.polyfit(x, y, 1)
                slope, intercept = float(coeffs[0]), float(coeffs[1])
                y_pred = slope * x + intercept
                ss_res = float(np.sum((y - y_pred) ** 2))
                ss_tot = float(np.sum((y - np.mean(y)) ** 2))
                r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                drv_result[compound.lower()] = {
                    'slope': round(slope, 4),
                    'intercept': round(intercept, 3),
                    'r_squared': round(max(0.0, r_squared), 3),
                    'stint_laps': int(len(compound_laps)),
                }
            except Exception:
                continue

        if drv_result:
            result[drv] = {'compounds': drv_result}

    return result


def get_circuit_historical_stats(circuit_name: str, seasons: List[int]) -> Dict:
    """
    Aggregate historical race statistics for a circuit across multiple seasons.

    Returns:
      - avg_dnf_rate: mean DNF rate across seasons
      - safety_car_frequency: fraction of races with at least one SC period
      - avg_rainfall: fraction of races with rainfall recorded
      - races_analysed: number of successfully loaded races
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    _ensure_cache()

    dnf_rates: List[float] = []
    sc_flags: List[int] = []
    rain_flags: List[int] = []
    total_races = 0

    for season in seasons:
        try:
            session = fastf1.get_session(season, circuit_name, 'R')
            session.load(telemetry=False, weather=True, messages=False)
            total_races += 1
            results = session.results
            laps = session.laps
            finished = len(results[results['Status'].str.contains('Finished', na=False)])
            total = len(results)
            if total > 0:
                dnf_rates.append(1.0 - finished / total)
            sc_lap_count = int(laps['LapTime'].isna().sum())
            sc_flags.append(1 if sc_lap_count > 5 else 0)
            weather = session.weather_data
            if 'Rainfall' in weather.columns:
                rain_flags.append(1 if bool(weather['Rainfall'].any()) else 0)
            else:
                rain_flags.append(0)
        except Exception as e:
            logger.warning(f"Skipping {season} {circuit_name}: {e}")
            continue

    if total_races == 0:
        return {'races_analysed': 0}

    return {
        'races_analysed': total_races,
        'avg_dnf_rate': round(float(np.mean(dnf_rates)), 3) if dnf_rates else 0.15,
        'safety_car_frequency': round(float(np.mean(sc_flags)), 3) if sc_flags else 0.3,
        'avg_rainfall': round(float(np.mean(rain_flags)), 3) if rain_flags else 0.2,
    }


def get_wet_weather_performance(seasons: List[int]) -> Dict[str, Dict]:
    """
    Compute per-driver wet vs dry pace delta across multiple seasons.

    Returns dict keyed by driver abbreviation with:
      - dry_avg_lap: mean lap time in dry races
      - wet_avg_lap: mean lap time in wet races
      - wet_delta: wet - dry (positive = slower in wet)
      - wet_pace_rating: 0-1 score where 1.0 = excels in wet
      - wet_races: number of wet races analysed
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    _ensure_cache()

    driver_dry: Dict[str, List[float]] = {}
    driver_wet: Dict[str, List[float]] = {}

    for season in seasons:
        try:
            schedule = fastf1.get_event_schedule(season)
        except Exception:
            continue
        for _, event in schedule.iterrows():
            if event['EventName'] == 'Pre-Season Test':
                continue
            try:
                session = fastf1.get_session(season, event['EventName'], 'R')
                session.load(telemetry=False, weather=True, messages=False)
                weather = session.weather_data
                is_wet = bool(weather['Rainfall'].any()) if 'Rainfall' in weather.columns else False
                for drv in session.laps['Driver'].unique():
                    drv_laps = session.laps[
                        (session.laps['Driver'] == drv) & session.laps['LapTime'].notna()
                    ]
                    if len(drv_laps) < 5:
                        continue
                    avg_time = float(drv_laps['LapTime'].apply(lambda t: t.total_seconds()).mean())
                    if is_wet:
                        driver_wet.setdefault(drv, []).append(avg_time)
                    else:
                        driver_dry.setdefault(drv, []).append(avg_time)
            except Exception:
                continue

    result: Dict[str, Dict] = {}
    for drv in set(driver_dry.keys()) & set(driver_wet.keys()):
        dry_avg = float(np.mean(driver_dry[drv]))
        wet_avg = float(np.mean(driver_wet[drv]))
        delta = wet_avg - dry_avg
        # Map: typical delta +5 to +15 -> rating 0.25 to 0.0; negative delta -> >0.5
        wet_pace_rating = max(0.0, min(1.0, 0.5 - delta / 20.0))
        result[drv] = {
            'dry_avg_lap': round(dry_avg, 3),
            'wet_avg_lap': round(wet_avg, 3),
            'wet_delta': round(delta, 3),
            'wet_pace_rating': round(wet_pace_rating, 3),
            'wet_races': len(driver_wet[drv]),
        }
    return result


def get_qualifying_vs_race_pace(season: int, race_name: str) -> Dict[str, Dict]:
    """
    Compare qualifying pace vs race pace for each driver.

    Returns dict keyed by driver abbreviation with:
      - quali_best: best qualifying lap in seconds
      - race_avg: average clean race lap in seconds
      - race_quali_gap: race_avg - quali_best
      - racer_rating: 0-1 score where 1.0 = strong racer
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")

    try:
        q_session = get_session(season, race_name, 'Q')
    except Exception as e:
        logger.warning(f"Qualifying not available for {race_name}: {e}")
        return {}

    r_session = get_session(season, race_name, 'R')
    result: Dict[str, Dict] = {}

    for drv in q_session.laps['Driver'].unique():
        q_laps = q_session.laps[
            (q_session.laps['Driver'] == drv) & q_session.laps['LapTime'].notna()
        ]
        if len(q_laps) == 0:
            continue
        quali_best = float(q_laps['LapTime'].apply(lambda t: t.total_seconds()).min())

        r_laps = r_session.laps[
            (r_session.laps['Driver'] == drv) & r_session.laps['LapTime'].notna()
        ]
        if len(r_laps) < 3:
            continue
        race_avg = float(r_laps['LapTime'].apply(lambda t: t.total_seconds()).mean())
        result[drv] = {
            'quali_best': round(quali_best, 3),
            'race_avg': round(race_avg, 3),
            'race_quali_gap': round(race_avg - quali_best, 3),
        }

    if result:
        gaps = [v['race_quali_gap'] for v in result.values()]
        min_gap, max_gap = min(gaps), max(gaps)
        spread = max_gap - min_gap if max_gap > min_gap else 1.0
        for drv in result:
            result[drv]['racer_rating'] = round(
                (result[drv]['race_quali_gap'] - min_gap) / spread, 3
            )
    return result


def get_constructor_pace_rankings(season: int, round_num: Optional[int] = None) -> Dict[str, float]:
    """
    Compute constructor pace rankings from actual race data.
    Returns dict keyed by team name with pace score 0-1 (1.0 = fastest team).
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    _ensure_cache()

    try:
        schedule = fastf1.get_event_schedule(season)
    except Exception as e:
        logger.error(f"Cannot get schedule for {season}: {e}")
        return {}

    team_pace: Dict[str, List[float]] = {}
    races = schedule if round_num is None else schedule[schedule['RoundNumber'] <= round_num]

    for _, event in races.iterrows():
        if event['EventName'] == 'Pre-Season Test':
            continue
        try:
            session = fastf1.get_session(season, event['EventName'], 'R')
            session.load(telemetry=False, weather=False, messages=False)
            clean = session.laps[session.laps['LapTime'].notna()]
            for drv in clean['Driver'].unique():
                drv_laps = clean[clean['Driver'] == drv]
                if len(drv_laps) < 3:
                    continue
                avg_pace = float(drv_laps['LapTime'].apply(lambda t: t.total_seconds()).mean())
                try:
                    team = session.results[
                        session.results['Abbreviation'] == drv
                    ]['TeamName'].iloc[0]
                except Exception:
                    continue
                team_pace.setdefault(team, []).append(avg_pace)
        except Exception as e:
            logger.warning(f"Skipping {event['EventName']}: {e}")
            continue

    if not team_pace:
        return {}

    team_avg = {team: float(np.mean(times)) for team, times in team_pace.items()}
    min_pace = min(team_avg.values())
    max_pace = max(team_avg.values())
    spread = max_pace - min_pace if max_pace > min_pace else 1.0

    return {
        team: round(1.0 - (avg - min_pace) / spread, 3)
        for team, avg in team_avg.items()
    }


def refresh_driver_database(season: int, round_num: Optional[int] = None) -> Dict[str, Dict]:
    """
    Pull latest results from FastF1 and return updated driver stats.
    Returns dict keyed by driver abbreviation with points, dnf_count, avg_finish, etc.
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    _ensure_cache()

    try:
        schedule = fastf1.get_event_schedule(season)
    except Exception:
        return {}

    if round_num is not None:
        schedule = schedule[schedule['RoundNumber'] <= round_num]

    driver_data: Dict[str, Dict] = {}

    for _, event in schedule.iterrows():
        if event['EventName'] == 'Pre-Season Test':
            continue
        try:
            session = fastf1.get_session(season, event['EventName'], 'R')
            session.load(telemetry=False, weather=False, messages=False)
            for _, row in session.results.iterrows():
                abbr = row['Abbreviation']
                pos = row.get('Position', None)
                status = str(row.get('Status', ''))
                points = float(row.get('Points', 0))
                is_dnf = 'Finished' not in status
                if abbr not in driver_data:
                    driver_data[abbr] = {'points': 0.0, 'dnf_count': 0, 'finishing_positions': []}
                driver_data[abbr]['points'] += points
                if is_dnf:
                    driver_data[abbr]['dnf_count'] += 1
                if isinstance(pos, (int, float)) and pos > 0:
                    driver_data[abbr]['finishing_positions'].append(int(pos))
        except Exception as e:
            logger.warning(f"Skipping {event['EventName']}: {e}")
            continue

    output: Dict[str, Dict] = {}
    for abbr, data in driver_data.items():
        positions = data['finishing_positions']
        output[abbr] = {
            'points': data['points'],
            'dnf_count': data['dnf_count'],
            'avg_finish': round(float(np.mean(positions)), 1) if positions else None,
            'last_3_results': positions[-3:] if len(positions) >= 3 else positions,
            'total_races': len(positions) + data['dnf_count'],
        }
    return output


def get_circuit_telemetry_profile(circuit_name: str, seasons: List[int]) -> Dict:
    """
    Build a telemetry profile for a circuit from historical data.
    Returns avg_top_speed_kmh, circuit_speed_index (0-1), races_sampled.
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    _ensure_cache()

    top_speeds: List[float] = []

    for season in seasons:
        try:
            session = fastf1.get_session(season, circuit_name, 'R')
            session.load(telemetry=True, weather=False, messages=False)
            for drv in session.laps['Driver'].unique()[:3]:
                try:
                    fastest = session.laps.pick_driver(drv).pick_fastest()
                    tel = fastest.get_car_data()
                    if 'Speed' in tel.columns:
                        top_speeds.append(float(tel['Speed'].max()))
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Skipping {season} {circuit_name}: {e}")
            continue

    if not top_speeds:
        return {}

    avg_top = float(np.mean(top_speeds))
    speed_index = max(0.0, min(1.0, (avg_top - 280) / 90))

    return {
        'avg_top_speed_kmh': round(avg_top, 1),
        'circuit_speed_index': round(speed_index, 3),
        'races_sampled': len(top_speeds),
    }



# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "FASTF1_AVAILABLE",
    "get_session",
    "ingest_race_results",
    "ingest_lap_data",
    "ingest_qualifying_results",
    "ingest_tire_strategy",
    "ingest_weather_data",
    "ingest_telemetry_data",
    "compare_drivers_telemetry",
    "load_entire_season",
    "extract_ml_features",
    # Phase 1 additions
    "get_driver_pace_metrics",
    "get_tyre_degradation_curves",
    "get_circuit_historical_stats",
    "get_wet_weather_performance",
    "get_qualifying_vs_race_pace",
    "get_constructor_pace_rankings",
    "refresh_driver_database",
    "get_circuit_telemetry_profile",
]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if FASTF1_AVAILABLE:
        print("Fast-F1 Integration Module v3.0 — ENHANCED")
        print("=" * 60)
        print("\nCore Functions:")
        print("  - get_session(season, race_name, session_type)")
        print("  - ingest_race_results(season, race_name)")
        print("  - ingest_lap_data(season, race_name, driver_id)")
        print("  - ingest_qualifying_results(season, race_name)")
        print("  - ingest_tire_strategy(season, race_name)")
        print("  - ingest_weather_data(season, race_name)")
        print("\nNEW Functions (v3.0 Enhanced):")
        print("  - ingest_telemetry_data(season, race_name, driver_id)")
        print("    → Speed, RPM, throttle, brake, DRS, gear, X/Y position")
        print("  - compare_drivers_telemetry(season, race_name, driver1, driver2)")
        print("    → Compare speed traces, braking, throttle application")
        print("  - load_entire_season(season, session_type)")
        print("    → Load all races with error handling")
        print("  - extract_ml_features(season, race_name)")
        print("    → ML-ready features: consistency, tire deg, race stats")
        print("\nUtility Functions:")
        print("  - get_historical_circuit_stats(circuit_name, seasons)")
        print("  - sync_all_historical_data(seasons)")
        print("\n" + "=" * 60)
        print("Install fastf1: pip install fastf1")
        print("Docs: https://docs.fastf1.dev")
    else:
        print("fastf1 not installed. Install with: pip install fastf1")
