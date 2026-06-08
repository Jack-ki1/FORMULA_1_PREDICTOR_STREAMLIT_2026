"""
Calibration state tracking for Platt calibration parameters.

Makes calibration status machine-readable so downstream code can warn users
when using placeholder parameters instead of fitted values.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
