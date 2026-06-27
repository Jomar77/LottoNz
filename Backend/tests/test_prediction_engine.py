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
