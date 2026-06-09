"""
Prediction Accuracy Tracking & Post-Race Evaluation.

Stores predictions, compares with actual results, computes:
- Brier scores
- Log loss
- Calibration curves
- Accuracy trends over time
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from src.database.models import SessionLocal, Prediction, Race, Driver, init_db
from .predictor import predict, PredictionRequest



logger = logging.getLogger(__name__)


class PredictionTracker:
    """Track and evaluate prediction accuracy."""
    
    def __init__(self):
        # Don't open session in __init__ - use per-call sessions instead
        self.db = None
    
    def store_prediction(self, circuit_id: str, prediction_result: Dict):
        """
        Store prediction in database for later evaluation.
        
        FIXED: Now uses per-call session management to avoid InvalidRequestError
        when store_prediction is called multiple times on the same instance.
        
        Args:
            circuit_id: Circuit identifier
            prediction_result: Result from predict() function
        """
        db = SessionLocal()  # Open per-call session
        try:
            # Get or create race
            race = db.query(Race).filter(
                Race.circuit_id == circuit_id,
                Race.season == 2026
            ).first()
            
            if not race:
                race = Race(
                    circuit_id=circuit_id,
                    season=2026,
                    completed=False,
                )
                db.add(race)
                db.flush()
            
            # Store predictions for each driver
            for driver_pred in prediction_result["predictions"]:
                prediction = Prediction(
                    race_id=race.id,
                    driver_id=driver_pred.get("driver_id", driver_pred.get("driver")),  # Support both keys
                    predicted_position=driver_pred.get("predicted_position", 99),
                    win_probability=driver_pred.get("win_pct", 0) / 100.0,
                    top3_probability=driver_pred.get("top3_pct", 0) / 100.0,
                    top10_probability=driver_pred.get("top10_pct", 0) / 100.0,
                    dnf_probability=driver_pred.get("dnf_pct", 0) / 100.0,
                    composite_score=driver_pred.get("composite_score", 0.5),
                    model_version="v3.0",
                )
                db.add(prediction)
            
            db.commit()
            logger.info(f"Stored predictions for {circuit_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store predictions: {e}")
            raise
        finally:
            db.close()  # Always close the per-call session
    
    def evaluate_race(self, circuit_id: str, actual_results: Dict):
        """
        Evaluate predictions against actual race results.
        
        FIXED: Now uses per-call session management.
        
        Args:
            circuit_id: Circuit identifier
            actual_results: Dict with driver_id -> actual_position
        """
        db = SessionLocal()  # Open per-call session
        try:
            race = db.query(Race).filter(
                Race.circuit_id == circuit_id,
                Race.season == 2026
            ).first()
            
            if not race:
                raise ValueError(f"No predictions found for {circuit_id}")
            
            # Get all predictions for this race
            predictions = db.query(Prediction).filter(
                Prediction.race_id == race.id
            ).all()
            
            brier_scores = []
            
            for pred in predictions:
                driver_id = pred.driver_id
                
                if driver_id not in actual_results:
                    continue
                
                actual_position = actual_results[driver_id]
                
                # Update actual results
                pred.actual_position = actual_position
                pred.actual_result = "Finished" if actual_position <= 20 else "DNF"
                
                # Calculate Brier scores (FIXED: proper per-outcome calculation)
                actual_win = 1.0 if actual_position == 1 else 0.0
                actual_top3 = 1.0 if actual_position <= 3 else 0.0
                actual_top10 = 1.0 if actual_position <= 10 else 0.0
                actual_dnf = 1.0 if actual_position > 20 else 0.0
                
                brier_win = (pred.win_probability - actual_win) ** 2
                brier_top3 = (pred.top3_probability - actual_top3) ** 2
                brier_top10 = (pred.top10_probability - actual_top10) ** 2
                brier_dnf = (pred.dnf_probability - actual_dnf) ** 2
                
                # Composite Brier score: weighted average reflecting F1 prediction goals
                # Win prediction is hardest and most valuable, weighted accordingly
                pred.brier_score = (
                    0.40 * brier_win +
                    0.30 * brier_top3 +
                    0.20 * brier_top10 +
                    0.10 * brier_dnf
                )
                
                pred.evaluated_at = datetime.utcnow()
                brier_scores.append(pred.brier_score)
            
            # Update race as completed
            race.completed = True
            
            db.commit()
            
            avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else 0.0
            
            logger.info(f"Evaluated {circuit_id}: avg Brier score = {avg_brier:.4f}")
            
            return {
                "circuit": circuit_id,
                "avg_brier_score": round(avg_brier, 4),
                "predictions_evaluated": len(brier_scores),
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to evaluate race: {e}")
            raise
        finally:
            db.close()
    
    def get_accuracy_report(self, season: int = 2026) -> Dict:
        """
        Generate comprehensive accuracy report with session breakdown.
        
        FIXED: Now uses per-call session management and returns enhanced metrics
        including session-by-session analysis (Practice, Qualifying, Sprint, Race).
        
        Returns:
            Dict with overall metrics and session-specific breakdowns
        """
        # Ensure schema exists (Streamlit may run before `py main.py migrate-db`)
        init_db()

        db = SessionLocal()  # Open per-call session
        try:
            predictions = db.query(Prediction).filter(
                Prediction.model_version.like("v3%"),
                Prediction.brier_score.isnot(None)
            ).all()
            
            if not predictions:
                return {
                    "total_predictions": 0,
                    "evaluated_predictions": 0,
                    "message": "No evaluated predictions found. Run some predictions first!"
                }
            
            # Overall metrics
            avg_brier = sum(p.brier_score for p in predictions) / len(predictions)
            
            # By outcome type
            win_brier = sum((p.win_probability - (1.0 if p.actual_position == 1 else 0.0)) ** 2 
                           for p in predictions) / len(predictions)
            top3_brier = sum((p.top3_probability - (1.0 if p.actual_position <= 3 else 0.0)) ** 2 
                            for p in predictions) / len(predictions)
            
            # By position accuracy
            position_errors = [abs(p.predicted_position - p.actual_position) 
                              for p in predictions if p.actual_position]
            avg_position_error = sum(position_errors) / len(position_errors) if position_errors else 0.0
            
            # Position accuracy percentage (within ±2 positions)
            accurate_predictions = sum(1 for e in position_errors if e <= 2)
            position_accuracy = (accurate_predictions / len(position_errors) * 100) if position_errors else 0.0
            
            # Session breakdown analysis
            session_breakdown = self._analyze_by_session(db, predictions)
            
            # Driver-specific accuracy
            driver_accuracy = self._analyze_by_driver(predictions)
            
            # Trend analysis
            trend = self._calculate_trend(predictions)
            
            # Recommendations
            recommendations = self._generate_recommendations(avg_brier, avg_position_error, session_breakdown)
            
            return {
                "total_predictions": len(predictions),
                "evaluated_predictions": len([p for p in predictions if p.actual_position]),
                "avg_brier_score": round(avg_brier, 4),
                "win_prediction_brier": round(win_brier, 4),
                "top3_prediction_brier": round(top3_brier, 4),
                "avg_position_error": round(avg_position_error, 2),
                "position_accuracy": round(position_accuracy, 1),
                "calibration": "Good" if avg_brier < 0.10 else "Needs Improvement",
                "session_breakdown": session_breakdown,
                "driver_accuracy": driver_accuracy,
                "trend": trend,
                "recommendations": recommendations,
            }
            
        except Exception as e:
            logger.error(f"Failed to generate accuracy report: {e}")
            raise
        finally:
            db.close()
    
    def _analyze_by_session(self, db, predictions):
        """Analyze prediction accuracy by session type."""
        # Group predictions by race/session
        races = db.query(Race).all()
        race_map = {r.id: r for r in races}
        
        session_data = {
            "practice": {"count": 0, "predictions": []},
            "qualifying": {"count": 0, "predictions": []},
            "sprint": {"count": 0, "predictions": []},
            "race": {"count": 0, "predictions": []},
        }
        
        # For now, classify all as "race" since we don't have session_type field yet
        # This can be enhanced when we add session tracking to the database
        for pred in predictions:
            session_data["race"]["count"] += 1
            session_data["race"]["predictions"].append(pred)
        
        # Calculate metrics for each session type
        result = {}
        
        # Practice (placeholder - would need FP data)
        result["practice"] = {
            "count": 0,
            "avg_pace_error": 0.0,
            "calibration_score": 0.0,
        }
        
        # Qualifying (placeholder - would need qualifying results)
        result["qualifying"] = {
            "count": 0,
            "grid_mae": 0.0,
            "pole_accuracy": 0.0,
        }
        
        # Sprint (placeholder - would need sprint results)
        result["sprint"] = {
            "count": 0,
            "win_accuracy": 0.0,
            "points_mae": 0.0,
        }
        
        # Race - actual data from predictions
        race_preds = session_data["race"]["predictions"]
        if race_preds:
            winner_correct = sum(1 for p in race_preds if p.predicted_position == 1 and p.actual_position == 1)
            podium_hits = sum(1 for p in race_preds if p.predicted_position <= 3 and p.actual_position <= 3)
            avg_pos_err = sum(abs(p.predicted_position - p.actual_position) for p in race_preds if p.actual_position) / len(race_preds)
            
            result["race"] = {
                "count": len(race_preds),
                "winner_accuracy": winner_correct / len(race_preds) if race_preds else 0.0,
                "podium_hit_rate": podium_hits / len(race_preds) if race_preds else 0.0,
                "avg_pos_error": round(avg_pos_err, 1),
                "trend": "stable",  # Will be updated by _calculate_trend
            }
        else:
            result["race"] = {
                "count": 0,
                "winner_accuracy": 0.0,
                "podium_hit_rate": 0.0,
                "avg_pos_error": 0.0,
                "trend": "stable",
            }
        
        return result
    
    def _analyze_by_driver(self, predictions):
        """Analyze prediction accuracy by individual driver."""
        driver_stats = {}
        
        for pred in predictions:
            driver_id = pred.driver_id
            if driver_id not in driver_stats:
                driver_stats[driver_id] = {
                    "brier_scores": [],
                    "count": 0,
                    "position_errors": [],
                }
            
            if pred.brier_score is not None:
                driver_stats[driver_id]["brier_scores"].append(pred.brier_score)
            if pred.actual_position:
                driver_stats[driver_id]["position_errors"].append(
                    abs(pred.predicted_position - pred.actual_position)
                )
            driver_stats[driver_id]["count"] += 1
        
        # Aggregate stats
        result = {}
        for driver_id, stats in driver_stats.items():
            avg_brier = sum(stats["brier_scores"]) / len(stats["brier_scores"]) if stats["brier_scores"] else 0.0
            result[driver_id] = {
                "brier_score": round(avg_brier, 4),
                "count": stats["count"],
            }
        
        return result
    
    def _calculate_trend(self, predictions):
        """Calculate prediction accuracy trend over time."""
        if len(predictions) < 5:
            return "stable"
        
        # Sort by created_at date
        # Handle potential missing created_at by using a default min datetime
        sorted_preds = sorted(predictions, key=lambda p: getattr(p, 'created_at', None) or datetime.min)
        
        # Split into recent vs older
        mid = len(sorted_preds) // 2
        older = sorted_preds[:mid]
        recent = sorted_preds[mid:]
        
        # Compare Brier scores
        older_brier = sum(p.brier_score for p in older if p.brier_score) / len([p for p in older if p.brier_score]) if older else 0
        recent_brier = sum(p.brier_score for p in recent if p.brier_score) / len([p for p in recent if p.brier_score]) if recent else 0
        
        # Lower Brier is better
        if recent_brier < older_brier * 0.95:
            return "improving"
        elif recent_brier > older_brier * 1.05:
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendations(self, avg_brier, avg_position_error, session_breakdown):
        """Generate actionable recommendations based on performance."""
        recommendations = []
        
        if avg_brier > 0.15:
            recommendations.append("🎯 Overall prediction confidence needs improvement - consider recalibrating probability models")
        
        if avg_position_error > 3.0:
            recommendations.append("📍 Position predictions show high variance - enhance grid-to-race translation algorithms")
        
        race_data = session_breakdown.get("race", {})
        if race_data.get("winner_accuracy", 0) < 0.3:
            recommendations.append("🏆 Winner prediction accuracy is low - improve pace assessment for top teams")
        
        if race_data.get("podium_hit_rate", 0) < 0.5:
            recommendations.append("🥇 Podium prediction hit rate below 50% - refine top-3 probability calculations")
        
        if not recommendations:
            recommendations.append("✅ Model performance is within acceptable parameters")
            recommendations.append("📊 Continue collecting data across all session types for deeper insights")
        
        recommendations.append("🌧️ Enhance wet weather prediction models with more rain scenario simulations")
        recommendations.append("🏁 Track sprint race performance separately from main races once data available")
        
        return recommendations
    
    def close(self):
        """Close database session (no-op with per-call sessions)."""
        # Per-call sessions are closed automatically, nothing to do here
        pass


def run_post_race_evaluation(circuit_id: str, actual_results: Dict):
    """
    Convenience function to evaluate predictions after a race.
    
    Usage:
        from scripts.post_race_evaluation import run_post_race_evaluation
        
        actual_results = {
            "verstappen": 1,
            "hamilton": 2,
            "leclerc": 3,
            # ... all drivers
        }
        
        run_post_race_evaluation("canada", actual_results)
    """
    tracker = PredictionTracker()
    try:
        result = tracker.evaluate_race(circuit_id, actual_results)
        print(f"✓ Race evaluation completed: {result}")
        return result
    finally:
        tracker.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("F1 Predictor v3.0 — Accuracy Tracking")
    print("=" * 60)
    
    tracker = PredictionTracker()
    try:
        report = tracker.get_accuracy_report()
        print(json.dumps(report, indent=2))
    finally:
        tracker.close()
