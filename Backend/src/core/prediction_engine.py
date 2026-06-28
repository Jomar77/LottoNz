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

LEFT_RANGE = (1, 20)
RIGHT_RANGE = (21, 40)


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


# ---------------------------------------------------------------------------
# B5 — Left/right lean classification
# ---------------------------------------------------------------------------
def classify_lean(numbers) -> str:
    """Classify a set of numbers as left- or right-leaning.

    Left iff strictly more numbers fall in 1..20 than in 21..40; ties -> "right"
    (mirrors new-algo.md's ``left if left_count > right_count``).
    """
    nums = list(numbers)
    left_count = sum(1 for n in nums if n <= LEFT_RANGE[1])
    right_count = len(nums) - left_count
    return "left" if left_count > right_count else "right"


# ---------------------------------------------------------------------------
# Recency helper (shared by several strategies)
# ---------------------------------------------------------------------------
def get_recent_numbers(df: pd.DataFrame, last_n_draws: int) -> set[int]:
    """Set of all main numbers appearing in the most recent ``last_n_draws``."""
    recent = df.tail(last_n_draws)
    return {int(n) for nums in recent["numbers"] for n in nums}


def _pad_to_n(selected: list[int], n: int, by_cv: list[int] | None = None) -> list[int]:
    """Pad ``selected`` to exactly ``n`` unique numbers by adding from fallback ordering.

    Fallback priority: ``by_cv`` (descending-CV order) then sequential 1..40.
    Contract: always returns ``n`` unique sorted ints in 1..40.
    """
    pool = by_cv or []
    remaining = [x for x in pool if x not in selected] + [
        x for x in range(MAIN_MIN, MAIN_MAX + 1) if x not in selected and x not in pool
    ]
    result = list(selected)
    for x in remaining:
        if len(result) >= n:
            break
        if x not in result:
            result.append(x)
    return sorted(result[:n])


# ---------------------------------------------------------------------------
# B6 — Strategy 1: Burst Volatility set
# ---------------------------------------------------------------------------
def generate_burst_set(df: pd.DataFrame, top_n: int = 6, recent_window: int = 30) -> list[int]:
    """High-CV (bursty) numbers that also appear in the recent window.

    Rank numbers by quarterly-frequency CV, take top ``top_n * 2`` candidates,
    filter to those drawn in the last ``recent_window`` draws. Always returns
    exactly ``top_n`` numbers (padded from the CV-ranked pool if needed).
    """
    quarterly = calculate_quarterly_frequencies(df)
    cv_scores = {num: calculate_cv(freqs) for num, freqs in quarterly.items()}
    by_cv_desc = [num for num, _ in sorted(cv_scores.items(), key=lambda kv: kv[1], reverse=True)]
    candidates = by_cv_desc[: top_n * 2]
    recent = get_recent_numbers(df, recent_window)
    result = [num for num in candidates if num in recent][:top_n]
    if len(result) < top_n:
        return _pad_to_n(result, top_n, by_cv=by_cv_desc)
    return sorted(result)


# ---------------------------------------------------------------------------
# B7 — Strategy 2: Regression (Sleeping Giants) set
# ---------------------------------------------------------------------------
def generate_regression_set(df: pd.DataFrame, z_threshold: float = -2.0) -> list[int]:
    """Coldest numbers (most below mean frequency), coldest-first.

    Numbers with z < ``z_threshold`` are returned coldest-first. If fewer than 6
    clear the threshold, fall back to the 6 lowest-z numbers (documented fallback
    so the set is never short).
    """
    freqs = calculate_frequencies(df)
    values = list(freqs.values())
    mean_freq = float(np.mean(values))
    std_freq = float(np.std(values))

    z_by_num = {num: calculate_z_score(freq, mean_freq, std_freq) for num, freq in freqs.items()}
    by_z_asc = sorted(z_by_num, key=lambda n: z_by_num[n])  # coldest first

    cold = [n for n in by_z_asc if z_by_num[n] < z_threshold]
    if len(cold) >= 6:
        return cold[:6]
    return by_z_asc[:6]


# ---------------------------------------------------------------------------
# B8 — Strategy 3: Momentum Carry-Over set
# ---------------------------------------------------------------------------
def generate_momentum_set(df: pd.DataFrame, window: int = 30, min_freq: int = 8) -> list[int]:
    """Hot numbers recurring within the recent ``window`` draws, freq-descending.

    Numbers appearing >= ``min_freq`` times in the window are returned highest-
    frequency-first. If fewer than 6 clear ``min_freq``, top up with the next
    most frequent numbers in the window (documented fallback).
    """
    recent = df.tail(window)
    freqs = calculate_frequencies(recent)
    by_freq_desc = sorted(freqs, key=lambda n: (-freqs[n], n))

    hot = [n for n in by_freq_desc if freqs[n] >= min_freq]
    if len(hot) >= 6:
        return hot[:6]
    return by_freq_desc[:6]


# ---------------------------------------------------------------------------
# B9 — Strategy 4: Balanced Hybrid set (seeded)
# ---------------------------------------------------------------------------
def generate_hybrid_set(df: pd.DataFrame, rng) -> list[int]:
    """A balanced mix: 2 hot + 2 cold + 2 neutral numbers, filled to 6, sorted.

    ``rng`` is an injected ``random.Random`` so the result is reproducible under a
    fixed seed (new-algo.md used bare ``random.*`` — replaced with injected RNG).
    """
    freqs = calculate_frequencies(df)
    mean_freq = float(np.mean(list(freqs.values())))

    hot = sorted(n for n, f in freqs.items() if f > mean_freq * 1.05)
    cold = sorted(n for n, f in freqs.items() if f < mean_freq * 0.95)
    neutral = sorted(n for n, f in freqs.items() if mean_freq * 0.95 <= f <= mean_freq * 1.05)

    result: list[int] = []
    result.extend(rng.sample(hot, min(2, len(hot))))
    result.extend(rng.sample(cold, min(2, len(cold))))
    result.extend(rng.sample(neutral, min(2, len(neutral))))

    while len(result) < 6:
        remaining = [n for n in range(MAIN_MIN, MAIN_MAX + 1) if n not in result]
        result.append(rng.choice(remaining))

    return sorted(result)


# ---------------------------------------------------------------------------
# B10 — Strategy 5: Left/Right Leaning set
# ---------------------------------------------------------------------------
def generate_lean_set(
    df: pd.DataFrame,
    lean_direction: str = "left",
    window_years: int = 1,
    reference_date: pd.Timestamp | None = None,
) -> list[int]:
    """Numbers from the target side (1-20 left / 21-40 right) with highest recent frequency.

    ``reference_date`` is injectable so tests are stable; defaults to the max draw date.
    Draws older than ``window_years`` before ``reference_date`` are excluded.
    Always returns exactly 6 sorted numbers from the target side.
    """
    ref = reference_date if reference_date is not None else df["date"].max()
    cutoff = ref - pd.DateOffset(years=window_years)
    recent = df[df["date"] >= cutoff]

    lo, hi = LEFT_RANGE if lean_direction == "left" else RIGHT_RANGE
    target_nums = list(range(lo, hi + 1))

    freqs = calculate_frequencies(recent)
    by_freq_desc = sorted(target_nums, key=lambda n: (-freqs[n], n))
    return sorted(by_freq_desc[:6])


# ---------------------------------------------------------------------------
# B11 — Powerball selection (hot/cold/cluster/balanced, seeded)
# ---------------------------------------------------------------------------
def _pb_frequencies(df: pd.DataFrame) -> dict[int, int]:
    """Zero-filled powerball frequency over all 10 possible values (1..10)."""
    freqs = {i: 0 for i in range(POWERBALL_MIN, POWERBALL_MAX + 1)}
    for pb in df["powerball"]:
        freqs[int(pb)] += 1
    return freqs


def get_high_cv_numbers(df: pd.DataFrame, top_n: int = 10) -> list[int]:
    """Top-``top_n`` main numbers by quarterly-frequency CV (high = 'bursty')."""
    quarterly = calculate_quarterly_frequencies(df)
    by_cv = sorted(quarterly, key=lambda n: calculate_cv(quarterly[n]), reverse=True)
    return by_cv[:top_n]


def calculate_pb_cooccurrence(df: pd.DataFrame, high_cv_nums: list[int]) -> dict[int, int]:
    """Count how often each PB co-occurs with any of ``high_cv_nums``."""
    counts = {i: 0 for i in range(POWERBALL_MIN, POWERBALL_MAX + 1)}
    for _, row in df.iterrows():
        if any(n in high_cv_nums for n in row["numbers"]):
            counts[int(row["powerball"])] += 1
    return counts


def select_powerball(
    df: pd.DataFrame,
    strategy: str = "balanced",
    rng=None,
    window: int = 30,
) -> int:
    """Select a powerball (1-10) using the given strategy.

    ``strategy`` is one of:
    - ``"hot"``: most frequent in recent ``window`` draws (not overall, per contract).
    - ``"cold"``: least frequent overall (zero-filled so never-appeared PBs are eligible).
    - ``"cluster"``: PB most co-occurring with high-CV main numbers.
    - ``"balanced"``: weighted-random by overall frequency; requires injected ``rng``
      (``random.Random``) for reproducibility.
    """
    if strategy == "hot":
        recent = df.tail(window)
        freqs = _pb_frequencies(recent)
        return max(freqs, key=lambda pb: (freqs[pb], -pb))

    if strategy == "cold":
        freqs = _pb_frequencies(df)
        return min(freqs, key=lambda pb: (freqs[pb], pb))

    if strategy == "cluster":
        high_cv = get_high_cv_numbers(df)
        cooc = calculate_pb_cooccurrence(df, high_cv)
        return max(cooc, key=lambda pb: (cooc[pb], -pb))

    # "balanced": weighted random by overall frequency
    freqs = _pb_frequencies(df)
    population = list(freqs.keys())
    weights = [freqs[pb] + 1 for pb in population]  # +1 so zero-count PBs still eligible
    total = sum(weights)
    cumulative = []
    running = 0.0
    for w in weights:
        running += w / total
        cumulative.append(running)
    r = (rng or __import__("random")).random()
    for pb, threshold in zip(population, cumulative):
        if r <= threshold:
            return pb
    return population[-1]


# ---------------------------------------------------------------------------
# B12 — Duplicate avoidance
# ---------------------------------------------------------------------------
def avoid_duplicates(
    candidate_nums: list[int],
    recent_numbers: set[int],
    max_overlap: int = 2,
) -> list[int]:
    """Ensure the candidate set doesn't overlap recent draws more than ``max_overlap``.

    Both branches return exactly 6 unique sorted ints in 1..40.
    """
    overlap = set(candidate_nums) & recent_numbers
    if len(overlap) <= max_overlap:
        return sorted(candidate_nums)

    # Build replacement pool: prefer non-recent numbers not already in candidate.
    available = [
        n for n in range(MAIN_MIN, MAIN_MAX + 1)
        if n not in recent_numbers and n not in candidate_nums
    ]
    # Fall back to recent numbers not already in candidate if pool is exhausted.
    fallback = [
        n for n in range(MAIN_MIN, MAIN_MAX + 1)
        if n not in candidate_nums and n not in available
    ]

    result = list(candidate_nums)
    replacement_pool = available + fallback

    # Replace numbers that are in the overlap until within limit.
    to_replace = [n for n in result if n in recent_numbers]
    replace_count = len(to_replace) - max_overlap
    for i, num in enumerate(result):
        if replace_count <= 0:
            break
        if num in recent_numbers and replacement_pool:
            result[i] = replacement_pool.pop(0)
            replace_count -= 1

    return sorted(result)


# ---------------------------------------------------------------------------
# B13 — Full pipeline: generate_prediction_sets (5 sets, seeded, deterministic)
# ---------------------------------------------------------------------------
def generate_prediction_sets(
    df: pd.DataFrame,
    num_sets: int = 5,
    exclude_recent_draws: int = 5,
    seed=None,
) -> list[dict]:
    """Generate ``num_sets`` strategically distinct prediction sets.

    PB strategy per set (per contract):
      burst_volatility  -> cluster
      mean_reversion    -> cold
      momentum_carry    -> hot
      balanced_hybrid   -> balanced (seeded)
      lean_bias         -> balanced (seeded)

    One ``random.Random`` instance is seeded once and threaded in a fixed call
    order through all randomised steps (hybrid set, both balanced PBs) so the
    same seed always produces byte-identical output.
    """
    import random as _random

    rng = _random.Random(seed)
    recent = get_recent_numbers(df, exclude_recent_draws)

    lean_dir = classify_lean(
        [n for nums in df.tail(30)["numbers"] for n in nums]
    )

    # Fixed call order for rng consumption (must not change without bumping the API).
    burst_main = avoid_duplicates(generate_burst_set(df), recent)
    regression_main = avoid_duplicates(generate_regression_set(df), recent)
    momentum_main = avoid_duplicates(generate_momentum_set(df), recent)
    hybrid_main = avoid_duplicates(generate_hybrid_set(df, rng), recent)
    lean_main = avoid_duplicates(generate_lean_set(df, lean_direction=lean_dir), recent)

    sets = [
        {
            "main": burst_main,
            "pb": select_powerball(df, strategy="cluster"),
            "strategy": "burst_volatility",
        },
        {
            "main": regression_main,
            "pb": select_powerball(df, strategy="cold"),
            "strategy": "mean_reversion",
        },
        {
            "main": momentum_main,
            "pb": select_powerball(df, strategy="hot"),
            "strategy": "momentum_carry",
        },
        {
            "main": hybrid_main,
            "pb": select_powerball(df, strategy="balanced", rng=rng),
            "strategy": "balanced_hybrid",
        },
        {
            "main": lean_main,
            "pb": select_powerball(df, strategy="balanced", rng=rng),
            "strategy": "lean_bias",
        },
    ]

    return sets[:num_sets]
