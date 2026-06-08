"""
Schema validation for race results using Pydantic.

Provides structured validation of season data to catch errors early
and prevent silent corruption from propagating through the prediction pipeline.
"""
from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional


POINTS_TABLE = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}


class RaceResultEntry(BaseModel):
    """Single driver result in a race."""
    driver: str
    position: int
    points: float
    status: str = "Finished"

    @field_validator("position")
    @classmethod
    def position_must_be_positive(cls, v):
        if v < 1 or v > 22:
            raise ValueError(f"Position {v} out of valid range [1, 22]")
        return v

    @field_validator("points")
    @classmethod
    def points_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError(f"Points cannot be negative: {v}")
        return v


class RaceResult(BaseModel):
    """Complete race result with all drivers."""
    round: int
    circuit: str
    name: str
    date: str
    sprint: bool = False
    results: List[RaceResultEntry]

    @model_validator(mode="after")
    def validate_positions_unique(self) -> "RaceResult":
        positions = [r.position for r in self.results]
        if len(positions) != len(set(positions)):
            dupes = [p for p in positions if positions.count(p) > 1]
            raise ValueError(f"Duplicate positions in race results: {set(dupes)}")
        return self

    @model_validator(mode="after")
    def validate_points_consistent(self) -> "RaceResult":
        pts_table = POINTS_TABLE  # Sprint would use SPRINT_POINTS
        for entry in self.results:
            expected = pts_table.get(entry.position, 0)
            # Allow +1 for fastest lap bonus
            if entry.points not in (expected, expected + 1):
                raise ValueError(
                    f"P{entry.position} {entry.driver}: "
                    f"points={entry.points}, expected {expected} or {expected+1}"
                )
        return self


def validate_season_results(results: list) -> List[RaceResult]:
    """
    Validate all season results on import, failing fast on data errors.
    
    Args:
        results: List of raw race result dictionaries
    
    Returns:
        List of validated RaceResult objects
    
    Raises:
        ValueError: If any race result fails validation
    """
    validated = []
    errors = []
    for raw in results:
        try:
            validated.append(RaceResult(**raw))
        except Exception as e:
            errors.append(f"Round {raw.get('round', '?')}: {e}")
    
    if errors:
        error_str = "\n".join(errors)
        raise ValueError(f"Season data validation failed:\n{error_str}")
    
    return validated
