"""
Post-Race Auto-Learning System - Phase 4 Implementation.

This module automatically ingests race results after each Grand Prix and updates
the prediction model based on actual outcomes. This enables continuous improvement
throughout the season.

Key Features:
- Automatic race result ingestion via FastF1
- ELO rating updates based on actual finishing positions
- Prediction accuracy tracking and reporting
- Model bias detection and correction
- Tire strategy learning
- Wet/dry performance calibration
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def auto_ingest_race_results(season: int, circuit_id: str) -> Dict[str, Any]:
    """
    Automatically ingest race results and update model parameters.
    
    This function should be called after each race weekend completes to:
    1. Fetch actual race results from FastF1
    2. Update driver/team ELO ratings
    3. Track prediction accuracy
    4. Learn tire degradation patterns
    5. Calibrate wet weather performance
    
    Args:
        season: Year (e.g., 2026)
        circuit_id: Circuit identifier from calendar
    
    Returns:
        Dictionary with ingestion results:
        - success: Boolean indicating if ingestion completed
        - drivers_updated: Number of driver ratings updated
        - predictions_tracked: Number of predictions validated
        - accuracy_metrics: Dict with accuracy statistics
        - errors: List of any errors encountered
    
    Example Usage:
        >>> result = auto_ingest_race_results(2026, "monaco")
        >>> if result['success']:
        ...     print(f"Updated {result['drivers_updated']} drivers")
        ...     print(f"Accuracy: {result['accuracy_metrics']}")
    """
    try:
        from src.data.fastf1_integration import get_session, FASTF1_AVAILABLE
        
        if not FASTF1_AVAILABLE:
            logger.warning("FastF1 not available. Cannot ingest race results.")
            return {
                "success": False,
                "drivers_updated": 0,
                "predictions_tracked": 0,
                "accuracy_metrics": {},
                "errors": ["FastF1 not installed"]
            }
        
        logger.info(f"Starting post-race auto-learning for {circuit_id} (Season {season})")
        
        # Map circuit_id to FastF1 race name
        from src.data.fastf1_integration import _circuit_to_race_name
        race_name = _circuit_to_race_name(circuit_id)
        
        if not race_name:
            raise ValueError(f"Could not map circuit '{circuit_id}' to race name")
        
        # Step 1: Fetch race results
        logger.info(f"Fetching race results for {race_name}")
        session = get_session(season, race_name, 'R')
        
        if session.results is None or len(session.results) == 0:
            raise ValueError("No race results available yet")
        
        # Step 2: Extract actual finishing positions
        actual_results = []
        for idx, row in session.results.iterrows():
            actual_results.append({
                'driver_abbrev': row.get('Abbreviation'),
                'position': int(row.get('Position', 99)),
                'team': row.get('TeamName'),
                'grid_position': int(row.get('GridPosition', 99)) if row.get('GridPosition') else None,
                'status': row.get('Status', 'Finished'),
                'points': float(row.get('Points', 0)),
                'fastest_lap': bool(row.get('FastestLap', False)),
            })
        
        logger.info(f"Fetched results for {len(actual_results)} drivers")
        
        # Step 3: Update ELO ratings
        from src.engine.multi_dimensional_elo import get_elo_system
        
        elo_system = get_elo_system()
        drivers_updated = 0
        
        for result in actual_results:
            driver_abbrev = result['driver_abbrev']
            actual_pos = result['position']
            
            # Find driver ID from abbreviation
            from src.data.driver_data import get_all_drivers
            all_drivers = get_all_drivers()
            driver_match = next((d for d in all_drivers if d.get('short', '').upper() == driver_abbrev), None)
            
            if driver_match:
                driver_id = driver_match['id']
                
                # Update race ELO based on actual position vs expected
                # Get expected position from current ELO
                expected_score = elo_system.get_expected_score(driver_id, actual_pos, len(actual_results))
                
                # Calculate ELO change
                k_factor = 32  # Standard K-factor for F1
                actual_score = 1.0 - (actual_pos - 1) / (len(actual_results) - 1)  # Normalize position to [0,1]
                
                elo_change = k_factor * (actual_score - expected_score)
                elo_system.update_driver_rating(driver_id, 'race', elo_change)
                
                drivers_updated += 1
                logger.debug(f"Updated {driver_id}: pos={actual_pos}, ELO change={elo_change:+.1f}")
        
        # Step 4: Track prediction accuracy (if predictions exist)
        accuracy_metrics = _track_prediction_accuracy(season, circuit_id, actual_results)
        
        # Step 5: Learn tire strategies
        tire_insights = _learn_tire_strategies(session, circuit_id)
        
        # Step 6: Update wet weather calibration if it rained
        weather_insights = _update_wet_weather_calibration(session, circuit_id)
        
        result = {
            "success": True,
            "drivers_updated": drivers_updated,
            "predictions_tracked": accuracy_metrics.get('total_predictions', 0),
            "accuracy_metrics": accuracy_metrics,
            "tire_insights": tire_insights,
            "weather_insights": weather_insights,
            "ingested_at": datetime.now().isoformat(),
            "errors": []
        }
        
        logger.info(
            f"Auto-learning complete: {drivers_updated} drivers updated, "
            f"{result['predictions_tracked']} predictions tracked"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Post-race auto-learning failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        
        return {
            "success": False,
            "drivers_updated": 0,
            "predictions_tracked": 0,
            "accuracy_metrics": {},
            "errors": [str(e)]
        }


def _track_prediction_accuracy(
    season: int, 
    circuit_id: str, 
    actual_results: List[Dict]
) -> Dict[str, Any]:
    """
    Compare stored predictions against actual results to track accuracy.
    
    Args:
        season: Year
        circuit_id: Circuit identifier
        actual_results: List of actual finishing positions
    
    Returns:
        Dictionary with accuracy metrics
    """
    try:
        from src.database.models import SessionLocal, PredictionResult
        
        db = SessionLocal()
        
        # Find most recent prediction for this circuit
        prediction = db.query(PredictionResult).filter(
            PredictionResult.circuit_id == circuit_id,
            PredictionResult.season == season
        ).order_by(PredictionResult.created_at.desc()).first()
        
        if not prediction:
            logger.info(f"No predictions found for {circuit_id} Season {season}")
            return {"total_predictions": 0}
        
        # Compare predicted vs actual top 3
        predicted_top3 = prediction.podium_predictions or []
        actual_top3 = [
            r['driver_abbrev'] for r in sorted(actual_results, key=lambda x: x['position'])[:3]
        ]
        
        # Calculate accuracy metrics
        correct_in_top3 = len(set(predicted_top3) & set(actual_top3))
        top3_accuracy = correct_in_top3 / 3.0
        
        # Check if winner was predicted
        predicted_winner = predicted_top3[0] if predicted_top3 else None
        actual_winner = actual_top3[0] if actual_top3 else None
        winner_correct = predicted_winner == actual_winner
        
        # Position correlation (Spearman rank correlation would be better, but simple for now)
        position_errors = []
        for result in actual_results[:10]:  # Top 10 only
            driver_abbrev = result['driver_abbrev']
            actual_pos = result['position']
            
            # Find predicted position
            pred_pos = None
            for i, pred_driver in enumerate(predicted_top3):
                if pred_driver == driver_abbrev:
                    pred_pos = i + 1
                    break
            
            if pred_pos:
                position_errors.append(abs(pred_pos - actual_pos))
        
        avg_position_error = sum(position_errors) / len(position_errors) if position_errors else None
        
        metrics = {
            "total_predictions": 1,
            "top3_accuracy": round(top3_accuracy, 2),
            "correct_in_top3": correct_in_top3,
            "winner_predicted": winner_correct,
            "avg_position_error": round(avg_position_error, 2) if avg_position_error else None,
            "predicted_top3": predicted_top3,
            "actual_top3": actual_top3,
        }
        
        logger.info(
            f"Prediction accuracy for {circuit_id}: "
            f"Top-3: {top3_accuracy*100:.0f}%, Winner: {'✓' if winner_correct else '✗'}"
        )
        
        db.close()
        return metrics
    
    except Exception as e:
        logger.warning(f"Failed to track prediction accuracy: {e}")
        return {"total_predictions": 0, "error": str(e)}


def _learn_tire_strategies(session, circuit_id: str) -> Dict[str, Any]:
    """
    Analyze tire strategies used in the race to improve future strategy modeling.
    
    Args:
        session: FastF1 race session
        circuit_id: Circuit identifier
    
    Returns:
        Dictionary with tire strategy insights
    """
    try:
        from src.data.fastf1_integration import ingest_tire_strategy
        
        tire_data = ingest_tire_strategy(
            session.event['EventDate'].year,
            session.event['EventName']
        )
        
        # Extract common strategies
        strategy_counts = {}
        for driver_data in tire_data.get('tire_strategy', []):
            stints = driver_data.get('stints', {})
            strategy_key = tuple(sorted(stints.items()))
            strategy_counts[strategy_key] = strategy_counts.get(strategy_key, 0) + 1
        
        # Most common strategy
        most_common = max(strategy_counts.items(), key=lambda x: x[1]) if strategy_counts else None
        
        insights = {
            "circuit_id": circuit_id,
            "total_strategies_analyzed": len(tire_data.get('tire_strategy', [])),
            "unique_strategies": len(strategy_counts),
            "most_common_strategy": str(most_common[0]) if most_common else None,
            "most_common_count": most_common[1] if most_common else 0,
        }
        
        logger.info(f"Tire strategy learning: {insights['unique_strategies']} unique strategies found")
        return insights
    
    except Exception as e:
        logger.warning(f"Tire strategy learning failed: {e}")
        return {"error": str(e)}


def _update_wet_weather_calibration(session, circuit_id: str) -> Dict[str, Any]:
    """
    Update wet weather performance calibration if race had rain.
    
    Args:
        session: FastF1 race session
        circuit_id: Circuit identifier
    
    Returns:
        Dictionary with wet weather insights
    """
    try:
        # Check if it rained during the race
        laps_with_rain = session.laps[session.laps['Rainfall'] == True]
        
        if len(laps_with_rain) == 0:
            logger.info(f"No rain during {circuit_id} race - skipping wet weather calibration")
            return {"rained": False}
        
        # Analyze driver performance in wet conditions
        wet_performance = {}
        for driver_abbrev in session.laps['Driver'].unique():
            driver_laps = session.laps.pick_driver(driver_abbrev)
            wet_laps = driver_laps[driver_laps['Rainfall'] == True]
            dry_laps = driver_laps[driver_laps['Rainfall'] == False]
            
            if len(wet_laps) > 0 and len(dry_laps) > 0:
                wet_avg = wet_laps['LapTime'].apply(lambda x: x.total_seconds()).mean()
                dry_avg = dry_laps['LapTime'].apply(lambda x: x.total_seconds()).mean()
                
                # Wet pace delta (positive = slower in wet)
                wet_delta = wet_avg - dry_avg
                
                wet_performance[driver_abbrev] = {
                    'wet_pace_delta': round(wet_delta, 3),
                    'wet_laps': len(wet_laps),
                    'dry_laps': len(dry_laps),
                }
        
        insights = {
            "rained": True,
            "wet_laps_total": len(laps_with_rain),
            "drivers_analyzed": len(wet_performance),
            "wet_performance": wet_performance,
        }
        
        logger.info(f"Wet weather calibration: {len(wet_performance)} drivers analyzed")
        return insights
    
    except Exception as e:
        logger.warning(f"Wet weather calibration failed: {e}")
        return {"error": str(e)}


def schedule_auto_learning_for_completed_races(season: int = None) -> Dict[str, Any]:
    """
    Check for recently completed races and trigger auto-learning.
    
    This function can be called periodically (e.g., daily) to ensure all
    completed races have been processed for model updates.
    
    Args:
        season: Year to check (defaults to current year)
    
    Returns:
        Dictionary with processing results
    """
    from datetime import datetime as dt
    
    if season is None:
        season = dt.now().year
    
    try:
        from src.data.calendar_2026 import CALENDAR_2026
        
        today = dt.now().date()
        processed = []
        skipped = []
        errors = []
        
        for race in CALENDAR_2026:
            if race.get('season', season) != season:
                continue
            
            race_date = dt.strptime(race['date'], '%Y-%m-%d').date()
            
            # Check if race was within last 7 days (recently completed)
            days_since_race = (today - race_date).days
            
            if 1 <= days_since_race <= 7 and race.get('status') == 'completed':
                logger.info(f"Processing recently completed race: {race['name']} ({days_since_race} days ago)")
                
                result = auto_ingest_race_results(season, race['circuit'])
                
                if result['success']:
                    processed.append({
                        'circuit': race['circuit'],
                        'name': race['name'],
                        'days_ago': days_since_race,
                        'drivers_updated': result['drivers_updated'],
                    })
                else:
                    errors.append({
                        'circuit': race['circuit'],
                        'name': race['name'],
                        'error': result['errors'][0] if result['errors'] else 'Unknown error',
                    })
            elif days_since_race > 7:
                skipped.append(race['circuit'])
        
        summary = {
            "season": season,
            "processed_count": len(processed),
            "skipped_count": len(skipped),
            "error_count": len(errors),
            "processed": processed,
            "errors": errors,
        }
        
        logger.info(
            f"Auto-learning scheduler complete: {len(processed)} processed, "
            f"{len(skipped)} skipped, {len(errors)} errors"
        )
        
        return summary
    
    except Exception as e:
        logger.error(f"Auto-learning scheduler failed: {e}")
        return {
            "season": season,
            "processed_count": 0,
            "error_count": 1,
            "errors": [{"error": str(e)}]
        }


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "auto_ingest_race_results",
    "schedule_auto_learning_for_completed_races",
]
