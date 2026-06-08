"""
Configuration settings for the F1 Predictor model.

This module contains the feature weights and hyperparameters used by the 
feature engineering pipeline and probability model.

FEATURE_WEIGHTS: Weights for the composite driver performance score.
                 All keys must match the features dict in compute_composite_score().
                 Values must sum to approximately 1.0.
"""

# ── Feature Weights ────────────────────────────────────────────────────────────
# These weights determine the importance of each feature in the composite score.
# Sum: 0.25 + 0.20 + 0.20 + 0.10 + 0.10 + 0.05 + 0.05 + 0.05 = 1.00

FEATURE_WEIGHTS: dict[str, float] = {
    "elo_rating":           0.25,  # Driver skill (multi-dimensional ELO)
    "constructor_strength": 0.20,  # Car performance
    "recent_form":          0.20,  # Last N race results (exponentially weighted)
    "track_type_fit":       0.10,  # Driver-circuit type compatibility
    "reliability":          0.10,  # DNF rate (career + recent blend)
    "weather_adjustment":   0.05,  # Wet skill × rain probability
    "safety_car_upside":    0.05,  # Opportunity to gain positions
    "grid_position":        0.05,  # Starting position advantage
}


# ── Recency Parameters ─────────────────────────────────────────────────────────
# Used in compute_recent_form_score() for exponentially-weighted averaging

RECENCY_DECAY: float = 0.95
"""Decay factor for recent form weighting. Higher values give more weight to older results."""

RECENCY_WINDOW: int = 5
"""Number of most recent races to consider when computing recent form score."""


# ── Validation ─────────────────────────────────────────────────────────────────
# Ensure weights are properly configured at module load time

def _validate_weights():
    """Validate that FEATURE_WEIGHTS is properly configured."""
    total = sum(FEATURE_WEIGHTS.values())
    assert abs(total - 1.0) < 0.02, f"FEATURE_WEIGHTS sum to {total}, expected ~1.0"
    
    for name, weight in FEATURE_WEIGHTS.items():
        assert weight > 0, f"Feature weight '{name}' is not positive: {weight}"
    
    # Required keys from compute_composite_score()
    required_keys = {
        "elo_rating", "constructor_strength", "recent_form", "track_type_fit",
        "reliability", "weather_adjustment", "safety_car_upside", "grid_position"
    }
    actual_keys = set(FEATURE_WEIGHTS.keys())
    assert required_keys == actual_keys, (
        f"FEATURE_WEIGHTS key mismatch:\n"
        f"Required: {required_keys}\n"
        f"Actual: {actual_keys}\n"
        f"Missing: {required_keys - actual_keys}\n"
        f"Extra: {actual_keys - required_keys}"
    )


# Run validation on import
_validate_weights()
