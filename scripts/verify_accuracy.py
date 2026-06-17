#!/usr/bin/env python3
"""
⚠️  DEVELOPER TOOL ONLY - NOT FOR END USERS

This script runs the prediction engine on completed races and measures accuracy
against actual results to verify if the 80% target is achievable.

FOR PREDICTIONS, USE THE STREAMLIT APP:
    streamlit run app.py

Then access: http://localhost:8501

USAGE (Developers Only):
    py scripts/verify_accuracy.py --season 2024
    py scripts/verify_accuracy.py --all
    
OUTPUTS:
    - Console summary of accuracy metrics
    - Detailed JSON report: accuracy_report_YYYYMMDD.json
"""

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_historical_data(season: int) -> List[Dict[str, Any]]:
    """Load actual race results for a given season."""
    try:
        if season == 2026:
            from src.data.season_2026 import SEASON_RESULTS_2026
            logger.info(f"Loaded {len(SEASON_RESULTS_2026)} races from 2026 season data")
            return SEASON_RESULTS_2026
        
        elif season in [2024, 2025]:
            # Try FastF1 for historical seasons
            try:
                from src.data.fastf1_integration import load_entire_season
                races = load_entire_season(season)
                logger.info(f"Loaded {len(races)} races from {season} via FastF1")
                return races
            except Exception as e:
                logger.warning(f"FastF1 failed for {season}: {e}")
                logger.info("Using fallback: No historical data available for this season")
                return []
        
        else:
            logger.warning(f"No data source configured for season {season}")
            return []
    
    except ImportError as e:
        logger.error(f"Failed to import season data: {e}")
        return []


def run_prediction(circuit_id: str, rain_prob: Optional[float] = None, 
                   n_simulations: int = 5000, use_qualifying_grid: bool = False) -> Dict:
    """Run prediction for a specific circuit."""
    from src.engine.predictor import predict as run_predict, PredictionRequest
    
    try:
        result = run_predict(
            PredictionRequest(
                circuit_id=circuit_id,
                rain_probability=rain_prob,
                n_simulations=n_simulations,
                seed=None,  # No fixed seed for realistic variance
                grid_overrides={},  # Empty for pre-qualifying predictions
                use_live_data=use_qualifying_grid,  # Use live data if qualifying available
            )
        )
        return result
    
    except Exception as e:
        logger.error(f"Prediction failed for {circuit_id}: {e}")
        return {"predictions": [], "error": str(e)}


def calculate_accuracy_metrics(predictions: List[Dict], actual_results: List[Dict]) -> Dict[str, Any]:
    """
    Calculate comprehensive accuracy metrics comparing predictions to actual results.
    
    Metrics:
    - Top-3 accuracy: How many of top-3 predicted drivers finished in top-3
    - Winner prediction: Was the actual winner in predicted top-3?
    - Points finisher accuracy: How many of top-10 predicted actually scored points
    - Position correlation: Spearman-like correlation between predicted and actual positions
    - Mean absolute error: Average position prediction error
    """
    
    if not predictions or not actual_results:
        return {"error": "Missing predictions or actual results"}
    
    # Build lookup maps
    pred_by_driver = {p["driver_id"]: p for p in predictions}
    actual_by_driver = {r["driver"]: r for r in actual_results}
    
    # Sort by predicted and actual positions
    sorted_preds = sorted(predictions, key=lambda x: x.get("expected_position_float", x.get("predicted_position", 999)))
    sorted_actuals = sorted(actual_results, key=lambda x: x.get("position", 999))
    
    # Extract driver IDs in order
    pred_top3 = [p["driver_id"] for p in sorted_preds[:3]]
    actual_top3 = [r["driver"] for r in sorted_actuals[:3]]
    
    pred_top10 = [p["driver_id"] for p in sorted_preds[:10]]
    actual_top10 = [r["driver"] for r in sorted_actuals[:10]]
    
    # Calculate metrics
    metrics = {
        # Top-3 accuracy
        "top3_intersection": list(set(pred_top3) & set(actual_top3)),
        "top3_correct_count": len(set(pred_top3) & set(actual_top3)),
        "top3_accuracy_pct": len(set(pred_top3) & set(actual_top3)) / 3 * 100,
        
        # Winner prediction
        "actual_winner": sorted_actuals[0]["driver"] if sorted_actuals else None,
        "winner_in_pred_top3": sorted_actuals[0]["driver"] in pred_top3 if sorted_actuals else False,
        "winner_predicted_position": pred_by_driver.get(sorted_actuals[0]["driver"], {}).get("expected_position_float", 999) if sorted_actuals else None,
        
        # Points finisher accuracy (top 10)
        "points_intersection": list(set(pred_top10) & set(actual_top10)),
        "points_correct_count": len(set(pred_top10) & set(actual_top10)),
        "points_accuracy_pct": len(set(pred_top10) & set(actual_top10)) / min(10, len(actual_top10)) * 100 if actual_top10 else 0,
        
        # Position errors
        "position_errors": {},
        "absolute_position_errors": [],
    }
    
    # Calculate position-by-position errors
    for driver_id in pred_by_driver:
        if driver_id in actual_by_driver:
            pred_pos = pred_by_driver[driver_id].get("expected_position_float", 999)
            actual_pos = actual_by_driver[driver_id].get("position", 999)
            error = abs(pred_pos - actual_pos)
            
            metrics["position_errors"][driver_id] = {
                "predicted": round(pred_pos, 2),
                "actual": actual_pos,
                "error": round(error, 2)
            }
            metrics["absolute_position_errors"].append(error)
    
    # Aggregate position metrics
    if metrics["absolute_position_errors"]:
        metrics["mean_absolute_error"] = sum(metrics["absolute_position_errors"]) / len(metrics["absolute_position_errors"])
        metrics["median_absolute_error"] = np.median(metrics["absolute_position_errors"])
        metrics["max_absolute_error"] = max(metrics["absolute_position_errors"])
        
        # Percentage within certain thresholds
        within_1 = sum(1 for e in metrics["absolute_position_errors"] if e <= 1) / len(metrics["absolute_position_errors"]) * 100
        within_2 = sum(1 for e in metrics["absolute_position_errors"] if e <= 2) / len(metrics["absolute_position_errors"]) * 100
        within_3 = sum(1 for e in metrics["absolute_position_errors"] if e <= 3) / len(metrics["absolute_position_errors"]) * 100
        
        metrics["pct_within_1_position"] = within_1
        metrics["pct_within_2_positions"] = within_2
        metrics["pct_within_3_positions"] = within_3
    
    return metrics


def generate_summary_report(all_race_metrics: List[Dict]) -> Dict[str, Any]:
    """Generate aggregate summary across all races."""
    
    if not all_race_metrics:
        return {"error": "No race metrics to summarize"}
    
    n_races = len(all_race_metrics)
    
    # Aggregate top-3 accuracy
    avg_top3_accuracy = sum(m["top3_accuracy_pct"] for m in all_race_metrics) / n_races
    top3_accuracies = [m["top3_accuracy_pct"] for m in all_race_metrics]
    
    # Aggregate winner prediction
    winner_in_top3_count = sum(1 for m in all_race_metrics if m.get("winner_in_pred_top3", False))
    winner_accuracy = winner_in_top3_count / n_races * 100
    
    # Aggregate points accuracy
    avg_points_accuracy = sum(m["points_accuracy_pct"] for m in all_race_metrics) / n_races
    
    # Aggregate position errors
    all_mean_errors = [m.get("mean_absolute_error", 0) for m in all_race_metrics if "mean_absolute_error" in m]
    overall_mean_error = sum(all_mean_errors) / len(all_mean_errors) if all_mean_errors else None
    
    all_median_errors = [m.get("median_absolute_error", 0) for m in all_race_metrics if "median_absolute_error" in m]
    overall_median_error = np.median(all_median_errors) if all_median_errors else None
    
    # Position threshold accuracies
    avg_within_1 = sum(m.get("pct_within_1_position", 0) for m in all_race_metrics) / n_races
    avg_within_2 = sum(m.get("pct_within_2_positions", 0) for m in all_race_metrics) / n_races
    avg_within_3 = sum(m.get("pct_within_3_positions", 0) for m in all_race_metrics) / n_races
    
    summary = {
        "total_races_analyzed": n_races,
        "analysis_date": datetime.now().isoformat(),
        
        "top3_accuracy": {
            "average_pct": round(avg_top3_accuracy, 2),
            "min_pct": round(min(top3_accuracies), 2),
            "max_pct": round(max(top3_accuracies), 2),
            "std_dev": round(np.std(top3_accuracies), 2),
            "target_80_pct": "✅ ACHIEVED" if avg_top3_accuracy >= 80 else f"❌ GAP: {80 - avg_top3_accuracy:.1f}%",
        },
        
        "winner_prediction": {
            "accuracy_pct": round(winner_accuracy, 2),
            "correct_count": winner_in_top3_count,
            "total_races": n_races,
        },
        
        "points_finisher_accuracy": {
            "average_pct": round(avg_points_accuracy, 2),
            "target_70_pct": "✅ ACHIEVED" if avg_points_accuracy >= 70 else f"❌ GAP: {70 - avg_points_accuracy:.1f}%",
        },
        
        "position_prediction": {
            "mean_absolute_error": round(overall_mean_error, 2) if overall_mean_error else None,
            "median_absolute_error": round(overall_median_error, 2) if overall_median_error else None,
            "pct_within_1_position": round(avg_within_1, 2),
            "pct_within_2_positions": round(avg_within_2, 2),
            "pct_within_3_positions": round(avg_within_3, 2),
        },
        
        "verdict": {
            "meets_80_pct_target": avg_top3_accuracy >= 80,
            "recommendation": _generate_recommendation(avg_top3_accuracy, winner_accuracy, avg_points_accuracy),
        }
    }
    
    return summary


def _generate_recommendation(top3_acc: float, winner_acc: float, points_acc: float) -> str:
    """Generate actionable recommendation based on accuracy metrics."""
    
    if top3_acc >= 80:
        return "🎉 EXCELLENT! Model meets 80% accuracy target. Continue monitoring and consider deploying to production."
    
    elif top3_acc >= 70:
        improvements = []
        if winner_acc < 75:
            improvements.append("- Improve winner prediction (currently {:.1f}%)".format(winner_acc))
        if points_acc < 70:
            improvements.append("- Improve points finisher prediction (currently {:.1f}%)".format(points_acc))
        
        return f"⚠️ GOOD but needs refinement. Top-3 accuracy is {top3_acc:.1f}%.\nRecommendations:\n" + "\n".join(improvements) + "\n- Consider using real qualifying grid data (+15-20% improvement expected)"
    
    else:
        return f"❌ BELOW TARGET. Top-3 accuracy is {top3_acc:.1f}%.\nCritical actions needed:\n- Ensure real qualifying grid is used for Sunday predictions\n- Train isotonic calibration on historical data\n- Review feature weights in feature_engineering.py\n- Increase simulation count to 10,000+"


def verify_accuracy(seasons: List[int], output_file: str = None, use_qualifying_data: bool = True):
    """Run full accuracy verification across specified seasons."""
    
    logger.info("=" * 80)
    logger.info("F1 PREDICTOR ACCURACY VERIFICATION")
    logger.info("=" * 80)
    logger.info(f"Seasons to test: {seasons}")
    logger.info(f"Use qualifying grid data: {'Yes' if use_qualifying_data else 'No'}")
    logger.info("=" * 80 + "\n")
    
    all_race_metrics = []
    
    for season in seasons:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Season {season}")
        logger.info(f"{'='*80}\n")
        
        races = load_historical_data(season)
        
        if not races:
            logger.warning(f"No races found for season {season}. Skipping.\n")
            continue
        
        for i, race in enumerate(races, 1):
            circuit_id = race.get("circuit", race.get("location", "unknown"))
            race_name = race.get("name", circuit_id)
            round_num = race.get("round", "?")
            
            logger.info(f"[{i}/{len(races)}] Round {round_num}: {race_name} ({circuit_id})")
            
            try:
                # Run prediction
                result = run_prediction(
                    circuit_id=circuit_id,
                    rain_prob=race.get("rain_probability_typical", 0.2),
                    n_simulations=5000,
                    use_qualifying_grid=use_qualifying_data,
                )
                
                if "error" in result:
                    logger.warning(f"  ⚠️  Prediction error: {result['error']}")
                    continue
                
                predictions = result.get("predictions", [])
                actual_results = race.get("results", [])
                
                if not predictions or not actual_results:
                    logger.warning(f"  ⚠️  Missing data. Skipping.")
                    continue
                
                # Calculate accuracy
                metrics = calculate_accuracy_metrics(predictions, actual_results)
                
                # Add race metadata
                metrics["season"] = season
                metrics["round"] = round_num
                metrics["circuit"] = circuit_id
                metrics["race_name"] = race_name
                
                all_race_metrics.append(metrics)
                
                # Log per-race results
                logger.info(f"  ✓ Top-3 Accuracy: {metrics['top3_accuracy_pct']:.1f}%")
                logger.info(f"  ✓ Winner in Pred Top-3: {'Yes' if metrics['winner_in_pred_top3'] else 'No'}")
                logger.info(f"  ✓ Points Finishers: {metrics['points_accuracy_pct']:.1f}%")
                if "mean_absolute_error" in metrics:
                    logger.info(f"  ✓ Mean Position Error: {metrics['mean_absolute_error']:.2f}")
                
            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                import traceback
                logger.debug(traceback.format_exc())
    
    # Generate summary
    logger.info(f"\n{'='*80}")
    logger.info("ACCURACY SUMMARY")
    logger.info(f"{'='*80}\n")
    
    summary = generate_summary_report(all_race_metrics)
    
    # Print summary
    print("\n" + "=" * 80)
    print("FINAL ACCURACY REPORT")
    print("=" * 80)
    
    if not summary or "total_races_analyzed" not in summary:
        print("\n⚠️  No races were analyzed. Possible reasons:")
        print("   • No historical data available for selected seasons")
        print("   • FastF1 connection failed")
        print("   • All races were skipped due to errors")
        print("\n💡 Recommendations:")
        print("   1. Check your internet connection for FastF1")
        print("   2. Try with --season 2026 only (uses local data)")
        print("   3. Verify FastF1 is installed: py -m pip show fastf1")
        print("=" * 80 + "\n")
        
        logger.warning("No accuracy data generated. Check data sources.")
        return report
    
    print(f"\nTotal Races Analyzed: {summary['total_races_analyzed']}")
    print(f"\n📊 TOP-3 ACCURACY:")
    print(f"   Average: {summary['top3_accuracy']['average_pct']:.1f}%")
    print(f"   Range: {summary['top3_accuracy']['min_pct']:.1f}% - {summary['top3_accuracy']['max_pct']:.1f}%")
    print(f"   Target (80%): {summary['top3_accuracy']['target_80_pct']}")
    
    print(f"\n🏆 WINNER PREDICTION:")
    print(f"   Accuracy: {summary['winner_prediction']['accuracy_pct']:.1f}%")
    print(f"   Correct: {summary['winner_prediction']['correct_count']}/{summary['winner_prediction']['total_races']}")
    
    print(f"\n🎯 POINTS FINISHER ACCURACY:")
    print(f"   Average: {summary['points_finisher_accuracy']['average_pct']:.1f}%")
    print(f"   Target (70%): {summary['points_finisher_accuracy']['target_70_pct']}")
    
    print(f"\n📍 POSITION PREDICTION:")
    if summary['position_prediction']['mean_absolute_error']:
        print(f"   Mean Absolute Error: {summary['position_prediction']['mean_absolute_error']:.2f} positions")
        print(f"   Median Absolute Error: {summary['position_prediction']['median_absolute_error']:.2f} positions")
    print(f"   Within 1 Position: {summary['position_prediction']['pct_within_1_position']:.1f}%")
    print(f"   Within 2 Positions: {summary['position_prediction']['pct_within_2_positions']:.1f}%")
    print(f"   Within 3 Positions: {summary['position_prediction']['pct_within_3_positions']:.1f}%")
    
    print(f"\n💡 RECOMMENDATION:")
    print(summary['verdict']['recommendation'])
    print("=" * 80 + "\n")
    
    # Save detailed report
    report = {
        "summary": summary,
        "per_race_metrics": all_race_metrics,
    }
    
    if output_file:
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Detailed report saved to: {output_file}")
    
    return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify F1 Predictor accuracy against historical data")
    parser.add_argument("--season", type=int, nargs="+", help="Season(s) to test (e.g., --season 2024 2025)")
    parser.add_argument("--all", action="store_true", help="Test all available seasons (2024, 2025, 2026)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON report file path")
    parser.add_argument("--no-qualifying", action="store_true", help="Disable use of qualifying grid data (baseline test)")
    
    args = parser.parse_args()
    
    # Determine seasons to test
    if args.all:
        seasons = [2024, 2025, 2026]
    elif args.season:
        seasons = args.season
    else:
        seasons = [2024, 2025]  # Default: historical seasons
    
    # Determine output file
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"accuracy_report_{timestamp}.json"
    
    # Run verification
    use_qualifying = not args.no_qualifying
    start_time = datetime.now()
    
    try:
        report = verify_accuracy(seasons, output_file=args.output, use_qualifying_data=use_qualifying)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"\nVerification completed in {elapsed:.1f} seconds")
        
        # Exit code based on accuracy
        summary = report.get("summary", {})
        top3_acc = summary.get("top3_accuracy", {}).get("average_pct", 0)
        
        if top3_acc >= 80:
            logger.info("✅ SUCCESS: 80% accuracy target achieved!")
            sys.exit(0)
        elif top3_acc >= 70:
            logger.warning("⚠️  WARNING: Accuracy below 80% target but above 70% minimum")
            sys.exit(0)
        else:
            logger.error("❌ FAILURE: Accuracy below 70%. Model needs significant improvement.")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
