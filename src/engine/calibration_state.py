"""
Calibration state tracking for Platt calibration and isotonic regression parameters.

Makes calibration status machine-readable so downstream code can warn users
when using placeholder parameters instead of fitted values.

FIX F-05: Added support for isotonic regression calibration points.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Tuple


@dataclass
class IsotonicCalibrationState:
    """
    Tracks isotonic regression calibration points.
    
    More flexible than Platt scaling - doesn't assume sigmoid shape.
    Trained on historical 2024-2025 race data.
    """
    outcome_type: str
    calibration_points: Optional[List[Tuple[float, float]]] = None
    is_fitted: bool = False
    fitted_at: Optional[datetime] = None
    training_races: int = 0
    brier_score_improvement: Optional[float] = None
    
    def calibrate(self, raw_prob: float) -> float:
        """Apply isotonic calibration if available."""
        if not self.is_fitted or not self.calibration_points:
            return raw_prob
        
        # Linear interpolation between calibration points
        for i in range(len(self.calibration_points) - 1):
            x0, y0 = self.calibration_points[i]
            x1, y1 = self.calibration_points[i + 1]
            
            if x0 <= raw_prob <= x1:
                if x1 == x0:
                    return y0
                t = (raw_prob - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
        
        # Edge cases
        if raw_prob < self.calibration_points[0][0]:
            return self.calibration_points[0][1]
        return self.calibration_points[-1][1]


@dataclass
class PlattCalibrationState:
    """
    Tracks whether Platt calibration parameters are fitted or placeholder.
    
    Placeholder parameters (is_fitted=False) mean raw simulation probabilities
    are used with minimal transformation. Fitted parameters require at least
    12 completed races for reliable estimation.
    """
    outcome_type: str
    A: float
    B: float
    is_fitted: bool
    fitted_at: Optional[datetime] = None
    training_races: int = 0
    brier_score_improvement: Optional[float] = None

    def warn_if_placeholder(self) -> None:
        if not self.is_fitted:
            import warnings
            warnings.warn(
                f"Platt calibration for '{self.outcome_type}' is using placeholder "
                f"parameters (A={self.A}, B={self.B}). Run `python main.py recalibrate "
                f"--fit-platt` after 12+ races to fit proper parameters. "
                f"Current predictions rely on raw simulation probabilities.",
                UserWarning,
                stacklevel=3,
            )


# FIX F-05: Initialize isotonic calibration states (to be fitted on 2024-2025 data)
ISOTONIC_CALIBRATION = {
    "win": IsotonicCalibrationState(outcome_type="win"),
    "top3": IsotonicCalibrationState(outcome_type="top3"),
    "top10": IsotonicCalibrationState(outcome_type="top10"),
    "dnf": IsotonicCalibrationState(outcome_type="dnf"),
}

PLATT_CALIBRATION = {
    "win": PlattCalibrationState(
        outcome_type="win",
        A=1.05, B=-0.02,
        is_fitted=False,
        training_races=0,
    ),
    "top3": PlattCalibrationState(
        outcome_type="top3",
        A=1.03, B=-0.01,
        is_fitted=False,
        training_races=0,
    ),
    "top10": PlattCalibrationState(
        outcome_type="top10",
        A=1.02, B=0.00,
        is_fitted=False,
        training_races=0,
    ),
    "dnf": PlattCalibrationState(
        outcome_type="dnf",
        A=1.00, B=0.00,
        is_fitted=False,
        training_races=0,
    ),
}
