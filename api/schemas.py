"""Pydantic request/response models for both endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared param enums (aligned with Frontend/src/types.ts)
# ---------------------------------------------------------------------------

class LeanType(str, Enum):
    left = "left"
    right = "right"
    middle = "middle"


class SpreadType(str, Enum):
    tight = "tight"
    wide = "wide"
    mixed = "mixed"


# ---------------------------------------------------------------------------
# /predict/weighted
# ---------------------------------------------------------------------------

class WeightedParams(BaseModel):
    count: int = Field(1, ge=1, le=20)
    lean: LeanType = LeanType.middle
    spread: SpreadType = SpreadType.mixed
    consecutive: bool = False
    mode: str = Field("classic", pattern="^(classic|temporal)$")
    seed: int | None = None


class Ticket(BaseModel):
    main_numbers: list[int] = Field(..., examples=[[3, 10, 18, 22, 31, 37]])
    powerball: int = Field(..., examples=[5])
    spread: int = Field(..., description="max − min of main numbers", examples=[34])
    lean: str = Field(..., description="left / right / middle classification of this ticket", examples=["left"])
    has_consecutive: bool = Field(..., examples=[False])
    constraint_satisfied: bool = Field(True, description="False if constraints couldn't be met in 200 attempts")


class WeightedResponse(BaseModel):
    engine: str = Field("weighted", examples=["weighted"])
    mode: str = Field(..., examples=["classic"])
    generated_at: str = Field(..., examples=["2026-06-30T12:00:00Z"])
    params: dict[str, Any] = Field(
        ...,
        examples=[{"count": 2, "lean": "left", "spread": "mixed", "consecutive": False, "mode": "classic", "seed": None}],
    )
    tickets: list[Ticket]
    metadata: dict[str, Any] = Field(
        ...,
        examples=[{"total_draws_analyzed": 1875, "date_range": "2001-02-17 to 2026-05-09"}],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "engine": "weighted",
                "mode": "classic",
                "generated_at": "2026-06-30T12:00:00Z",
                "params": {"count": 1, "lean": "middle", "spread": "mixed", "consecutive": False, "mode": "classic", "seed": None},
                "tickets": [
                    {"main_numbers": [3, 10, 18, 22, 31, 37], "powerball": 5, "spread": 34, "lean": "middle", "has_consecutive": False, "constraint_satisfied": True}
                ],
                "metadata": {"total_draws_analyzed": 1875, "date_range": "2001-02-17 to 2026-05-09"},
            }
        }
    }


# ---------------------------------------------------------------------------
# /predict/strategies
# ---------------------------------------------------------------------------

class StrategiesParams(BaseModel):
    lean: LeanType = LeanType.middle
    spread: SpreadType = SpreadType.mixed
    consecutive: bool = False
    date_from: str | None = None
    count: int = Field(5, ge=1, le=5)
    seed: int | None = None

    @field_validator("date_from")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date_from must be YYYY-MM-DD")
        return v


class PredictionSetOut(BaseModel):
    id: int = Field(..., examples=[1])
    strategy: str = Field(
        ...,
        examples=["burst_volatility"],
        description="One of: burst_volatility, mean_reversion, momentum_carry, balanced_hybrid, lean_bias",
    )
    main_numbers: list[int] = Field(..., examples=[[5, 6, 11, 20, 22, 28]])
    powerball: int = Field(..., examples=[2])
    rationale: str = Field(..., examples=["Numbers with high coefficient of variation across quarterly draws."])


class StrategiesMetadata(BaseModel):
    total_draws_analyzed: int = Field(..., examples=[1875])
    date_range: str = Field(..., examples=["2001-02-17 to 2026-05-09"])
    uniformity_confirmed: bool = Field(..., examples=[True])
    chi_square_p_main: float = Field(..., examples=[0.421])
    chi_square_p_powerball: float = Field(..., examples=[0.318])
    applied_filters: dict[str, Any] = Field(
        ...,
        examples=[{"date_from": None, "lean": "middle", "spread": "mixed", "consecutive": False}],
    )


class PredictionSetWeightedOut(PredictionSetOut):
    constraint_satisfied: bool = Field(
        ...,
        description="False if constraints could not be met within the 3-swap budget",
        examples=[True],
    )


class StrategiesWeightedResponse(BaseModel):
    draw_reference: int = Field(..., examples=[1876])
    generated_at: str = Field(..., examples=["2026-06-30T12:00:00Z"])
    sets: list[PredictionSetWeightedOut]
    metadata: StrategiesMetadata


class StrategiesResponse(BaseModel):
    draw_reference: int = Field(..., examples=[1876])
    generated_at: str = Field(..., examples=["2026-06-30T12:00:00Z"])
    sets: list[PredictionSetOut]
    metadata: StrategiesMetadata

    model_config = {
        "json_schema_extra": {
            "example": {
                "draw_reference": 1876,
                "generated_at": "2026-06-30T12:00:00Z",
                "sets": [
                    {"id": 1, "strategy": "burst_volatility", "main_numbers": [5, 6, 11, 20, 22, 28], "powerball": 2, "rationale": "Numbers with high CV across quarterly draws."},
                    {"id": 2, "strategy": "mean_reversion", "main_numbers": [1, 7, 13, 19, 33, 38], "powerball": 4, "rationale": "Numbers drawn below their long-run expected frequency."},
                    {"id": 3, "strategy": "momentum_carry", "main_numbers": [3, 9, 14, 21, 29, 35], "powerball": 7, "rationale": "Numbers recurring most often in the recent 30-draw window."},
                    {"id": 4, "strategy": "balanced_hybrid", "main_numbers": [2, 8, 17, 24, 31, 40], "powerball": 3, "rationale": "A balanced mix of frequently, rarely, and averagely drawn numbers."},
                    {"id": 5, "strategy": "lean_bias", "main_numbers": [4, 10, 12, 15, 18, 20], "powerball": 6, "rationale": "Numbers from the most-represented side of the range in the recent year."},
                ],
                "metadata": {
                    "total_draws_analyzed": 1875,
                    "date_range": "2001-02-17 to 2026-05-09",
                    "uniformity_confirmed": True,
                    "chi_square_p_main": 0.421,
                    "chi_square_p_powerball": 0.318,
                    "applied_filters": {"date_from": None, "lean": "middle", "spread": "mixed", "consecutive": False},
                },
            }
        }
    }
