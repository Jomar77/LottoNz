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
