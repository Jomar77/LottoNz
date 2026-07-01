"""5-strategy prediction service wrapping prediction_engine.py in-memory."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from fastapi import HTTPException

from api.config import MIN_DRAWS_FOR_DATE_FILTER
from api.deps import get_data
from api.schemas import (
    LeanType,
    PredictionSetOut,
    SpreadType,
    StrategiesMetadata,
    StrategiesResponse,
)


def generate_strategies(
    lean: LeanType,
    spread: SpreadType,
    consecutive: bool,
    date_from: str | None,
    count: int,
    seed: int | None,
) -> StrategiesResponse:
    from src.core.prediction_engine import (
        format_output,
        generate_prediction_sets,
        generate_lean_set,
        to_dataframe,
    )

    df, _ = get_data()

    # Apply date filter if requested.
    if date_from is not None:
        try:
            cutoff = pd.Timestamp(date_from)
        except Exception:
            raise HTTPException(status_code=422, detail=f"date_from={date_from!r} is not a valid date (use YYYY-MM-DD).")
        df_filtered = df[df["date"] >= cutoff].reset_index(drop=True)
        if len(df_filtered) < MIN_DRAWS_FOR_DATE_FILTER:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"date_from={date_from!r} leaves only {len(df_filtered)} draws. "
                    f"Minimum is {MIN_DRAWS_FOR_DATE_FILTER}."
                ),
            )
        df = df_filtered

    # Use a fresh random seed (not fixed) when none supplied → guarantees
    # output differs from the static predictions.json which uses seed=None
    # with the scraper's own seeding.
    sets = generate_prediction_sets(df, num_sets=count, seed=seed)

    # Override lean_bias direction with caller's lean param (when not middle).
    if lean != LeanType.middle:
        lean_direction = lean.value  # "left" or "right"
        new_lean_main = generate_lean_set(df, lean_direction=lean_direction)
        for s in sets:
            if s["strategy"] == "lean_bias":
                s["main"] = new_lean_main
                break

    doc = format_output(sets=sets, df=df)

    out_sets = [
        PredictionSetOut(
            id=s["id"],
            strategy=s["strategy"],
            main_numbers=s["main_numbers"],
            powerball=s["powerball"],
            rationale=s["rationale"],
        )
        for s in doc["sets"]
    ]

    meta = doc["metadata"]
    applied: dict = {
        "date_from": date_from,
        "lean": lean.value,
        "spread": spread.value,
        "consecutive": consecutive,
    }

    return StrategiesResponse(
        draw_reference=doc["draw_reference"],
        generated_at=doc["generated_at"],
        sets=out_sets,
        metadata=StrategiesMetadata(
            total_draws_analyzed=meta["total_draws_analyzed"],
            date_range=meta["date_range"],
            uniformity_confirmed=meta["uniformity_confirmed"],
            chi_square_p_main=meta["chi_square_p_main"],
            chi_square_p_powerball=meta["chi_square_p_powerball"],
            applied_filters=applied,
        ),
    )
