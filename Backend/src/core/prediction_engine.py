"""5-strategy NZ Lotto prediction engine (Phase B).

Reads historical draws from ``frontend/public/results.json`` and produces a
static ``frontend/public/predictions.json`` containing five strategically
distinct number sets. See ``backend/docs/predictions_contract.md`` for the
output contract and ``new-algo.md`` for the analytical framework.

> NZ Lotto draws are independent, uniform-random events. The "strategies" here
> surface historical patterns for entertainment/education only — they carry no
> predictive edge over a random pick.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Paths (mirror decay_generator.py)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DATA_PATH = REPO_ROOT / "frontend" / "public" / "results.json"
OUTPUT_PATH = REPO_ROOT / "frontend" / "public" / "predictions.json"

MAIN_MIN, MAIN_MAX = 1, 40
POWERBALL_MIN, POWERBALL_MAX = 1, 10
NUMBERS_PER_DRAW = 6


# ---------------------------------------------------------------------------
# B1 — Data loading + ascending DataFrame normalization
# ---------------------------------------------------------------------------
def load_draws(path: Path | str = DATA_PATH) -> list[dict]:
    """Load raw draw dicts from a results.json file (most-recent-first on disk)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def to_dataframe(draws: list[dict]) -> pd.DataFrame:
    """Normalize raw draws into a DataFrame sorted oldest -> newest.

    Columns:
      - ``date``: ``pd.Timestamp``
      - ``numbers``: list[int] of the 6 main numbers
      - ``powerball``: int
    """
    df = pd.DataFrame(draws)
    df["date"] = pd.to_datetime(df["date"])
    df["numbers"] = df["numbers"].apply(lambda nums: [int(n) for n in nums])
    df["powerball"] = df["powerball"].astype(int)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def _as_dataframe(draws_or_df) -> pd.DataFrame:
    if isinstance(draws_or_df, pd.DataFrame):
        return draws_or_df
    return to_dataframe(draws_or_df)


# ---------------------------------------------------------------------------
# B2 — Frequency distributions (overall, quarterly, yearly)
# ---------------------------------------------------------------------------
def calculate_frequencies(draws_or_df) -> dict[int, int]:
    """Overall count per main number, zero-filled for all of 1..40."""
    df = _as_dataframe(draws_or_df)
    freqs = {n: 0 for n in range(MAIN_MIN, MAIN_MAX + 1)}
    for nums in df["numbers"]:
        for n in nums:
            freqs[int(n)] += 1
    return freqs


def _bucketed_frequencies(df: pd.DataFrame, period_freq: str) -> dict[int, list[int]]:
    """Per-number count within each time bucket, as equal-length vectors.

    ``period_freq`` is a pandas offset alias ("Q" quarterly, "Y" yearly). Every
    number 1..40 maps to a list with one count per bucket (chronological order),
    so the vectors are equal length for CV computation.
    """
    periods = df["date"].dt.to_period(period_freq)
    ordered_buckets = sorted(periods.unique())
    bucket_index = {p: i for i, p in enumerate(ordered_buckets)}
    n_buckets = len(ordered_buckets)

    result = {n: [0] * n_buckets for n in range(MAIN_MIN, MAIN_MAX + 1)}
    for period, nums in zip(periods, df["numbers"]):
        i = bucket_index[period]
        for n in nums:
            result[int(n)][i] += 1
    return result


def calculate_quarterly_frequencies(df: pd.DataFrame) -> dict[int, list[int]]:
    return _bucketed_frequencies(_as_dataframe(df), "Q")


def calculate_yearly_frequencies(df: pd.DataFrame) -> dict[int, list[int]]:
    return _bucketed_frequencies(_as_dataframe(df), "Y")


# ---------------------------------------------------------------------------
# B3 — Scalar stats: CV and z-score (with zero-denominator guards)
# ---------------------------------------------------------------------------
def calculate_cv(values) -> float:
    """Coefficient of variation (population std / mean). Returns 0.0 if mean==0."""
    if len(values) == 0:
        return 0.0
    arr = np.asarray(values, dtype=float)
    mean = arr.mean()
    if mean == 0:
        return 0.0
    return float(arr.std() / mean)


def calculate_z_score(current_freq: float, mean_freq: float, std_freq: float) -> float:
    """Standard score. Returns 0.0 if std_freq==0 (guard not in new-algo.md)."""
    if std_freq == 0:
        return 0.0
    return float((current_freq - mean_freq) / std_freq)


# ---------------------------------------------------------------------------
# B4 — Chi-square uniformity test
# ---------------------------------------------------------------------------
def _observed_list(frequencies) -> list[float]:
    if isinstance(frequencies, dict):
        return [float(frequencies[k]) for k in sorted(frequencies)]
    return [float(v) for v in frequencies]


def uniformity_pvalue(frequencies, expected) -> float:
    """Chi-square goodness-of-fit p-value against a uniform expectation."""
    observed = _observed_list(frequencies)
    exp = [float(expected)] * len(observed)
    _, p_value = stats.chisquare(observed, f_exp=exp)
    return float(p_value)


def test_uniformity(frequencies, expected) -> bool:
    """True if the distribution is consistent with uniform (p > 0.05).

    Note: named ``test_uniformity`` to mirror new-algo.md; it is a helper, not a
    pytest test (pytest only collects ``test_*`` inside test modules).
    """
    return uniformity_pvalue(frequencies, expected) > 0.05
