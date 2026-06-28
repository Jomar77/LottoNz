"""Tests for the prediction engine (Phase B)."""

import pandas as pd
import pytest

from src.core import prediction_engine as pe

# A tiny results.json-shaped fixture, stored MOST-RECENT-FIRST (like the real file).
SAMPLE_DRAWS = [
    {"date": "2026-05-09", "numbers": [3, 10, 12, 18, 26, 32], "powerball": 5},
    {"date": "2026-05-02", "numbers": [1, 4, 9, 22, 33, 40], "powerball": 2},
    {"date": "2026-04-25", "numbers": [5, 7, 11, 19, 28, 35], "powerball": 8},
    {"date": "2025-12-13", "numbers": [2, 8, 14, 20, 30, 39], "powerball": 1},
    {"date": "2025-01-04", "numbers": [6, 13, 17, 23, 31, 38], "powerball": 7},
]


# --- B1: data loader -------------------------------------------------------

def test_load_draws_reads_default_results_json():
    draws = pe.load_draws()
    assert isinstance(draws, list)
    assert len(draws) > 1000  # the real file has ~1874 rows
    assert {"date", "numbers", "powerball"} <= set(draws[0].keys())


def test_load_draws_reads_given_path(tmp_path):
    import json

    p = tmp_path / "results.json"
    p.write_text(json.dumps(SAMPLE_DRAWS), encoding="utf-8")
    draws = pe.load_draws(p)
    assert len(draws) == len(SAMPLE_DRAWS)


def test_to_dataframe_returns_sorted_ascending():
    df = pe.to_dataframe(SAMPLE_DRAWS)
    dates = list(df["date"])
    assert dates == sorted(dates)  # oldest -> newest
    assert df.iloc[0]["date"] == pd.Timestamp("2025-01-04")
    assert df.iloc[-1]["date"] == pd.Timestamp("2026-05-09")


def test_to_dataframe_schema():
    df = pe.to_dataframe(SAMPLE_DRAWS)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    # numbers column is list-valued
    assert isinstance(df.iloc[0]["numbers"], list)
    assert len(df.iloc[0]["numbers"]) == 6
    # powerball column is integer-typed
    assert pd.api.types.is_integer_dtype(df["powerball"])


# --- B2: frequency distributions ------------------------------------------

def test_calculate_frequencies_overall():
    # In SAMPLE_DRAWS every drawn number appears exactly once; 10 numbers never appear.
    freqs = pe.calculate_frequencies(SAMPLE_DRAWS)
    assert set(freqs.keys()) == set(range(1, 41))  # all 40 zero-filled
    drawn = {n for d in SAMPLE_DRAWS for n in d["numbers"]}
    for n in range(1, 41):
        assert freqs[n] == (1 if n in drawn else 0)


def test_calculate_frequencies_accepts_dataframe():
    df = pe.to_dataframe(SAMPLE_DRAWS)
    assert pe.calculate_frequencies(df) == pe.calculate_frequencies(SAMPLE_DRAWS)


def test_quarterly_frequencies_shape():
    df = pe.to_dataframe(SAMPLE_DRAWS)
    q = pe.calculate_quarterly_frequencies(df)
    assert set(q.keys()) == set(range(1, 41))
    # SAMPLE spans 2025Q1, 2025Q4, 2026Q2 -> 3 buckets; equal-length vectors.
    lengths = {len(v) for v in q.values()}
    assert lengths == {3}
    assert sum(q[3]) == 1  # number 3 drawn once (2026Q2)
    assert sum(q[15]) == 0  # number 15 never drawn


def test_yearly_frequencies_shape():
    df = pe.to_dataframe(SAMPLE_DRAWS)
    y = pe.calculate_yearly_frequencies(df)
    assert set(y.keys()) == set(range(1, 41))
    # SAMPLE spans 2025, 2026 -> 2 buckets.
    lengths = {len(v) for v in y.values()}
    assert lengths == {2}
    assert sum(y[6]) == 1  # number 6 drawn once (2025)


# --- B3: scalar stats (CV, z-score) ---------------------------------------

def test_calculate_cv():
    # mean=5, population std=2 -> cv=0.4
    assert pe.calculate_cv([2, 4, 4, 4, 5, 5, 7, 9]) == pytest.approx(0.4)


def test_calculate_cv_zero_mean_guard():
    assert pe.calculate_cv([0, 0, 0]) == 0.0
    assert pe.calculate_cv([]) == 0.0


def test_calculate_z_score():
    assert pe.calculate_z_score(10, 5, 2.5) == pytest.approx(2.0)
    assert pe.calculate_z_score(2, 5, 2.5) == pytest.approx(-1.2)


def test_calculate_z_score_zero_std_guard():
    assert pe.calculate_z_score(10, 5, 0) == 0.0


# --- B4: chi-square uniformity --------------------------------------------

def test_uniformity_true_for_flat():
    freqs = {n: 10 for n in range(1, 41)}
    assert pe.test_uniformity(freqs, 10) is True


def test_uniformity_false_for_skewed():
    freqs = {n: 5 for n in range(1, 41)}
    freqs[1] = 200  # one number wildly over-represented
    expected = sum(freqs.values()) / 40
    assert pe.test_uniformity(freqs, expected) is False


def test_uniformity_pvalue_in_range():
    freqs = {n: 10 for n in range(1, 41)}
    p = pe.uniformity_pvalue(freqs, 10)
    assert isinstance(p, float)
    assert 0.0 <= p <= 1.0
    assert p > 0.05  # flat distribution


# --- B5: left/right lean classification -----------------------------------

def test_classify_lean_left():
    assert pe.classify_lean([1, 2, 3, 4, 30, 40]) == "left"


def test_classify_lean_right():
    assert pe.classify_lean([1, 25, 30, 33, 38, 40]) == "right"


def test_classify_lean_tie_is_right():
    # 3 left / 3 right -> "right" per new-algo.md (left only if left_count > right_count)
    assert pe.classify_lean([1, 2, 3, 30, 33, 40]) == "right"


# --- B6: burst volatility set ---------------------------------------------

def _build_burst_fixture():
    """Draws where 10 is high-CV AND recent, 20 is high-CV but NOT recent.

    Background numbers 1-6 appear uniformly every quarter (low CV). Burst numbers
    cluster in specific quarters. Q1 (oldest) falls outside the last-30 window, so
    20 (only in Q1) is excluded by the recency filter while 10 (also in Q4) is not.
    """
    draws = []
    bg = [1, 2, 3, 4, 5, 6]

    def add(date, nums, count):
        for _ in range(count):
            draws.append({"date": date, "numbers": list(nums), "powerball": 1})

    # Q1 (oldest): 12 background + 3 bursts containing 10 and 20
    add("2025-01-15", bg, 12)
    add("2025-02-15", [7, 8, 9, 10, 11, 20], 3)
    # Q2, Q3: background only
    add("2025-04-15", bg, 12)
    add("2025-07-15", bg, 12)
    # Q4 (newest): 12 background + 3 bursts containing 10 (and 12) but NOT 20
    add("2025-10-15", bg, 12)
    add("2025-11-15", [7, 8, 9, 10, 11, 12], 3)
    return draws


def test_get_recent_numbers():
    df = pe.to_dataframe(_build_burst_fixture())
    recent = pe.get_recent_numbers(df, 30)
    assert isinstance(recent, set)
    assert 10 in recent  # appears in Q4
    assert 20 not in recent  # only in Q1 (oldest, outside last 30 draws)


def test_burst_set_size_and_range():
    df = pe.to_dataframe(_build_burst_fixture())
    result = pe.generate_burst_set(df)
    assert len(result) == 6  # contract: always exactly 6
    assert len(set(result)) == 6
    assert all(1 <= n <= 40 for n in result)
    assert result == sorted(result)  # must be sorted ascending


def test_burst_prefers_high_cv_recent():
    df = pe.to_dataframe(_build_burst_fixture())
    result = pe.generate_burst_set(df)
    assert 10 in result  # high CV and recent
    assert 20 not in result  # high CV but not recent


# --- B7: regression (sleeping giants) set ----------------------------------

def _build_regression_fixture():
    """Most numbers drawn often; 38/39/40 progressively colder (40 coldest)."""
    draws = []

    def add(nums):
        draws.append({"date": "2025-01-01", "numbers": list(nums), "powerball": 1})

    # 1..37 each appear ~10 times via rotating 6-number draws.
    hot = list(range(1, 38))
    for _ in range(10):
        for i in range(0, len(hot) - 5, 6):
            add(hot[i : i + 6])
    # leftover of 1..37 to even things; then cold tail:
    add([38, 38 - 1, 38 - 2, 38 - 3, 38 - 4, 38 - 5])  # one extra draw with 38 (cold but not coldest)
    add([39 - 1, 39 - 2, 39 - 3, 39 - 4, 39 - 5, 38])  # 38 appears twice total, 39 zero so far
    add([1, 2, 3, 4, 5, 39])  # 39 appears once
    return draws


def test_regression_returns_coldest():
    df = pe.to_dataframe(_build_regression_fixture())
    result = pe.generate_regression_set(df)
    freqs = pe.calculate_frequencies(df)
    # coldest-first: frequencies non-decreasing along the returned set
    result_freqs = [freqs[n] for n in result]
    assert result_freqs == sorted(result_freqs)
    assert result[0] == 40  # 40 is never drawn -> coldest
    assert len(result) == 6


def test_regression_threshold_relaxes_when_empty():
    # Perfectly flat distribution -> no z < -2.0 -> fallback to 6 lowest-z.
    draws = [
        {"date": "2025-01-01", "numbers": list(g), "powerball": 1}
        for g in ([1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12])
    ]
    df = pe.to_dataframe(draws)
    result = pe.generate_regression_set(df)
    assert len(result) == 6
    assert len(set(result)) == 6


# --- B8: momentum carry-over set ------------------------------------------

def _build_momentum_fixture():
    """Old draws use 35-40 (outside last-30 window); recent draws use 1-7."""
    draws = []

    def add(date, nums, count):
        for _ in range(count):
            draws.append({"date": date, "numbers": list(nums), "powerball": 1})

    add("2024-01-01", [35, 36, 37, 38, 39, 40], 30)  # oldest -> outside window
    add("2025-01-01", [1, 2, 3, 4, 5, 6], 15)
    add("2025-06-01", [1, 2, 3, 4, 5, 7], 15)  # newest
    return draws


def test_momentum_returns_hot_in_window():
    df = pe.to_dataframe(_build_momentum_fixture())
    result = pe.generate_momentum_set(df, window=30, min_freq=8)
    assert len(result) == 6
    assert 1 in result  # appears 30x in window
    recent_freqs = pe.calculate_frequencies(df.tail(30))
    ordered = [recent_freqs[n] for n in result]
    assert ordered == sorted(ordered, reverse=True)  # freq-descending


def test_momentum_window_only():
    df = pe.to_dataframe(_build_momentum_fixture())
    result = pe.generate_momentum_set(df, window=30, min_freq=8)
    assert 40 not in result  # hot only outside the window


# --- B9: balanced hybrid set (seeded) -------------------------------------

def test_hybrid_is_seeded_reproducible():
    import random

    df = pe.to_dataframe(_build_regression_fixture())
    a = pe.generate_hybrid_set(df, random.Random(42))
    b = pe.generate_hybrid_set(df, random.Random(42))
    assert a == b
    # different seed should (very likely) differ in at least the random fills
    c = pe.generate_hybrid_set(df, random.Random(7))
    assert isinstance(c, list)


def test_hybrid_composition():
    import random

    df = pe.to_dataframe(_build_regression_fixture())
    result = pe.generate_hybrid_set(df, random.Random(1))
    assert len(result) == 6
    assert len(set(result)) == 6
    assert result == sorted(result)
    assert all(1 <= n <= 40 for n in result)


# --- B10: left/right leaning set ------------------------------------------

def _build_lean_fixture():
    """Draws spanning 2023-2025. Left numbers 1-20 heavily used; right 21-40 rarely."""
    draws = []

    def add(date, nums):
        draws.append({"date": date, "numbers": list(nums), "powerball": 1})

    # 2023 draws (>1 year old from ref date 2025-06-01 -> excluded)
    for _ in range(10):
        add("2023-01-15", [21, 25, 30, 33, 37, 40])  # right-heavy, old

    # Recent draws (within 1 year)
    for _ in range(10):
        add("2025-01-15", [1, 2, 3, 4, 5, 6])   # left numbers, frequent
    for _ in range(5):
        add("2025-03-15", [1, 3, 7, 11, 15, 19])  # still left
    add("2025-05-01", [22, 25, 28, 32, 36, 39])  # right numbers, recent but fewer
    return draws


def test_lean_set_left_side():
    df = pe.to_dataframe(_build_lean_fixture())
    ref = pd.Timestamp("2025-06-01")
    result = pe.generate_lean_set(df, lean_direction="left", window_years=1, reference_date=ref)
    assert len(result) == 6
    assert all(1 <= n <= 20 for n in result)  # all in left range
    assert result == sorted(result)


def test_lean_set_right_side():
    df = pe.to_dataframe(_build_lean_fixture())
    ref = pd.Timestamp("2025-06-01")
    result = pe.generate_lean_set(df, lean_direction="right", window_years=1, reference_date=ref)
    assert len(result) == 6
    assert all(21 <= n <= 40 for n in result)  # all in right range


def test_lean_window_filter():
    df = pe.to_dataframe(_build_lean_fixture())
    ref = pd.Timestamp("2025-06-01")
    # The 2023 right-heavy draws are outside the 1-year window; only recent left draws remain.
    result = pe.generate_lean_set(df, lean_direction="left", window_years=1, reference_date=ref)
    # 1 appears ~15x in recent draws -> must be in the result
    assert 1 in result


# --- B11: powerball selection ---------------------------------------------

def _build_pb_fixture():
    """30 draws: PB 3 dominates recent 10; PB 9 is coldest overall; PB 1 co-occurs with CV-high mains."""
    draws = []

    def add(date, nums, pb):
        draws.append({"date": date, "numbers": list(nums), "powerball": pb})

    # Older draws (outside recent-10 window): various PBs but PB 3 absent
    for i in range(20):
        add("2024-01-01", [1 + i % 6, 7, 8, 9, 10, 11], pb=(i % 8) + 1)  # PBs 1-8

    # Recent 10 draws: PB 3 appears 8 times (hot)
    for i in range(8):
        add("2025-01-01", [1, 2, 3, 4, 5, 6], pb=3)
    add("2025-01-02", [1, 2, 3, 4, 5, 6], pb=7)
    add("2025-01-03", [1, 2, 3, 4, 5, 6], pb=5)
    return draws


def test_pb_hot():
    df = pe.to_dataframe(_build_pb_fixture())
    pb = pe.select_powerball(df, strategy="hot", window=10)
    assert pb == 3  # most frequent in recent 10
    assert 1 <= pb <= 10


def test_pb_cold():
    df = pe.to_dataframe(_build_pb_fixture())
    pb = pe.select_powerball(df, strategy="cold")
    assert 1 <= pb <= 10
    # PB 9 and 10 never appear in this fixture -> should be one of them
    freqs = {i: 0 for i in range(1, 11)}
    for d in _build_pb_fixture():
        freqs[d["powerball"]] += 1
    assert freqs[pb] == min(freqs.values())


def test_pb_cluster():
    df = pe.to_dataframe(_build_pb_fixture())
    pb = pe.select_powerball(df, strategy="cluster")
    assert 1 <= pb <= 10


def test_pb_balanced_seeded():
    import random

    df = pe.to_dataframe(_build_pb_fixture())
    a = pe.select_powerball(df, strategy="balanced", rng=random.Random(42))
    b = pe.select_powerball(df, strategy="balanced", rng=random.Random(42))
    assert a == b
    assert 1 <= a <= 10


# --- B12: duplicate avoidance ---------------------------------------------

def test_avoid_duplicates_passthrough():
    recent = {1, 2, 3}
    candidate = [4, 5, 6, 10, 20, 30]
    result = pe.avoid_duplicates(candidate, recent, max_overlap=2)
    assert result == sorted(candidate)  # no excess overlap -> returned sorted


def test_avoid_duplicates_replaces():
    recent = {1, 2, 3, 4, 5, 6}
    candidate = [1, 2, 3, 4, 5, 7]  # 5 overlap (> max_overlap=2) -> replace 3
    result = pe.avoid_duplicates(candidate, recent, max_overlap=2)
    overlap = len(set(result) & recent)
    assert overlap <= 2
    assert len(result) == 6
    assert len(set(result)) == 6
    assert result == sorted(result)


def test_avoid_duplicates_preserves_count():
    # Extreme: all of 1..39 are "recent" — only 40 is non-recent.
    recent = set(range(1, 40))
    candidate = [1, 2, 3, 4, 5, 6]  # 6 overlap
    result = pe.avoid_duplicates(candidate, recent, max_overlap=2)
    assert len(result) == 6
    assert len(set(result)) == 6
    assert all(1 <= n <= 40 for n in result)
    assert result == sorted(result)
