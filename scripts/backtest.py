#!/usr/bin/env python3
"""
⚠️  DEVELOPER TOOL ONLY - NOT FOR END USERS

This script runs the prediction engine against completed races WITHOUT future-leaking
features, then compares predictions to actual results to measure accuracy.

FOR PREDICTIONS, USE THE STREAMLIT APP:
    streamlit run app.py

Then access: http://localhost:8501

USAGE (Developers Only):
    py scripts/backtest.py --season 2024 --season 2025
    py scripts/backtest.py --all
    
Outputs:
    - Per-session accuracy metrics
    - JSON report: backtest_results.json
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_historical_results(season: int) -> List[Dict[str, Any]]:
    """Load actual race results for a given season."""
    try:
        if season == 2026:
            from src.data.season_2026 import SEASON_RESULTS_2026
            return SEASON_RESULTS_2026
        elif season in [2024, 2025]:
            # Try FastF1 for historical seasons
            try:
                from src.data.fastf1_integration import load_entire_season
                return load_entire_season(season)
            except Exception as e:
                logger.warning(f"FastF1 failed for {season}: {e}. Using fallback data.")
                return []
        else:
            logger.warning(f"No historical data available for season {season}")
            return []
    except ImportError as e:
        logger.error(f"Failed to import season data: {e}")
        return []


def predict_race_for_backtest(circuit_id: str, rain_probability: float = None, n_simulations: int = 5000):
    """Run prediction without future-leaking features."""
    from src.engine.predictor import predict as run_predict, PredictionRequest
    
    result = run_predict(
        PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            seed=None,  # No fixed seed for realistic variance
            grid_overrides={},  # No grid overrides (simulates pre-race prediction)
            use_live_data=False,  # Don't use live data for backtesting
        )
    )
    
    return result


def evaluate_predictions(predictions: List[Dict], actual_results: List[Dict]) -> Dict[str, Any]:
    """Compare predicted vs actual results and compute accuracy metrics."""
    
    # Build lookup maps
    pred_by_driver = {p["driver_id"]: p for p in predictions}
    actual_by_driver = {r["driver"]: r for r in actual_results}
    
    # Sort by predicted position
    sorted_preds = sorted(predictions, key=lambda x: x.get("expected_position_float", x.get("predicted_position", 999)))
    sorted_actuals = sorted(actual_results, key=lambda x: x.get("position", 999))
    
    # Extract top-3 predictions and actuals
    pred_top3 = [p["driver_id"] for p in sorted_preds[:3]]
    actual_top3 = [r["driver"] for r in sorted_actuals[:3]]
    
    # Calculate metrics
    metrics = {
        "top3_correct": len(set(pred_top3) & set(actual_top3)),
        "top3_total": 3,
        "winner_in_pred_top3": sorted_actuals[0]["driver"] in pred_top3 if sorted_actuals else False,
        "points_finishers_correct": 0,
        "points_finishers_total": min(10, len(sorted_actuals)),
    }
    
    # Check points finishers (top 10)
    pred_points = set(p["driver_id"] for p in sorted_preds[:10])
    actual_points = set(r["driver"] for r in sorted_actuals[:10])
    metrics["points_finishers_correct"] = len(pred_points & actual_points)
    
    # Position correlation (Spearman-like)
    position_errors = []
    for driver_id in pred_by_driver:
        if driver_id in actual_by_driver:
            pred_pos = pred_by_driver[driver_id].get("expected_position_float", 999)
            actual_pos = actual_by_driver[driver_id].get("position", 999)
            position_errors.append(abs(pred_pos - actual_pos))
    
    metrics["avg_position_error"] = sum(position_errors) / len(position_errors) if position_errors else None
    metrics["median_position_error"] = sorted(position_errors)[len(position_errors)//2] if position_errors else None
    
    return metrics


def run_backtest(seasons: List[int], output_file: str = None):
    """Run full backtest across specified seasons."""
    
    all_metrics = {
        "sessions": [],
        "summary": {},
    }
    
    session_type_counts = defaultdict(int)
    session_type_accuracy = defaultdict(list)
    
    for season in seasons:
        logger.info(f"\n{'='*60}")
        logger.info(f"Backtesting Season {season}")
        logger.info(f"{'='*60}\n")
        
        races = load_historical_results(season)
        
        if not races:
            logger.warning(f"No races found for season {season}. Skipping.")
            continue
        
        for race in races:
            circuit_id = race.get("circuit", race.get("location", "unknown"))
            race_name = race.get("name", circuit_id)
            round_num = race.get("round", "?")
            
            logger.info(f"Processing Round {round_num}: {race_name} ({circuit_id})")
            
            try:
                # Run prediction (simulate pre-race forecast)
                result = predict_race_for_backtest(
                    circuit_id=circuit_id,
                    rain_probability=race.get("rain_probability_typical", 0.2),
                    n_simulations=5000,
                )
                
                predictions = result.get("predictions", [])
                actual_results = race.get("results", [])
                
                if not predictions or not actual_results:
                    logger.warning(f"  ⚠️  Missing data for {race_name}. Skipping.")
                    continue
                
                # Evaluate
                metrics = evaluate_predictions(predictions, actual_results)
                
                # Record session
                session_record = {
                    "season": season,
                    "round": round_num,
                    "circuit": circuit_id,
                    "race_name": race_name,
                    "date": race.get("date", ""),
                    "metrics": metrics,
                }
                all_metrics["sessions"].append(session_record)
                
                # Aggregate by session type (Sunday race for now)
                session_type_counts["sunday_race"] += 1
                session_type_accuracy["sunday_race"].append(metrics)
                
                # Log per-race results
                logger.info(f"  ✓ Top-3 Correct: {metrics['top3_correct']}/{metrics['top3_total']}")
                logger.info(f"  ✓ Winner in Pred Top-3: {'Yes' if metrics['winner_in_pred_top3'] else 'No'}")
                logger.info(f"  ✓ Points Finishers: {metrics['points_finishers_correct']}/{metrics['points_finishers_total']}")
                if metrics.get("avg_position_error"):
                    logger.info(f"  ✓ Avg Position Error: {metrics['avg_position_error']:.2f}")
                
            except Exception as e:
                logger.error(f"  ✗ Failed to process {race_name}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
    
    # Compute summary statistics
    logger.info(f"\n{'='*60}")
    logger.info("BACKTEST SUMMARY")
    logger.info(f"{'='*60}\n")
    
    for session_type, acc_list in session_type_accuracy.items():
        if not acc_list:
            continue
        
        n_races = len(acc_list)
        avg_top3_correct = sum(m["top3_correct"] for m in acc_list) / n_races
        top3_accuracy = avg_top3_correct / 3 * 100
        
        winner_in_top3_count = sum(1 for m in acc_list if m["winner_in_pred_top3"])
        winner_accuracy = winner_in_top3_count / n_races * 100
        
        avg_points_correct = sum(m["points_finishers_correct"] for m in acc_list) / n_races
        avg_points_total = sum(m["points_finishers_total"] for m in acc_list) / n_races
        points_accuracy = (avg_points_correct / avg_points_total * 100) if avg_points_total > 0 else 0
        
        avg_pos_errors = [m["avg_position_error"] for m in acc_list if m.get("avg_position_error")]
        overall_avg_pos_error = sum(avg_pos_errors) / len(avg_pos_errors) if avg_pos_errors else None
        
        summary = {
            "session_type": session_type,
            "total_races": n_races,
            "top3_accuracy_pct": round(top3_accuracy, 2),
            "winner_in_top3_pct": round(winner_accuracy, 2),
            "points_finisher_accuracy_pct": round(points_accuracy, 2),
            "avg_points_correct": round(avg_points_correct, 2),
            "avg_position_error": round(overall_avg_pos_error, 2) if overall_avg_pos_error else None,
        }
        
        all_metrics["summary"][session_type] = summary
        
        logger.info(f"Session Type: {session_type.upper()}")
        logger.info(f"  Total Races: {n_races}")
        logger.info(f"  Top-3 Accuracy: {top3_accuracy:.1f}% (target: ≥70%)")
        logger.info(f"  Winner in Top-3: {winner_accuracy:.1f}%")
        logger.info(f"  Points Finishers: {points_accuracy:.1f}% (target: ≥70%)")
        logger.info(f"  Avg Position Error: {overall_avg_pos_error:.2f}" if overall_avg_pos_error else "  Avg Position Error: N/A")
        logger.info("")
    
    # Save results
    if output_file:
        with open(output_file, "w") as f:
            json.dump(all_metrics, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")
    
    return all_metrics


def main():
    parser = argparse.ArgumentParser(description="F1 Predictor Backtesting Script")
    parser.add_argument("--season", type=int, nargs="+", help="Season(s) to backtest (e.g., --season 2024 2025)")
    parser.add_argument("--all", action="store_true", help="Backtest all available seasons (2024, 2025, 2026)")
    parser.add_argument("--output", type=str, default="backtest_results.json", help="Output JSON file path")
    
    args = parser.parse_args()
    
    if args.all:
        seasons = [2024, 2025, 2026]
    elif args.season:
        seasons = args.season
    else:
        seasons = [2024, 2025]  # Default: test historical seasons
    
    logger.info(f"Starting backtest for seasons: {seasons}")
    logger.info(f"Output file: {args.output}")
    
    start_time = datetime.now()
    results = run_backtest(seasons, output_file=args.output)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"\nBacktest completed in {elapsed:.1f} seconds")
    
    # Exit with appropriate code
    summary = results.get("summary", {})
    if summary:
        worst_top3 = min(s.get("top3_accuracy_pct", 0) for s in summary.values())
        if worst_top3 < 50:
            logger.warning("⚠️  WARNING: Top-3 accuracy below 50%. Model needs significant improvement.")
            sys.exit(1)
        elif worst_top3 < 70:
            logger.warning("⚠️  Top-3 accuracy below 70% target. Continue tuning model parameters.")
            sys.exit(0)
        else:
            logger.info("✅ Top-3 accuracy meets 70% target!")
            sys.exit(0)
    else:
        logger.error("No summary data generated. Check logs for errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
