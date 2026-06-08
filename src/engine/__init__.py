"""
F1 Prediction Engine - Core prediction modules.

Public API:
  - predict(): Run race predictions with Monte Carlo simulation
  - compute_all_drivers(): Compute features for all drivers
  - simulate_race(): Low-level race simulation
"""

from .predictor import predict, PredictionRequest, DriverPrediction
from .probability_model import simulate_race, apply_platt, get_field_size
from .feature_engineering import (

    compute_all_drivers,
    compute_composite_score,
    compute_elo_score,
    compute_constructor_strength,
    compute_recent_form_score,
    estimate_dnf_probability,
)

__all__ = [
    "predict",
    "PredictionRequest",
    "DriverPrediction",
    "simulate_race",
    "apply_platt",
    "get_field_size",
    "compute_all_drivers",
    "compute_composite_score",
    "compute_elo_score",
    "compute_constructor_strength",
    "compute_recent_form_score",
    "estimate_dnf_probability",
]
