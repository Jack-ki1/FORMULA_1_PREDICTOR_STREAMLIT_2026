"""
Input validation for prediction requests.

Provides structured validation of all user inputs before they reach
the prediction engine, preventing invalid data from causing silent failures.
"""
from dataclasses import dataclass
from typing import Optional
from data.circuit_data import CIRCUITS


class ValidationError(ValueError):
    """Raised when request parameters fail validation."""
    pass


@dataclass
class ValidatedPredictionRequest:
    circuit_id: str
    rain_probability: Optional[float]
    n_simulations: int
    seed: Optional[int]

    @classmethod
    def from_dict(cls, data: dict) -> "ValidatedPredictionRequest":
        """
        Validate and normalize prediction request parameters.
        
        Args:
            data: Raw request dictionary (e.g., from Flask request.json)
        
        Returns:
            ValidatedPredictionRequest with normalized values
        
        Raises:
            ValidationError: If any parameter fails validation
        """
        # Validate circuit_id
        circuit_id = data.get("circuit_id", "").strip().lower()
        if not circuit_id:
            raise ValidationError("circuit_id is required")
        if circuit_id not in CIRCUITS:
            known = sorted(CIRCUITS.keys())
            raise ValidationError(
                f"Unknown circuit '{circuit_id}'. "
                f"Valid circuits: {', '.join(known)}"
            )

        # Validate rain_probability
        rain = data.get("rain_probability")
        if rain is not None:
            try:
                rain = float(rain)
            except (TypeError, ValueError):
                raise ValidationError("rain_probability must be a number")
            if not (0.0 <= rain <= 1.0):
                raise ValidationError("rain_probability must be between 0.0 and 1.0")

        # Validate n_simulations
        raw_sims = data.get("n_simulations", 5000)
        try:
            n_sims = int(raw_sims)
        except (TypeError, ValueError):
            raise ValidationError("n_simulations must be an integer")
        if n_sims < 100:
            raise ValidationError("n_simulations must be at least 100")
        if n_sims > 50000:
            raise ValidationError("n_simulations cannot exceed 50,000")

        # Validate seed
        seed = data.get("seed")
        if seed is not None:
            try:
                seed = int(seed)
            except (TypeError, ValueError):
                raise ValidationError("seed must be an integer")

        return cls(
            circuit_id=circuit_id,
            rain_probability=rain,
            n_simulations=n_sims,
            seed=seed,
        )
