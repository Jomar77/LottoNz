"""5-strategy prediction service with enforced lean/spread/consecutive constraints.

Extends strategies_service.py by applying a deterministic minimal-swap repair to each
strategy set, per the mathematician's recommendation (lean → spread → consecutive,
budget = 3 swaps). Sets that cannot satisfy all constraints within budget are returned
with constraint_satisfied=False (best-effort, mirrors /predict/weighted behaviour).
"""

from __future__ import annotations

import pandas as pd
from fastapi import HTTPException

from api.config import MIN_DRAWS_FOR_DATE_FILTER
from api.deps import get_data
from api.schemas import (
    LeanType,
    PredictionSetWeightedOut,
    SpreadType,
    StrategiesMetadata,
    StrategiesWeightedResponse,
)

# ---------------------------------------------------------------------------
# Constraint checkers (match weighted_service.py semantics exactly)
# ---------------------------------------------------------------------------

def _is_lean_ok(numbers: list[int], lean: LeanType) -> bool:
    left = sum(1 for n in numbers if n <= 20)
    if lean == LeanType.left:
        return left >= 4
    if lean == LeanType.right:
        return left <= 2
    return True


def _is_spread_ok(numbers: list[int], spread: SpreadType) -> bool:
    span = max(numbers) - min(numbers)
    if spread == SpreadType.tight:
        return span <= 20
    if spread == SpreadType.wide:
        return span >= 20
    return True


def _is_consecutive_ok(numbers: list[int], want_consecutive: bool) -> bool:
    s = sorted(numbers)
    has = any(s[i + 1] - s[i] == 1 for i in range(len(s) - 1))
    return has if want_consecutive else not has


# ---------------------------------------------------------------------------
# Per-constraint repair passes
# ---------------------------------------------------------------------------

def _repair_lean(
    result: list[int],
    lean: LeanType,
    scores: dict[int, float],
    budget: int,
) -> tuple[list[int], int]:
    if lean == LeanType.middle or _is_lean_ok(result, lean):
        return result, 0

    is_target = (lambda n: n > 20) if lean == LeanType.right else (lambda n: n <= 20)
    target_count = sum(1 for n in result if is_target(n))
    deficit = 4 - target_count  # need ≥4 on target side

    if deficit <= 0:
        return result, 0

    result = list(result)
    pool = set(range(1, 41)) - set(result)

    # Evict weakest wrong-side members; insert strongest target-side candidates.
    wrong = sorted([n for n in result if not is_target(n)], key=lambda n: scores.get(n, 0.0))
    cands = sorted([n for n in pool if is_target(n)], key=lambda n: -scores.get(n, 0.0))

    swaps = 0
    for i in range(min(deficit, len(wrong), len(cands), budget)):
        result.remove(wrong[i])
        result.append(cands[i])
        swaps += 1

    return result, swaps


def _repair_spread(
    result: list[int],
    spread: SpreadType,
    scores: dict[int, float],
    budget: int,
) -> tuple[list[int], int]:
    if spread == SpreadType.mixed or _is_spread_ok(result, spread):
        return result, 0

    result = list(result)
    swaps = 0

    if spread == SpreadType.wide:
        # Extend the range: evict a mid-range number and insert a more extreme one.
        while not _is_spread_ok(result, spread) and swaps < budget:
            pool = sorted(set(range(1, 41)) - set(result))
            low_ext = [n for n in pool if n < min(result)]
            high_ext = [n for n in pool if n > max(result)]

            if not low_ext and not high_ext:
                break  # can't extend further

            # Evict the non-extreme number with the lowest strategy score.
            s = sorted(result)
            mid_members = s[1:-1]  # exclude current min/max; they anchor the span
            evict = min(mid_members if mid_members else s, key=lambda n: scores.get(n, 0.0))

            # Insert the candidate that maximises span gain.
            best_low = low_ext[0] if low_ext else None   # most extreme low
            best_high = high_ext[-1] if high_ext else None  # most extreme high

            if best_low is not None and best_high is not None:
                gain_low = min(result) - best_low
                gain_high = best_high - max(result)
                new_n = best_low if gain_low >= gain_high else best_high
            else:
                new_n = best_low if best_low is not None else best_high  # type: ignore[assignment]

            result.remove(evict)
            result.append(new_n)
            swaps += 1

    elif spread == SpreadType.tight:
        # Slide all numbers into the best 20-unit window.
        while not _is_spread_ok(result, spread) and swaps < budget:
            pool = set(range(1, 41)) - set(result)

            # Find the [lo, lo+20] window that retains the most current members.
            best_lo, best_kept = 1, 0
            for lo in range(1, 22):  # lo+20 ≤ 41 → lo ≤ 21
                hi = lo + 20
                kept = sum(1 for n in result if lo <= n <= hi)
                if kept > best_kept:
                    best_kept, best_lo = kept, lo

            lo, hi = best_lo, best_lo + 20
            outside = sorted(
                [n for n in result if not (lo <= n <= hi)],
                key=lambda n: scores.get(n, 0.0),
            )
            inside_cands = sorted(
                [n for n in pool if lo <= n <= hi],
                key=lambda n: -scores.get(n, 0.0),
            )

            if not outside or not inside_cands:
                break

            result.remove(outside[0])
            result.append(inside_cands[0])
            swaps += 1

    return result, swaps


def _repair_consecutive(
    result: list[int],
    want_consecutive: bool,
    scores: dict[int, float],
    budget: int,
) -> tuple[list[int], int]:
    if budget <= 0 or _is_consecutive_ok(result, want_consecutive):
        return result, 0

    result = list(result)
    pool = set(range(1, 41)) - set(result)

    if want_consecutive:
        # Add a neighbour of an existing member (1 swap).
        for n in sorted(result):
            for neighbor in [n - 1, n + 1]:
                if 1 <= neighbor <= 40 and neighbor in pool:
                    weakest = min((x for x in result if x != n), key=lambda x: scores.get(x, 0.0))
                    result.remove(weakest)
                    result.append(neighbor)
                    return result, 1
        return result, 0  # no neighbour available

    else:
        # Break all consecutive pairs (up to budget swaps).
        swaps = 0
        s = sorted(result)
        for i in range(len(s) - 1):
            if swaps >= budget:
                break
            if s[i + 1] - s[i] == 1:
                forbidden = {s[i] - 1, s[i], s[i] + 1, s[i + 1] - 1, s[i + 1], s[i + 1] + 1}
                cands = sorted(
                    [n for n in pool if n not in forbidden],
                    key=lambda n: -scores.get(n, 0.0),
                )
                if cands:
                    result.remove(s[i + 1])
                    result.append(cands[0])
                    pool = set(range(1, 41)) - set(result)
                    swaps += 1
                    s = sorted(result)

        return result, swaps


# ---------------------------------------------------------------------------
# Top-level constraint application
# ---------------------------------------------------------------------------

def _apply_constraints(
    numbers: list[int],
    lean: LeanType,
    spread: SpreadType,
    want_consecutive: bool,
    scores: dict[int, float],
    max_swaps: int = 3,
) -> tuple[list[int], bool]:
    """Apply lean → spread → consecutive repair within a swap budget.

    Returns (repaired_sorted_list, all_constraints_satisfied).
    """
    result, used = _repair_lean(numbers, lean, scores, max_swaps)
    result, n = _repair_spread(result, spread, scores, max_swaps - used)
    used += n
    result, _ = _repair_consecutive(result, want_consecutive, scores, max_swaps - used)

    satisfied = (
        _is_lean_ok(result, lean)
        and _is_spread_ok(result, spread)
        and _is_consecutive_ok(result, want_consecutive)
    )
    return sorted(result), satisfied


# ---------------------------------------------------------------------------
# Public service entry point
# ---------------------------------------------------------------------------

def generate_strategies_weighted(
    lean: LeanType,
    spread: SpreadType,
    consecutive: bool,
    date_from: str | None,
    count: int,
    seed: int | None,
) -> StrategiesWeightedResponse:
    from src.core.prediction_engine import (
        calculate_frequencies,
        format_output,
        generate_lean_set,
        generate_prediction_sets,
    )

    df, _ = get_data()

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

    sets = generate_prediction_sets(df, num_sets=count, seed=seed)

    if lean != LeanType.middle:
        new_lean_main = generate_lean_set(df, lean_direction=lean.value)
        for s in sets:
            if s["strategy"] == "lean_bias":
                s["main"] = new_lean_main
                break

    # Overall historical frequency used as per-number importance score.
    scores: dict[int, float] = {k: float(v) for k, v in calculate_frequencies(df).items()}

    constrained: list[dict] = []
    for s in sets:
        repaired, satisfied = _apply_constraints(
            numbers=s["main"],
            lean=lean,
            spread=spread,
            want_consecutive=consecutive,
            scores=scores,
        )
        constrained.append({**s, "main": repaired, "constraint_satisfied": satisfied})

    doc = format_output(sets=constrained, df=df)

    out_sets = [
        PredictionSetWeightedOut(
            id=doc_s["id"],
            strategy=doc_s["strategy"],
            main_numbers=doc_s["main_numbers"],
            powerball=doc_s["powerball"],
            rationale=doc_s["rationale"],
            constraint_satisfied=constrained[i]["constraint_satisfied"],
        )
        for i, doc_s in enumerate(doc["sets"])
    ]

    meta = doc["metadata"]
    applied: dict = {
        "date_from": date_from,
        "lean": lean.value,
        "spread": spread.value,
        "consecutive": consecutive,
        "enforcement": "active",
    }

    from datetime import datetime, timezone
    return StrategiesWeightedResponse(
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
