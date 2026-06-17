"""
Accuracy Tracking Service — Monitor and Analyze Prediction Performance.

Tracks prediction accuracy over time by comparing predicted vs actual race results.
Provides metrics dashboard data and alerts when accuracy drops below thresholds.

Usage:
    from src.services.accuracy_service import AccuracyService
    
    service = AccuracyService()
    service.log_prediction(prediction_id, circuit_id, predictions)
    service.record_actual_results(prediction_id, actual_results)
    metrics = service.get_accuracy_metrics(days=30)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AccuracyService:
    """
    Track and analyze prediction accuracy over time.
    
    Monitors key metrics:
    - Top-3 accuracy (% of top-3 predicted drivers in actual top-3)
    - Winner prediction accuracy
    - Points finisher accuracy (top-10)
    - Mean absolute position error
    """
    
    def __init__(self, storage_path: str = "accuracy_tracking.json"):
        self.storage_path = Path(storage_path)
        self._load_history()
    
    def _load_history(self):
        """Load historical accuracy data from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    self.history = json.load(f)
                logger.info(f"Loaded {len(self.history)} accuracy records")
            except Exception as e:
                logger.warning(f"Failed to load accuracy history: {e}")
                self.history = []
        else:
            self.history = []
    
    def _save_history(self):
        """Save accuracy history to disk."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save accuracy history: {e}")
    
    def log_prediction(
        self,
        prediction_id: str,
        circuit_id: str,
        predictions: List[Dict],
        metadata: Optional[Dict] = None,
    ):
        """
        Log a prediction for later accuracy tracking.
        
        Args:
            prediction_id: Unique identifier for this prediction
            circuit_id: Circuit where prediction applies
            predictions: List of predicted outcomes with positions
            metadata: Additional context (rain prob, date, etc.)
        """
        record = {
            "prediction_id": prediction_id,
            "circuit_id": circuit_id,
            "predicted_at": datetime.now().isoformat(),
            "predictions": predictions,
            "metadata": metadata or {},
            "actual_results": None,
            "accuracy_metrics": None,
            "status": "pending",  # pending, evaluated, failed
        }
        
        self.history.append(record)
        self._save_history()
        logger.info(f"Logged prediction {prediction_id} for {circuit_id}")
    
    def record_actual_results(
        self,
        prediction_id: str,
        actual_results: List[Dict],
    ) -> Optional[Dict[str, Any]]:
        """
        Record actual race results and calculate accuracy metrics.
        
        Args:
            prediction_id: ID of prediction to evaluate
            actual_results: Actual race results with positions
        
        Returns:
            Calculated accuracy metrics, or None if prediction not found
        """
        # Find prediction record
        record = next((r for r in self.history if r["prediction_id"] == prediction_id), None)
        
        if not record:
            logger.warning(f"Prediction {prediction_id} not found")
            return None
        
        try:
            # Calculate accuracy metrics
            metrics = self._calculate_accuracy(record["predictions"], actual_results)
            
            # Update record
            record["actual_results"] = actual_results
            record["accuracy_metrics"] = metrics
            record["evaluated_at"] = datetime.now().isoformat()
            record["status"] = "evaluated"
            
            self._save_history()
            logger.info(f"Evaluated prediction {prediction_id}: Top-3 accuracy = {metrics['top3_accuracy_pct']:.1f}%")
            
            # Check if accuracy is below threshold
            self._check_accuracy_alert(metrics)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to evaluate prediction {prediction_id}: {e}")
            record["status"] = "failed"
            record["error"] = str(e)
            self._save_history()
            return None
    
    def _calculate_accuracy(
        self,
        predictions: List[Dict],
        actual_results: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate comprehensive accuracy metrics."""
        
        if not predictions or not actual_results:
            return {"error": "Missing data"}
        
        # Build lookup maps
        pred_by_driver = {p["driver_id"]: p for p in predictions}
        actual_by_driver = {r["driver"]: r for r in actual_results}
        
        # Sort by position
        sorted_preds = sorted(predictions, key=lambda x: x.get("expected_position_float", 999))
        sorted_actuals = sorted(actual_results, key=lambda x: x.get("position", 999))
        
        # Extract top-3 and top-10
        pred_top3 = [p["driver_id"] for p in sorted_preds[:3]]
        actual_top3 = [r["driver"] for r in sorted_actuals[:3]]
        
        pred_top10 = [p["driver_id"] for p in sorted_preds[:10]]
        actual_top10 = [r["driver"] for r in sorted_actuals[:10]]
        
        # Calculate metrics
        top3_correct = len(set(pred_top3) & set(actual_top3))
        points_correct = len(set(pred_top10) & set(actual_top10))
        
        # Position errors
        position_errors = []
        for driver_id in pred_by_driver:
            if driver_id in actual_by_driver:
                pred_pos = pred_by_driver[driver_id].get("expected_position_float", 999)
                actual_pos = actual_by_driver[driver_id].get("position", 999)
                position_errors.append(abs(pred_pos - actual_pos))
        
        metrics = {
            "top3_accuracy_pct": round(top3_correct / 3 * 100, 2),
            "top3_correct_count": top3_correct,
            "winner_in_pred_top3": sorted_actuals[0]["driver"] in pred_top3 if sorted_actuals else False,
            "points_accuracy_pct": round(points_correct / min(10, len(actual_top10)) * 100, 2) if actual_top10 else 0,
            "mean_absolute_error": round(sum(position_errors) / len(position_errors), 2) if position_errors else None,
            "median_absolute_error": round(sorted(position_errors)[len(position_errors)//2], 2) if position_errors else None,
            "evaluated_at": datetime.now().isoformat(),
        }
        
        return metrics
    
    def _check_accuracy_alert(self, metrics: Dict[str, Any]):
        """Check if accuracy metrics trigger alerts."""
        top3_acc = metrics.get("top3_accuracy_pct", 0)
        
        if top3_acc < 50:
            logger.warning(f"⚠️  CRITICAL: Top-3 accuracy {top3_acc:.1f}% is below 50% threshold!")
        elif top3_acc < 70:
            logger.warning(f"⚠️  WARNING: Top-3 accuracy {top3_acc:.1f}% is below 70% target")
    
    def get_accuracy_metrics(
        self,
        days: int = 30,
        circuit_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated accuracy metrics for recent predictions.
        
        Args:
            days: Number of days to look back
            circuit_id: Filter by specific circuit (optional)
        
        Returns:
            Aggregated accuracy statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter records
        filtered = [
            r for r in self.history
            if r["status"] == "evaluated"
            and r.get("evaluated_at")
            and datetime.fromisoformat(r["evaluated_at"]) >= cutoff_date
        ]
        
        if circuit_id:
            filtered = [r for r in filtered if r["circuit_id"] == circuit_id]
        
        if not filtered:
            return {
                "total_evaluations": 0,
                "period_days": days,
                "message": "No evaluated predictions in this period",
            }
        
        # Aggregate metrics
        top3_accuracies = [r["accuracy_metrics"]["top3_accuracy_pct"] for r in filtered if r.get("accuracy_metrics")]
        winner_predictions = [r["accuracy_metrics"]["winner_in_pred_top3"] for r in filtered if r.get("accuracy_metrics")]
        mean_errors = [r["accuracy_metrics"]["mean_absolute_error"] for r in filtered if r.get("accuracy_metrics") and r["accuracy_metrics"].get("mean_absolute_error")]
        
        summary = {
            "total_evaluations": len(filtered),
            "period_days": days,
            "circuit_filter": circuit_id,
            
            "top3_accuracy": {
                "average_pct": round(sum(top3_accuracies) / len(top3_accuracies), 2) if top3_accuracies else None,
                "min_pct": round(min(top3_accuracies), 2) if top3_accuracies else None,
                "max_pct": round(max(top3_accuracies), 2) if top3_accuracies else None,
                "target_80_pct": "✅ ACHIEVED" if (top3_accuracies and sum(top3_accuracies) / len(top3_accuracies) >= 80) else "❌ BELOW TARGET",
            },
            
            "winner_prediction": {
                "accuracy_pct": round(sum(winner_predictions) / len(winner_predictions) * 100, 2) if winner_predictions else None,
            },
            
            "position_error": {
                "mean_absolute_error": round(sum(mean_errors) / len(mean_errors), 2) if mean_errors else None,
            },
            
            "trend": self._calculate_trend(filtered),
        }
        
        return summary
    
    def _calculate_trend(self, records: List[Dict]) -> Dict[str, Any]:
        """Calculate accuracy trend over time."""
        if len(records) < 2:
            return {"direction": "insufficient_data", "change_pct": None}
        
        # Sort by evaluation date
        sorted_records = sorted(records, key=lambda r: r["evaluated_at"])
        
        # Compare first half vs second half
        mid = len(sorted_records) // 2
        first_half = sorted_records[:mid]
        second_half = sorted_records[mid:]
        
        avg_first = sum(r["accuracy_metrics"]["top3_accuracy_pct"] for r in first_half) / len(first_half)
        avg_second = sum(r["accuracy_metrics"]["top3_accuracy_pct"] for r in second_half) / len(second_half)
        
        change_pct = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
        
        return {
            "direction": "improving" if change_pct > 5 else ("declining" if change_pct < -5 else "stable"),
            "change_pct": round(change_pct, 2),
            "first_half_avg": round(avg_first, 2),
            "second_half_avg": round(avg_second, 2),
        }
    
    def export_report(self, output_path: str = "accuracy_report.json"):
        """Export full accuracy report to JSON file."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary_30_days": self.get_accuracy_metrics(days=30),
            "summary_90_days": self.get_accuracy_metrics(days=90),
            "all_evaluations": [r for r in self.history if r["status"] == "evaluated"],
        }
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Accuracy report exported to {output_path}")
        return report


# Singleton instance for easy import
_accuracy_service_instance = None


def get_accuracy_service() -> AccuracyService:
    """Get or create singleton AccuracyService instance."""
    global _accuracy_service_instance
    if _accuracy_service_instance is None:
        _accuracy_service_instance = AccuracyService()
    return _accuracy_service_instance
