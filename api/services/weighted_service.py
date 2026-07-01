"""Weighted-sampling ticket generator wrapping decay_generator.py."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from api.config import MAX_REJECTION_ATTEMPTS
from api.deps import get_data
from api.schemas import LeanType, SpreadType, Ticket, WeightedResponse


def _classify_lean(numbers: list[int]) -> str:
    left = sum(1 for n in numbers if n <= 20)
    if left >= 4:
        return "left"
    if left <= 2:
        return "right"
    return "middle"


def _check_lean(numbers: list[int], lean: LeanType) -> bool:
    left = sum(1 for n in numbers if n <= 20)
    if lean == LeanType.left:
        return left >= 4
    if lean == LeanType.right:
        return left <= 2
    return True  # middle: any balance accepted


def _check_spread(numbers: list[int], spread: SpreadType) -> bool:
    s = max(numbers) - min(numbers)
    if spread == SpreadType.tight:
        return s <= 20
    if spread == SpreadType.wide:
        return s >= 20
    return True


def _check_consecutive(numbers: list[int], want_consecutive: bool) -> bool:
    s = sorted(numbers)
    has = any(s[i + 1] - s[i] == 1 for i in range(len(s) - 1))
    return has if want_consecutive else not has


def generate_weighted(
    count: int,
    lean: LeanType,
    spread: SpreadType,
    consecutive: bool,
    mode: str,
    seed: int | None,
    half_life: float = 52.0,
) -> WeightedResponse:
    from src.core.decay_generator import (
        build_historical_sets,
        decay_draw,
        derive_lambdas_classic,
        derive_lambdas_temporal,
        is_historically_unique,
    )

    _, draws = get_data()
    df, _ = get_data()

    rng = np.random.default_rng(seed)

    if mode == "temporal":
        lam_main, lam_pb, *_ = derive_lambdas_temporal(draws, half_life)
    else:
        lam_main, lam_pb, *_ = derive_lambdas_classic(draws)

    hist = build_historical_sets(draws)

    tickets: list[Ticket] = []
    for _ in range(count):
        best: tuple[list[int], int] | None = None
        satisfied = False

        for attempt in range(MAX_REJECTION_ATTEMPTS):
            numbers, powerball = decay_draw(lam_main, lam_pb, rng)
            if not is_historically_unique(numbers, hist):
                continue
            if _check_lean(numbers, lean) and _check_spread(numbers, spread) and _check_consecutive(numbers, consecutive):
                best = (numbers, powerball)
                satisfied = True
                break
            if best is None:
                best = (numbers, powerball)

        assert best is not None
        nums, pb = best
        s = sorted(nums)
        tickets.append(
            Ticket(
                main_numbers=s,
                powerball=pb,
                spread=max(s) - min(s),
                lean=_classify_lean(s),
                has_consecutive=any(s[i + 1] - s[i] == 1 for i in range(len(s) - 1)),
                constraint_satisfied=satisfied,
            )
        )

    total = len(draws)
    sorted_draws = sorted(draws, key=lambda d: d["date"])

    return WeightedResponse(
        engine="weighted",
        mode=mode,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        params={
            "count": count,
            "lean": lean.value,
            "spread": spread.value,
            "consecutive": consecutive,
            "mode": mode,
            "seed": seed,
        },
        tickets=tickets,
        metadata={
            "total_draws_analyzed": total,
            "date_range": f"{sorted_draws[0]['date']} to {sorted_draws[-1]['date']}",
        },
    )
